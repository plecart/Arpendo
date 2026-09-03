"""Hôte HTTP de la couche de services : la fabrique d'application FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from arpendo_api.core import health
from arpendo_api.core.logs import configure_logging
from arpendo_api.core.rate_limit import RateLimitMiddleware
from arpendo_api.core.resources import open_resources
from arpendo_api.core.settings import Settings, load_settings


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ouvre les ressources partagées au démarrage et les libère à l'arrêt.

    Elles vivent dans ``app.state`` parce que c'est le seul endroit dont la durée de vie est
    exactement celle de l'application : un singleton de module survivrait aux tests et fuirait
    d'une application à l'autre. Un test qui construit son application obtient donc les ressources
    de *celle-ci*, jamais un état global laissé par un test précédent. C'est là que les sondes de
    ``core.health`` et la session par requête vont les chercher.

    Leur ouverture, elle, n'appartient pas à l'hôte HTTP : ``core.resources`` la porte pour les
    deux points d'entrée du paquet. Ce cycle de vie ne fait que la consommer et ranger le résultat
    — ajouter une ressource se fait là-bas, plus ici.
    """
    settings: Settings = app.state.settings
    async with open_resources(settings) as ressources:
        app.state.engine = ressources.engine
        app.state.sessionmaker = ressources.sessionmaker
        app.state.valkey = ressources.valkey
        yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Assemble l'application HTTP.

    Fabrique plutôt qu'instance de module : chaque appel construit une application neuve, avec
    ses propres connexions, ce qui donne aux tests un état vierge.
    Point d'entrée ASGI : ``uvicorn arpendo_api.main:create_app --factory``.

    C'est aussi le seul endroit où les journaux de l'hôte HTTP peuvent être configurés : uvicorn
    pose les siens **avant** d'appeler cette fabrique, et ``configure_logging`` les reprend. Elle
    est idempotente, donc la construire plusieurs fois — ce que font les tests — n'installe qu'un
    handler.

    Les routeurs des domaines métier s'ajoutent ici sous le préfixe ``/v1`` ; ``/health`` reste
    à la racine parce qu'il s'adresse aux sondes (reverse proxy, moniteur d'uptime), pas aux
    clients.

    Args:
        settings: les réglages à utiliser. Omis, ils sont lus dans l'environnement par
            ``load_settings`` — c'est le cas en production, où l'application est construite par
            uvicorn sans argument, et où une configuration fausse doit échouer sans jamais écrire
            la valeur fautive. Un test en fournit un explicite pour décrire l'environnement qu'il
            veut éprouver.

    Returns:
        L'application, dont les connexions s'ouvriront à l'entrée dans son cycle de vie.

    Raises:
        ConfigurationError: si les réglages sont omis et que l'environnement en décrit une
            configuration invalide.
    """
    app = FastAPI(title="Arpendo", lifespan=_lifespan)
    app.state.settings = settings if settings is not None else load_settings()
    configure_logging()
    app.add_middleware(RateLimitMiddleware)
    app.include_router(health.router)
    return app
