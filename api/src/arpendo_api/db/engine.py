"""Le moteur SQLAlchemy async : comment on l'ouvre, et comment les routes y accèdent."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from arpendo_api.core.settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Ouvre le moteur de l'application, avec son pool de connexions.

    Un moteur par processus, créé au démarrage et libéré à l'arrêt : c'est le pool qui rend le
    coût d'une requête négligeable, et en créer un par requête l'annulerait. La connexion n'est
    pas établie ici — SQLAlchemy la diffère jusqu'au premier usage, ce qui laisse le processus
    démarrer même si la base tarde.

    C'est ici, et nulle part ailleurs, qu'on déballe le DSN de son ``Secret`` : il porte le mot de
    passe de la base, et ne prend sa forme lisible que pour être remis à SQLAlchemy.

    Args:
        settings: les réglages validés, dont ``database_url`` fournit le DSN
            ``postgresql+asyncpg://…``.

    Returns:
        Le moteur, à fermer par ``await moteur.dispose()``.
    """
    return create_async_engine(settings.database_url.get_secret_value())


def _from_state(request: Request) -> AsyncEngine:
    """Rend le moteur rangé dans ``app.state`` par le cycle de vie de l'application."""
    engine: AsyncEngine = request.app.state.engine
    return engine


Engine = Annotated[AsyncEngine, Depends(_from_state)]
"""Le moteur, vu par une route : ``async def route(engine: Engine)``.

Une dépendance plutôt qu'un singleton de module : un test qui construit son application obtient
le moteur de *cette* application, jamais un état global laissé par un test précédent.
"""
