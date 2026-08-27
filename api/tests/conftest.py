from collections.abc import AsyncIterator, Mapping

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app


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
