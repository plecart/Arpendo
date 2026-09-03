import os
import uuid
from collections.abc import AsyncIterator, Mapping
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from evenements import PREFIXE
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.schema import CreateIndex, CreateTable

from arpendo_api.core import resources
from arpendo_api.core.journal import DomainEvent
from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app

PAIR_DE_TEST = (f"192.0.2.{100 + os.getpid() % 100}", 0)
"""L'adresse sous laquelle les clients de test se présentent à l'application.

**Surtout pas `127.0.0.1`**, le défaut d'`ASGITransport` : cette adresse a un vrai locataire dans
l'environnement de développement. Le healthcheck du conteneur `api` interroge `/health` toutes les
dix secondes depuis l'intérieur du conteneur, donc sous `ratelimit:ip:127.0.0.1`, dans le Valkey
que la suite utilise. Mesuré : `test_la_fenetre_expire_et_le_quota_repart`, qui tient une fenêtre
d'une seconde à un jeton, échouait deux fois sur quatre avec le conteneur levé, zéro fois sur six
sans lui. Invisible en CI, où aucun conteneur `api` n'existe.

Le dernier octet vient du **pid** : deux suites lancées en parallèle — deux worktrees d'une même
vague sur le même Valkey — ne partagent alors ni leur compteur ni leur purge. Une adresse fixe
échangerait une collision contre une autre.

`192.0.2.0/24` est **TEST-NET-1** (RFC 5737), réservée à la documentation : aucune machine réelle
ne la porte. L'octet est borné à 100–199 pour rester hors des adresses basses que
`test_rate_limit.py` emploie déjà dans ses propres scénarios (`192.0.2.1`, `198.51.100.1`).
"""

VALKEY_SUR_UN_PORT_FERME = {"valkey_url": "redis://127.0.0.1:1/0"}
"""Un Valkey absent, décrit une seule fois pour les modules qui éprouvent une panne de cache.

Surcharge de `settings` par paramétrisation indirecte. Sur un runner Linux, le port fermé est
refusé aussitôt ; sur un poste dont le pare-feu filtre la boucle locale, la connexion expire au
bout du délai du client. Les deux mènent au même verdict, jamais à la même durée.
"""


def ddl(element: CreateTable | CreateIndex) -> str:
    """Le SQL qu'un élément de schéma produirait sur PostgreSQL — sans base ni connexion.

    Les conventions de `db.base` s'observent dans le DDL compilé : c'est là, et nulle part dans
    l'objet Python, qu'un `Mapped[int]` devient un `BIGINT`.
    """
    return str(element.compile(dialect=postgresql.dialect()))


def reglages_surcharges(surcharges: Mapping[str, str]) -> Settings:
    """Les réglages de l'environnement, amendés — et **revalidés**.

    `model_copy(update=…)` poserait les valeurs telles quelles, sans repasser par les validateurs :
    un test pourrait alors décrire une configuration que `Settings` refuse en production, et
    prouver quelque chose d'une application qui ne démarrerait jamais. On reconstruit donc plutôt
    qu'on ne modifie.

    Args:
        surcharges: les champs à remplacer, par nom d'attribut. Vide, on rend l'environnement tel
            qu'il est.

    Returns:
        Des réglages valides, secrets compris — `model_dump()` rend les `SecretStr` intacts, et
        la revalidation les réaccepte sans les aplatir en `'**********'`.

    Raises:
        pydantic.ValidationError: si la surcharge décrit un environnement invalide.
    """
    return Settings.model_validate({**Settings().model_dump(), **surcharges})


