"""Hôte HTTP de la couche de services : la fabrique d'application FastAPI."""

from fastapi import FastAPI

from arpendo_api.core import health


def create_app() -> FastAPI:
    """Assemble l'application HTTP.

    Fabrique plutôt qu'instance de module : chaque appel construit une application neuve, ce qui
    donne aux tests un état vierge et permettra d'injecter les réglages par environnement.
    Point d'entrée ASGI : ``uvicorn arpendo_api.main:create_app --factory``.

    Les routeurs des domaines métier s'ajoutent ici sous le préfixe ``/v1`` ; ``/health`` reste
    à la racine parce qu'il s'adresse aux sondes (reverse proxy, moniteur d'uptime), pas aux
    clients.
    """
    app = FastAPI(title="Arpendo")
    app.include_router(health.router)
    return app
