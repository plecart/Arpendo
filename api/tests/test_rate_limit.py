import time
from collections.abc import AsyncIterator

import pytest
from conftest import VALKEY_SUR_UN_PORT_FERME, reglages_surcharges
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from starlette.types import ASGIApp
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from arpendo_api.core import rate_limit
from arpendo_api.core.health import PROBE_TIMEOUT
from arpendo_api.core.rate_limit import Dimension
from arpendo_api.core.settings import Settings
from arpendo_api.core.valkey import CONNECT_TIMEOUT, create_valkey
from arpendo_api.main import create_app

DEUX_REQUETES_PAR_FENETRE = {"rate_limit_ip_requests": 2}
UNE_REQUETE_PAR_SECONDE = {"rate_limit_ip_requests": 1, "rate_limit_ip_window_seconds": 1}

DERRIERE_LE_PROXY = "203.0.113.7"
"""L'adresse que le proxy annonce dans `X-Forwarded-For` — celle d'un vrai client."""

PROXY = "10.0.0.9"
"""Le pair qui se présente comme proxy. De confiance ou non selon le test."""

EN_TETE_FACTICE = "x-cle-factice"
"""L'en-tête où la dimension inventée par les tests va chercher sa clé."""

COMPTEUR_LOCAL = "ratelimit:ip:127.0.0.1"
"""Le compteur de l'adresse qu'`ASGITransport` donne à ses clients par défaut."""


async def cles_de_limitation(valkey: Redis) -> list[str]:
    """Les compteurs présents, triés — le seul état que le limiteur laisse derrière lui."""
    return sorted([cle.decode() async for cle in valkey.scan_iter(match="ratelimit:*")])


async def _purger(valkey: Redis) -> None:
    """Supprime tous les compteurs, s'il y en a — `delete()` sans argument est une erreur."""
    if cles := await cles_de_limitation(valkey):
        await valkey.delete(*cles)


@pytest.fixture(autouse=True)
async def valkey() -> AsyncIterator[Redis]:
    """Un Valkey vidé de ses compteurs avant et après CHAQUE test du module.

    `ASGITransport` donne `127.0.0.1` à tous ses clients par défaut : sans cette purge, toute la
    suite incrémenterait un même `ratelimit:ip:127.0.0.1` d'une durée de vie d'une minute, et un
    test à petit quota échouerait selon ce qui a tourné avant lui.

    Le client est construit sur l'environnement réel et non sur la fixture `settings` : un test
    qui décrit un Valkey injoignable doit quand même voir ses clés purgées.
    """
    async with create_valkey(reglages_surcharges({})) as valkey:
        await _purger(valkey)
        yield valkey
        await _purger(valkey)


def _client_depuis(application: ASGIApp, pair: str) -> AsyncClient:
    """Un client HTTP qui se présente à l'application sous l'adresse `pair`.

    C'est `ASGITransport` qui pose `scope["client"]`, exactement là où un vrai serveur le
    poserait : le limiteur ne peut pas distinguer ce montage d'une connexion réseau.
    """
    return AsyncClient(
        transport=ASGITransport(app=application, client=(pair, 0)),
        base_url="http://test",
    )


@pytest.mark.parametrize("settings", [DEUX_REQUETES_PAR_FENETRE], indirect=True)
async def test_au_dela_du_quota_l_api_refuse_avec_429_et_retry_after(client: AsyncClient) -> None:
    """Le quota s'épuise sur des requêtes réelles, et la suivante est refusée.

    `/health` sert d'endpoint : aucune route n'est exemptée, et c'est la seule qui existe.
    """
    for _ in range(2):
        assert (await client.get("/health")).status_code == 200

    refus = await client.get("/health")

    assert refus.status_code == 429
    assert int(refus.headers["Retry-After"]) >= 1
    assert "detail" in refus.json()