@pytest.fixture
def settings(request: pytest.FixtureRequest) -> Settings:
    """Les réglages de l'environnement de test — donc de vrais services.

    En local, ce sont ceux du `.env` que le justfile charge, et les services que `just up`
    démarre ; en CI, ceux du job et les conteneurs `services:` du workflow. Aucun double : une
    connexion simulée ne prouverait rien de ce que cette configuration existe pour garantir.

    Un test qui a besoin d'un environnement dégradé le décrit par une paramétrisation indirecte,
    et hérite alors de toute la chaîne (`app`, `client`) sans la reconstruire ::

        @pytest.mark.parametrize("settings", [{"valkey_url": "redis://127.0.0.1:1/0"}],
                                 indirect=True)
    """
    return reglages_surcharges(getattr(request, "param", {}))


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    """Une application dont le cycle de vie a réellement tourné.

    `ASGITransport` ne déclenche pas le `lifespan` : sans ce contexte, ni le moteur ni le client
    Valkey n'existeraient, et les tests parleraient à une application à moitié démarrée.
    """
    application = create_app(settings)
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Client HTTP branché directement sur l'application, sans réseau ni serveur.

    Il se présente sous [PAIR_DE_TEST] plutôt que sous le `127.0.0.1` par défaut d'`ASGITransport`
    — voir cette constante pour le pourquoi. C'est `ASGITransport` qui pose `scope["client"]`,
    exactement là où un vrai serveur le poserait : aucun code de production ne voit la différence.
    """
    transport = ASGITransport(app=app, client=PAIR_DE_TEST)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    """La configuration d'Alembic — `[tool.alembic]` du `pyproject.toml`, sans `alembic.ini`.

    Chemin absolu : la suite peut être lancée d'ailleurs que depuis `api/`.
    """
    return Config(toml_file=str(Path(__file__).resolve().parent.parent / "pyproject.toml"))


@pytest.fixture(scope="session", autouse=True)
def schema(alembic_config: Config) -> None:
    """Monte le schéma à `head` avant la suite : après `just up`, `just test` se suffit.

    Synchrone, et c'est nécessaire : `env.py` appelle `asyncio.run()`, qui refuse de démarrer
    dans une boucle déjà en cours — celle qu'un test asynchrone aurait ouverte.
    """
    command.upgrade(alembic_config, "head")


@pytest.fixture
def partie() -> uuid.UUID:
    """Une partie propre à chaque test — aucun test ne voit ce qu'un autre a écrit.

    Sans elle, l'isolation reposerait sur l'ordre d'exécution et sur le nettoyage d'un voisin. Elle
    isole aussi les canaux du bus, y compris entre deux suites qui parlent au même Valkey : le
    pub/sub ignore l'index de base de données, un nom de canal fixe serait partagé.
    """
    return uuid.uuid4()


def fabrique_de(app: FastAPI) -> async_sessionmaker[AsyncSession]:
    """La fabrique de sessions que le cycle de vie a rangée dans ``app.state``."""
    fabrique: async_sessionmaker[AsyncSession] = app.state.sessionmaker
    return fabrique


async def evenements_persistes(app: FastAPI, partie: uuid.UUID) -> list[DomainEvent]:
    """Ce que voit une session *neuve* — donc ce qui a réellement été commis."""
    async with fabrique_de(app)() as session:
        resultat = await session.execute(
            select(DomainEvent).where(DomainEvent.game_id == partie).order_by(DomainEvent.id)
        )
        return list(resultat.scalars())


@pytest.fixture
async def journal_nettoye(app: FastAPI, partie: uuid.UUID) -> AsyncIterator[None]:
    """Retire ce que le test a délibérément commis — la base est partagée par toute la suite.

    Le nettoyage porte sur le **préfixe de type**, et non sur la partie : un événement publié sans
    partie est journalisé lui aussi, et aucune clause sur ``game_id`` ne peut l'atteindre. Mesuré —
    avec la clause par partie, une ligne orpheline survivait à la suite, et n'en disparaissait que
    par accident, quand le test des migrations défait le schéma.
    """
    yield
    async with fabrique_de(app)() as session:
        await session.execute(delete(DomainEvent).where(DomainEvent.type.startswith(PREFIXE)))
        await session.commit()


class MoteurEspion:
    """Un moteur qui n'ouvre rien et note seulement qu'on l'a libéré.

    Doublure de notre propre fabrique, et non d'une frontière du système : c'est le seul moyen
    d'observer une libération, `AsyncEngine.dispose` ne laissant aucune trace visible.
    """

    def __init__(self) -> None:
        self.libere = False

    async def dispose(self) -> None:
        self.libere = True


@pytest.fixture
def moteur_espion(monkeypatch: pytest.MonkeyPatch) -> MoteurEspion:
    """Substitue au moteur une doublure qui note sa libération.

    La substitution vise ``core.resources``, où les fabriques sont désormais appelées : c'est le
    module qui ouvre les ressources, quel que soit l'hôte qui les consomme.
    """
    moteur = MoteurEspion()
    monkeypatch.setattr(resources, "create_engine", lambda _: moteur)
    return moteur
