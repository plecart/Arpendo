from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app


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
    surcharges: dict[str, str] = getattr(request, "param", {})
    return Settings().model_copy(update=surcharges)


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