@pytest.mark.parametrize("settings", [UNE_REQUETE_PAR_SECONDE], indirect=True)
async def test_la_fenetre_expire_et_le_quota_repart(client: AsyncClient) -> None:
    """Une fenêtre fixe se referme d'elle-même : c'est l'expiration de la clé qui la ferme.

    Le test attend réellement — mesurer une expiration sans laisser le temps passer reviendrait à
    faire confiance à l'`EXPIRE` qu'on cherche justement à prouver.
    """
    assert (await client.get("/health")).status_code == 200
    assert (await client.get("/health")).status_code == 429

    time.sleep(1.1)

    assert (await client.get("/health")).status_code == 200


async def test_la_fenetre_ne_se_decale_pas_a_chaque_requete(
    client: AsyncClient, valkey: Redis
) -> None:
    """Seule la première requête de la fenêtre en pose l'échéance — c'est le rôle du `NX`.

    Sans lui, chaque requête repousserait l'expiration : un client qui frappe sans relâche ne
    verrait jamais sa fenêtre se refermer, et resterait bloqué indéfiniment. Le défaut est
    invisible pour un test qui laisse passer le temps, puisque l'expiration finit par arriver
    dans les deux cas ; il ne se voit qu'en regardant l'échéance elle-même ne pas bouger.
    """
    await client.get("/health")
    echeance = await valkey.pttl(COMPTEUR_LOCAL)

    assert echeance > 0, "un compteur sans échéance ne se réinitialiserait jamais"

    time.sleep(0.05)
    await client.get("/health")

    assert await valkey.pttl(COMPTEUR_LOCAL) < echeance


@pytest.mark.parametrize("settings", [UNE_REQUETE_PAR_SECONDE], indirect=True)
async def test_deux_adresses_ont_des_compteurs_distincts(app: FastAPI) -> None:
    """Le quota est par adresse : celui qu'un client épuise ne pèse pas sur son voisin."""
    async with _client_depuis(app, "198.51.100.1") as premier:
        assert (await premier.get("/health")).status_code == 200
        assert (await premier.get("/health")).status_code == 429

    async with _client_depuis(app, "198.51.100.2") as second:
        assert (await second.get("/health")).status_code == 200


@pytest.mark.parametrize(
    ("confiance", "comptee"),
    [(PROXY, DERRIERE_LE_PROXY), ("192.0.2.1", PROXY)],
    ids=["pair-de-confiance", "pair-inconnu"],
)
async def test_l_en_tete_du_proxy_n_est_lu_que_derriere_un_proxy_de_confiance(
    app: FastAPI, valkey: Redis, confiance: str, comptee: str
) -> None:
    """La frontière de confiance est celle d'uvicorn, et le limiteur en hérite sans la relire.

    Même requête, même en-tête, deux listes de confiance : l'adresse comptée bascule de celle
    qu'annonce `X-Forwarded-For` à celle du pair qui l'a envoyée. Le montage passe par le vrai
    `ProxyHeadersMiddleware`, seul endroit du projet qui décide à qui l'on croit — un double
    prouverait seulement que le double fonctionne.
    """
    derriere_le_proxy = ProxyHeadersMiddleware(app, trusted_hosts=confiance)

    async with _client_depuis(derriere_le_proxy, PROXY) as client:
        await client.get("/health", headers={"X-Forwarded-For": DERRIERE_LE_PROXY})

    assert await cles_de_limitation(valkey) == [f"ratelimit:ip:{comptee}"]


