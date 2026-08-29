"""Les ressources partagées de la couche de services, et leur cycle de vie.

Un seul endroit ouvre le moteur, la fabrique de sessions et le client Valkey — et les libère. Les
**deux points d'entrée du paquet** (cadrage §13.0) le consomment : l'hôte HTTP depuis son cycle de
vie FastAPI, le worker depuis sa boucle. Rien ici ne connaît FastAPI : c'est ce qui rend le second
hôte possible sans réécrire le premier.
"""

from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from arpendo_api.core.settings import Settings
from arpendo_api.core.valkey import create_valkey
from arpendo_api.db.engine import create_engine
from arpendo_api.db.session import create_sessionmaker


@dataclass(frozen=True, slots=True)
class Resources:
    """Ce qu'un hôte de la couche de services a besoin d'avoir sous la main.

    Gelée : un hôte consomme ces ressources, il n'en substitue pas une en cours de route. Les
    remplacer se fait à l'ouverture, là où les fabriques sont substituables.

    Attributs :
        engine: le moteur SQLAlchemy, un par processus.
        sessionmaker: la fabrique de sessions, qui ne détient rien et ne se ferme pas.
        valkey: le client Valkey, avec son pool.
    """

    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]
    valkey: Redis


@asynccontextmanager
async def open_resources(settings: Settings) -> AsyncIterator[Resources]:
    """Ouvre les ressources partagées, les rend, puis les libère en ordre inverse.

    Chaque ressource est empilée sur un ``AsyncExitStack`` **dès sa naissance**, et la pile se
    déroule quoi qu'il arrive : si la suivante échoue à naître, les précédentes sont libérées ; si
    une fermeture lève, les autres sont fermées quand même. Une suite de ``try``/``finally``
    imbriqués donnerait la même garantie et deviendrait illisible à la troisième ressource.

    Ajouter une ressource, c'est donc deux lignes — la créer, l'empiler — au bon rang : l'ordre de
    création est celui des dépendances, l'ordre de libération s'en déduit. Une *fabrique*, elle, ne
    s'empile pas : la fabrique de sessions ne détient rien à fermer, c'est le moteur qu'elle
    référence qui est libéré.

    Args:
        settings: les réglages validés, seule source des coordonnées des services.

    Yields:
        Les ressources ouvertes, valides jusqu'à la sortie du contexte.
    """
    async with AsyncExitStack() as pile:
        engine = create_engine(settings)
        pile.push_async_callback(engine.dispose)
        valkey = create_valkey(settings)
        pile.push_async_callback(valkey.aclose)
        yield Resources(engine=engine, sessionmaker=create_sessionmaker(engine), valkey=valkey)
