"""Le moteur SQLAlchemy async : comment on l'ouvre."""

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