@pytest.fixture
def dimension_factice(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ajoute un axe de limitation à la table, sans toucher au middleware.

    Sa clé vient d'un en-tête plutôt que du réseau : c'est ce qui permet à un même client de se
    présenter tantôt avec une clé, tantôt sans.
    """
    monkeypatch.setitem(
        rate_limit.DIMENSIONS,
        "factice",
        Dimension(
            key=lambda requete: requete.headers.get(EN_TETE_FACTICE),
            quota=lambda _: 1,
            window=lambda _: 60,
        ),
    )


async def test_une_dimension_ajoutee_a_la_table_limite_sans_modifier_le_middleware(
    dimension_factice: None, client: AsyncClient
) -> None:
    """Ajouter un axe, c'est ajouter une entrée.

    L'axe `ip` reste loin de son quota : c'est bien la dimension inventée qui refuse.
    """
    entete = {EN_TETE_FACTICE: "abonne-42"}

    assert (await client.get("/health", headers=entete)).status_code == 200
    refus = await client.get("/health", headers=entete)

    assert refus.status_code == 429


async def test_une_cle_absente_ne_compte_sur_aucun_axe(
    dimension_factice: None, client: AsyncClient, valkey: Redis
) -> None:
    """Une dimension qui ne s'applique pas à la requête la laisse passer sans compteur.

    C'est le cas d'un axe « compte » sur une requête anonyme : rien ne doit être créé sous son
    nom, sans quoi tous les anonymes partageraient un compteur.
    """
    for _ in range(3):
        assert (await client.get("/health")).status_code == 200

    assert await cles_de_limitation(valkey) == [COMPTEUR_LOCAL]


@pytest.mark.parametrize("settings", [VALKEY_SUR_UN_PORT_FERME], indirect=True)
async def test_valkey_injoignable_laisse_passer_la_requete(client: AsyncClient) -> None:
    """Échec ouvert : la panne du compteur ne devient pas un refus (cadrage §13.8).

    La requête atteint la route, qui rend alors son propre verdict — ici le 503 de `/health`, qui
    constate la dépendance absente. C'est bien ce 503, et non un 200, qui prouve l'échec ouvert :
    il ne peut venir que de la route, donc le limiteur l'a laissée s'exécuter.

    Et la panne se constate sans faire attendre : la tentative que le limiteur ajoute est bornée
    par le délai de connexion du client, qui ne réessaie jamais. Le plafond est donc celui de
    `/health` — un délai de client pour le limiteur, le budget de la sonde pour la sonde.
    """
    debut = time.perf_counter()
    reponse = await client.get("/health")
    duree = time.perf_counter() - debut

    assert reponse.status_code == 503
    assert reponse.json()["valkey"] == "unreachable"
    assert duree < CONNECT_TIMEOUT + PROBE_TIMEOUT


class ValkeyBogue:
    """Un client dont l'échec n'est ni une coupure ni un délai — donc un défaut du code."""

    def pipeline(self, transaction: bool = True) -> object:
        raise RuntimeError("le limiteur a un bug")


async def test_une_erreur_qui_n_est_pas_une_panne_de_valkey_n_est_pas_avalee(
    app: FastAPI,
) -> None:
    """L'échec ouvert est étroit : il couvre la panne du cache, jamais un bug du limiteur.

    Attraper `Exception` rendrait la limitation silencieusement inopérante — la pire des pannes,
    celle qui ne se voit pas.
    """
    app.state.valkey = ValkeyBogue()

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        assert (await client.get("/health")).status_code == 500


async def test_aucun_compteur_ne_survit_au_test_precedent(
    client: AsyncClient, valkey: Redis
) -> None:
    """La purge `autouse` tient la promesse dont tous les tests à petit quota dépendent.

    Les deux assertions se lisent ensemble : une requête crée bien un compteur, et pourtant
    aucun n'existe à l'entrée du test — donc ce que les autres ont créé a été balayé.
    """
    assert await cles_de_limitation(valkey) == []

    await client.get("/health")

    assert await cles_de_limitation(valkey) == [COMPTEUR_LOCAL]


async def test_le_cycle_de_vie_traverse_le_limiteur_sans_etre_compte(
    settings: Settings, valkey: Redis
) -> None:
    """uvicorn fait traverser le cycle de vie à toute la pile, exactement comme une requête.

    La fixture `app` ne le montre pas : elle entre dans `router.lifespan_context`, donc en aval
    des middlewares. C'est ici qu'on parle à l'application entière, comme le serveur le fait —
    et sans la sortie anticipée du limiteur, `Request(scope)` refuserait un scope qui n'est pas
    une requête HTTP, et l'api ne démarrerait jamais.
    """
    application = create_app(settings)
    entrees = iter([{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}])
    reponses: list[str] = []

    async def receive() -> dict[str, str]:
        return next(entrees)

    async def send(message: dict[str, str]) -> None:
        reponses.append(message["type"])

    await application({"type": "lifespan"}, receive, send)

    assert reponses == ["lifespan.startup.complete", "lifespan.shutdown.complete"]
    assert await cles_de_limitation(valkey) == []
