"""Le bus d'événements : ce qui journalise, et ce qui diffuse.

Deux fonctions et rien d'autre — ``publish`` d'un côté, ``subscribe`` de l'autre — sans aucune
dépendance au transport HTTP : la couche de services (cadrage §12.6) appelle les mêmes fonctions
depuis l'api et depuis le worker.
"""

import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from sqlalchemy.ext.asyncio import AsyncSession

from arpendo_api.core.journal import EVENTS, DomainEvent, Event

_FILLED_AT_PUBLICATION = {"id", "game_id", "occurred_at"}
"""Les champs d'``Event`` que porte la ligne du journal, et non sa charge utile.

Une seule liste pour les deux sens : ``publish`` les **exclut** de la charge utile qu'il écrit,
``_decode`` les **relit** à côté d'elle. Les séparer laisserait dériver l'encodage du décodage."""


def channel_for(game_id: uuid.UUID) -> str:
    """Le canal d'une partie — **le seul endroit** où ce nom se compose.

    Un canal par partie, et non un canal global filtré à l'arrivée : chaque abonné SSE ne recevra
    que les événements de sa partie, au lieu de trier ceux de toutes.
    """
    return f"game:{game_id}"


def _envelope(ligne: DomainEvent, game_id: uuid.UUID) -> str:
    """La ligne commise, telle qu'elle voyage : ``{id, game_id, type, payload, occurred_at}``.

    Le message est la **forme de la ligne**, pas celle de l'événement Python. C'est ce qui
    permettra à la relecture du journal (``Last-Event-ID``, §13.3) de servir exactement le même
    décodeur que le fil : une seule façon de reconstruire un événement, quelle qu'en soit la
    source.

    Args:
        ligne: la ligne commise à diffuser.
        game_id: sa partie, exigée à part parce qu'une ligne peut ne pas en avoir. Une enveloppe
            n'a alors aucun canal où aller : le cas se traite **avant** d'appeler, et le type le
            rappelle plutôt qu'un ``str(None)`` glissé dans le message.
    """
    return json.dumps(
        {
            "id": str(ligne.id),
            "game_id": str(game_id),
            "type": ligne.type,
            "payload": ligne.payload,
            "occurred_at": ligne.occurred_at.isoformat(),
        }
    )


def _decode(donnees: bytes) -> Event | None:
    """L'opération inverse d'``_envelope`` : l'événement typé d'un message, ou ``None``.

    ``None`` quand le type n'est inscrit dans **ce** processus : ce n'est pas une erreur, un
    producteur plus récent peut publier un type que celui-ci ne connaît pas encore, et un abonné
    qui lèverait là-dessus perdrait aussi les messages suivants, qu'il sait pourtant lire. Une clé
    inattendue *dans* la charge utile, elle, fait lever — c'est ``extra="forbid"`` sur ``Event``,
    et le fil reste une frontière.
    """
    message: dict[str, Any] = json.loads(donnees)
    classe = EVENTS.get(message["type"])
    if classe is None:
        return None
    return classe.model_validate(
        {**message["payload"], **{champ: message[champ] for champ in _FILLED_AT_PUBLICATION}}
    )


async def publish(session: AsyncSession, valkey: Redis, *events: Event) -> None:
    """Journalise les événements, **commet**, puis les diffuse — dans cet ordre.

    Args:
        session: la session ouverte de l'appelant. ``publish`` **clôt son unité de travail** : le
            commit est ici, parce que la garantie « rien n'est diffusé qui ne soit journalisé » est
            la séquence de ces trois awaits, et non une discipline laissée à l'appelant.
        valkey: le client sur lequel diffuser.
        *events: les événements du lot, publiés dans l'ordre reçu. Un événement **sans partie**
            est journalisé et jamais publié : il n'a pas de canal. Variadique parce qu'un fait
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
        if ligne.game_id is not None:
            await valkey.publish(channel_for(ligne.game_id), _envelope(ligne, ligne.game_id))


def _registered(evenement: Event) -> bool:
    """Dit si l'objet est l'instance d'un type d'événement réellement inscrit au registre."""
    classe = type(evenement)
    return EVENTS.get(getattr(classe, "type", "")) is classe


async def _flux(pubsub: PubSub) -> AsyncIterator[Event]:
    """Décode les messages du canal, indéfiniment, en sautant ceux d'un type inconnu.

    ``PubSub.listen()`` plutôt qu'une boucle de ``get_message`` : il bloque jusqu'au message
    suivant, ne rend que ce qui en est un, et s'arrête de lui-même quand l'abonnement est défait.
    Une boucle maison rejouerait ces trois règles, avec une branche « rien à décoder » qu'aucun
    test ne peut atteindre.
    """
    async for message in pubsub.listen():
        evenement = _decode(message["data"])
        if evenement is not None:
            yield evenement


@asynccontextmanager
async def subscribe(valkey: Redis, game_id: uuid.UUID) -> AsyncIterator[AsyncIterator[Event]]:
    """Ouvre l'abonnement aux événements d'une partie, et rend de quoi les lire.

    Gestionnaire de contexte, et pas simple fabrique d'itérateur, pour deux raisons qui tiennent
    aux deux bouts :

    - **à l'entrée**, il attend le message de confirmation du serveur. ``PubSub.subscribe()``
      n'écrit que sur la socket : publier aussitôt après perd des messages — mesuré, 8 sur 30 — et
      la perte est invisible, l'abonné voit simplement moins d'événements qu'il n'en a été publié.
      L'attente est un ``get_message`` bloquant dont **la valeur est sans intérêt** : le ``PubSub``
      est construit en ignorant les confirmations, donc il rend ``None``. Ce qui compte est qu'il
      ait lu la réponse du serveur, et un test le constate depuis le serveur (``PUBSUB NUMSUB``) ;
    - **à la sortie**, il ferme le ``PubSub``, donc rend sa connexion au pool quoi qu'il arrive.

    Aucune reconnexion : le client échoue vite et ne réessaie pas (``core.valkey``), donc la perte
    de Valkey fait lever l'itérateur au lieu de le faire attendre en silence. Le cadrage §13.8 pose
    cette perte comme indolore par conception — l'appelant se réabonne, le journal a tout gardé.

    Args:
        valkey: le client sur lequel s'abonner.
        game_id: la partie dont on veut le fil.

    Yields:
        Un itérateur asynchrone d'événements typés, valide tant que le contexte est ouvert.
    """
    async with valkey.pubsub(ignore_subscribe_messages=True) as pubsub:
        await pubsub.subscribe(channel_for(game_id))
        await pubsub.get_message(timeout=None)
        yield _flux(pubsub)
