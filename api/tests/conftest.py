import uuid
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from typing import ClassVar

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.schema import CreateIndex, CreateTable

from arpendo_api.core.journal import DomainEvent, Event
from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app


class Capture(Event):
    """Le type d'événement de toute la suite — #44 n'en livre aucun de métier.

    Il vit ici, et pas dans un module de test, parce que le registre d'``EVENTS`` est un
    dictionnaire de module : déclarer deux fois le même identifiant lèverait, et déclarer un type
    par module de test multiplierait des classes identiques. Son identifiant est préfixé ``test.``
    pour qu'aucune lecture ne le prenne pour un type de production.
    """

    type: ClassVar[str] = "test.captured"

    hexagones: int


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
    """Client HTTP branché directement sur l'application, sans réseau ni serveur."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    """Retire ce que le test a délibérément commis — la base est partagée par toute la suite."""
    yield
    async with fabrique_de(app)() as session:
        await session.execute(delete(DomainEvent).where(DomainEvent.game_id == partie))
        await session.commit()
