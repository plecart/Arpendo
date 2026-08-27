"""Sonde de santé de l'api : une table de dépendances, leur état, un verdict."""

import asyncio
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

router = APIRouter()

Probe = Callable[[Request], Awaitable[None]]
"""Un aller-retour vers une dépendance, à partir de la requête qui la traverse.

Elle ne rend rien : seul compte qu'elle aboutisse. Elle va chercher sa ressource dans
``app.state``, où le cycle de vie l'a rangée — c'est ce qui permet à la route d'ignorer jusqu'au
nombre des dépendances.
"""

PROBE_TIMEOUT = 1.0
"""Secondes accordées à chaque dépendance.

Une sonde de santé qui pend est pire qu'une sonde qui échoue : le reverse proxy et le moniteur
d'uptime attendraient, et un ``docker compose up`` resterait bloqué sur un ``healthcheck`` sans
réponse. Une seconde est très au-dessus de ce que coûtent un ``SELECT 1`` et un ``PING`` sur le
réseau local ; la dépasser signifie que quelque chose ne va pas, pas que la machine est lente.

C'est un **filet**, pas un délai de fonctionnement : chaque client sait échouer plus vite que ça
tout seul, et un test le vérifie.
"""

OK = "ok"
"""Le verdict favorable — celui d'une dépendance joignable comme celui de l'api entière."""

UNREACHABLE = "unreachable"
"""L'état d'une dépendance qui n'aboutit pas, quelle qu'en soit la raison."""

DEGRADED = "degraded"
"""Le verdict de l'api dès qu'une seule de ses dépendances manque."""


async def _probe_postgres(request: Request) -> None:
    """Ouvre une connexion et l'utilise : c'est le seul moyen de savoir qu'elle sert encore.

    Le moteur ne se connecte qu'au premier usage et son pool peut contenir des connexions
    coupées depuis. Vérifier l'objet moteur ne prouverait donc rien.
    """
    engine: AsyncEngine = request.app.state.engine
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def _probe_valkey(request: Request) -> None:
    """Un ``PING`` — le seul ordre dont la réussite prouve que le serveur répond."""
    valkey: Redis = request.app.state.valkey
    await valkey.ping()


PROBES: dict[str, Probe] = {
    "postgres": _probe_postgres,
    "valkey": _probe_valkey,
}
"""Les dépendances dont la santé de l'api dépend, sous le nom qui les désignera dans la réponse.

**Ajouter une dépendance, c'est ajouter une entrée ici.** Ni la route, ni le calcul du verdict, ni
le code de statut, ni le format de la réponse n'ont à changer — et un test le vérifie en ajoutant
une sonde de son cru.
"""


async def _state_of(probe: Probe, request: Request) -> str:
    """Rend ``ok`` si la sonde aboutit dans le délai, ``unreachable`` sinon.

    Attrape ``Exception`` volontairement : du point de vue de l'appelant, une dépendance qui
    refuse la connexion, qui répond une erreur de protocole ou qui expire sont le même fait —
    elle n'est pas exploitable. Laisser fuir l'une d'elles transformerait la sonde de santé en
    500, c'est-à-dire en panne supplémentaire au moment précis où on l'interroge pour
    diagnostiquer.
    """
    try:
        async with asyncio.timeout(PROBE_TIMEOUT):
            await probe(request)
    except Exception:
        return UNREACHABLE
    return OK


@router.get("/health")
async def health(request: Request, response: Response) -> dict[str, str]:
    """Rapporte l'état de l'api et de chacune de ses dépendances.

    Répond **200** ``{"status": "ok", …}`` si toutes répondent, **503**
    ``{"status": "degraded", …}`` dès qu'une manque, en la nommant : un moniteur d'uptime a
    besoin du verdict, la personne d'astreinte a besoin de savoir laquelle.

    Les sondes partent **en parallèle** — deux dépendances lentes coûtent le délai de la plus
    lente, pas leur somme — et chacune est bornée par ``PROBE_TIMEOUT``.

    Une seule route, pas de ``/ready`` distinct : rien ici ne redémarre un conteneur sur un état
    dégradé, donc distinguer « vivant » de « disponible » n'aurait aucun lecteur.

    La route ne nomme aucune dépendance : elle parcourt ``PROBES``. C'est la table qu'on étend,
    jamais ce code.
    """
    results = await asyncio.gather(*(_state_of(probe, request) for probe in PROBES.values()))
    states = dict(zip(PROBES, results, strict=True))

    healthy = all(state == OK for state in states.values())
    response.status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": OK if healthy else DEGRADED, **states}
