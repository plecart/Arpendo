"""Hôte HTTP de la couche de services : la fabrique d'application FastAPI."""

from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from arpendo_api.core import health
from arpendo_api.core.settings import Settings
from arpendo_api.core.valkey import create_valkey
from arpendo_api.db.engine import create_engine
from arpendo_api.db.session import create_sessionmaker


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ouvre les ressources partagées au démarrage et les libère à l'arrêt.

    Elles vivent dans ``app.state`` parce que c'est le seul endroit dont la durée de vie est
    exactement celle de l'application : un singleton de module survivrait aux tests et fuirait
    d'une application à l'autre. Un test qui construit son application obtient donc les
    ressources de *celle-ci*, jamais un état global laissé par un test précédent. C'est là que
    les sondes de ``core.health`` vont les chercher.

    Chaque ressource est empilée sur un ``AsyncExitStack`` **dès sa naissance**, et la pile se
    déroule en ordre inverse quoi qu'il arrive : si la ressource suivante échoue à naître, les
    précédentes sont libérées ; si une fermeture lève, les autres sont fermées quand même. Une
    suite de ``try``/``finally`` imbriqués donnerait la même garantie et deviendrait illisible à
    la troisième ressource.

    Ajouter une ressource, c'est donc deux lignes — la créer, l'empiler — au bon rang : l'ordre de
    création est celui des dépendances, l'ordre de libération s'en déduit. Une *fabrique*, elle,
    ne s'empile pas : la fabrique de sessions ne détient rien à fermer, c'est le moteur qu'elle
    référence qui est libéré.
    """
    settings: Settings = app.state.settings
    async with AsyncExitStack() as resources:
        app.state.engine = create_engine(settings)
        resources.push_async_callback(app.state.engine.dispose)
        app.state.sessionmaker = create_sessionmaker(app.state.engine)
        app.state.valkey = create_valkey(settings)
        resources.push_async_callback(app.state.valkey.aclose)
        yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Assemble l'application HTTP.

    Fabrique plutôt qu'instance de module : chaque appel construit une application neuve, avec
    ses propres connexions, ce qui donne aux tests un état vierge.
    Point d'entrée ASGI : ``uvicorn arpendo_api.main:create_app --factory``.

    Les routeurs des domaines métier s'ajoutent ici sous le préfixe ``/v1`` ; ``/health`` reste
    à la racine parce qu'il s'adresse aux sondes (reverse proxy, moniteur d'uptime), pas aux
    clients.

    Args:
        settings: les réglages à utiliser. Omis, ils sont lus dans l'environnement — c'est le cas
            en production, où l'application est construite par uvicorn sans argument. Un test en
            fournit un explicite pour décrire l'environnement qu'il veut éprouver.

    Returns:
        L'application, dont les connexions s'ouvriront à l'entrée dans son cycle de vie.
    """
    app = FastAPI(title="Arpendo", lifespan=_lifespan)
    app.state.settings = settings if settings is not None else Settings()
    app.include_router(health.router)
    return app
