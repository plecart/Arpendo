"""La session de base de données : une par requête, et qui ne commet jamais toute seule."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Fabrique les sessions de l'application, toutes sur le moteur qu'on lui donne.

    Un ``async_sessionmaker`` ne détient rien : c'est une fabrique configurée, pas une ressource.
    Elle naît avec l'application et n'a rien à fermer — c'est le moteur, lui, qu'on libère.

    ``expire_on_commit=False`` : par défaut, SQLAlchemy invalide tous les attributs chargés au
    moment du ``commit``, et le premier attribut relu déclenche un rechargement en base. En async,
    ce rechargement implicite ne peut pas s'attendre — il lève. Or une réponse HTTP est sérialisée
    **après** le commit : ce serait le cas nominal qui casse, pas un cas limite.

    Args:
        engine: le moteur de l'application, ouvert par le cycle de vie.

    Returns:
        La fabrique à ranger dans ``app.state``, dont la dépendance ci-dessous tire une session
        par requête.
    """
    return async_sessionmaker(engine, expire_on_commit=False)


async def _open_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Ouvre une session pour la durée d'une requête, et la referme quoi qu'il arrive.

    **Elle ne commet pas à la sortie, et c'est délibéré.** Committer ici persisterait la moitié
    d'une unité de travail quand une erreur survient à mi-chemin — le pire des deux mondes, car
    l'appelant reçoit une erreur *et* la base garde un état partiel. C'est donc l'appelant qui
    commet, au moment où il sait que son travail est complet. Ce qu'il n'a pas commis est annulé
    à la fermeture.

    La fabrique se lit dans ``app.state``, où le cycle de vie l'a rangée — comme les sondes de
    ``core.health`` y prennent le moteur et le client Valkey.

    Args:
        request: la requête en cours, par qui l'application est atteignable.

    Yields:
        La session, ouverte, sans transaction commencée — SQLAlchemy l'ouvre au premier ordre.
    """
    fabrique: async_sessionmaker[AsyncSession] = request.app.state.sessionmaker
    async with fabrique() as session:
        yield session


Session = Annotated[AsyncSession, Depends(_open_session)]
"""Le type d'un paramètre de route qui veut une session : ``async def route(session: Session)``.

L'annotation porte l'injection, donc la signature d'une route dit ce dont elle a besoin sans
répéter comment l'obtenir.
"""
