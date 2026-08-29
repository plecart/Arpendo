"""Le bus d'événements : ce qui journalise, et ce qui diffuse.

Deux fonctions et rien d'autre — ``publish`` d'un côté, ``subscribe`` de l'autre — sans aucune
dépendance au transport HTTP : la couche de services (cadrage §12.6) appelle les mêmes fonctions
depuis l'api et depuis le worker.
"""

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from arpendo_api.core.journal import EVENTS, DomainEvent, Event

_FILLED_AT_PUBLICATION = {"id", "game_id", "occurred_at"}
"""Les champs d'``Event`` que la ligne du journal porte déjà — donc pas une seconde fois dans sa
charge utile. Ce sont exactement ceux que la publication remplit en retour."""


def _registered(evenement: Event) -> bool:
    """Dit si l'objet est l'instance d'un type d'événement réellement inscrit au registre."""
    classe = type(evenement)
    return EVENTS.get(getattr(classe, "type", "")) is classe


async def publish(session: AsyncSession, valkey: Redis, *events: Event) -> None:
    """Journalise les événements, **commet**, puis les diffuse — dans cet ordre.

    Args:
        session: la session ouverte de l'appelant. ``publish`` **clôt son unité de travail** : le
            commit est ici, parce que la garantie « rien n'est diffusé qui ne soit journalisé » est
            la séquence de ces trois awaits, et non une discipline laissée à l'appelant.
        valkey: le client sur lequel diffuser.
        *events: les événements du lot, publiés dans l'ordre reçu. Variadique parce qu'un fait
            de domaine en produit parfois plusieurs — une neutralisation, c'est un commit et N
            messages.

    Raises:
        TypeError: si l'un des objets n'est pas l'instance d'une sous-classe inscrite d'``Event``.
            Vérifié **avant la première écriture** : un lot à moitié journalisé serait exactement
            l'état partiel que le commit explicite existe pour éviter.

    Note:
        ``id`` et ``occurred_at`` sont relus **sur la ligne commise**, jamais recalculés ici. Le
        premier vient du défaut Python du modèle, le second du ``now()`` de PostgreSQL, et
        SQLAlchemy le rapporte par un ``RETURNING`` posé dès l'INSERT : ``Mapper.eager_defaults``
        vaut ``"auto"``, ce qui l'active sur tout backend qui sait le faire (doc SQLAlchemy 2.0,
        « ORM — persistence techniques », *fetching server-generated defaults*). C'est ce qui rend
        la lecture possible en async : un chargement différé après le commit, lui, lèverait
        ``MissingGreenlet``.
    """
    for evenement in events:
        if not _registered(evenement):
            raise TypeError(f"type d'événement non inscrit : {type(evenement).__name__}")

    lignes = [
        DomainEvent(
            game_id=evenement.game_id,
            type=type(evenement).type,
            payload=evenement.model_dump(mode="json", exclude=_FILLED_AT_PUBLICATION),
        )
        for evenement in events
    ]
    session.add_all(lignes)
    await session.commit()

    for evenement, ligne in zip(events, lignes, strict=True):
        evenement.id = ligne.id
        evenement.occurred_at = ligne.occurred_at
