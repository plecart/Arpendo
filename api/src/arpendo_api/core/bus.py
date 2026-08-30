"""Le bus d'événements : ce qui journalise, et ce qui diffuse.

Deux opérations — ``publish`` d'un côté, ``subscribe`` de l'autre — et le nom de canal qu'elles
partagent, sans aucune dépendance au transport HTTP : la couche de services (cadrage §12.6)
appellera les mêmes fonctions depuis l'api et depuis le worker.
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

_ROW_FIELDS = {"id", "game_id", "occurred_at"}
"""Les champs d'``Event`` que porte la ligne du journal en colonnes, et non sa charge utile.

Une seule liste pour les deux sens : ``publish`` les **exclut** de la charge utile qu'il écrit,
``_decode`` les **relit** à côté d'elle. Les séparer laisserait dériver l'encodage du décodage.

Ils n'ont pas tous la même origine — ``game_id`` vient de l'appelant, ``id`` et ``occurred_at`` de
la ligne commise — mais ils partagent ce qui compte ici : la colonne les porte, la charge utile ne
doit pas les porter une seconde fois."""


def channel_for(game_id: uuid.UUID) -> str:
    """Le canal d'une partie — **le seul endroit** où ce nom se compose.

    Un canal par partie, et non un canal global filtré à l'arrivée : chaque abonné SSE ne recevra
    que les événements de sa partie, au lieu de trier ceux de toutes.
    """
    return f"game:{game_id}"


def _envelope(row: DomainEvent, game_id: uuid.UUID) -> str:
    """La ligne commise, telle qu'elle voyage : ``{id, game_id, type, payload, occurred_at}``.

    Le message est la **forme de la ligne**, pas celle de l'événement Python. C'est ce qui
    permettra à la relecture du journal (``Last-Event-ID``, §13.3) de servir exactement le même
    décodeur que le fil : une seule façon de reconstruire un événement, quelle qu'en soit la
    source.

    Args:
        row: la ligne commise à diffuser.
        game_id: sa partie, exigée à part parce qu'une ligne peut ne pas en avoir. Une enveloppe
            n'a alors aucun canal où aller : le cas se traite **avant** d'appeler, et le type le
            rappelle plutôt qu'un ``str(None)`` glissé dans le message.
    """
    return json.dumps(
        {
            "id": str(row.id),
            "game_id": str(game_id),
            "type": row.type,
            "payload": row.payload,
            "occurred_at": row.occurred_at.isoformat(),
        }
    )


def _decode(data: bytes) -> Event | None:
    """L'opération inverse d'``_envelope`` : l'événement typé d'un message, ou ``None``.

    ``None`` quand le type n'est inscrit dans **ce** processus : ce n'est pas une erreur, un
    producteur plus récent peut publier un type que celui-ci ne connaît pas encore, et un abonné
    qui lèverait là-dessus perdrait aussi les messages suivants, qu'il sait pourtant lire. Une clé
    inattendue *dans* la charge utile, elle, fait lever — c'est ``extra="forbid"`` sur ``Event``,
    et le fil reste une frontière.
    """
    message: dict[str, Any] = json.loads(data)
    classe = EVENTS.get(message["type"])
    if classe is None:
        return None
    return classe.model_validate(
        {**message["payload"], **{champ: message[champ] for champ in _ROW_FIELDS}}
    )


def _registered(event: Event) -> bool:
    """Dit si l'objet est l'instance d'un type d'événement réellement inscrit au registre.

    L'identité, et non la seule présence de l'identifiant : un modèle étranger qui déclarerait
    ``type = "tile.captured"`` sans descendre d'``Event`` publierait une charge utile qu'aucun
    abonné ne saurait décoder.
    """
    classe = type(event)
    return EVENTS.get(getattr(classe, "type", "")) is classe


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
        Si la diffusion échoue au milieu d'un lot — Valkey absent —, tout est déjà **commis** et
        l'exception remonte à l'appelant ; les événements déjà traités portent leur ``id``, les
        suivants non. Rien n'est perdu pour autant : le journal a tout, et le cadrage §13.8 pose la
        perte du bus comme indolore. L'appelant n'a donc rien de particulier à faire de cette
        exception.

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
            payload=evenement.model_dump(mode="json", exclude=_ROW_FIELDS),
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


async def _stream(pubsub: PubSub) -> AsyncIterator[Event]:
    """Décode les messages du canal, indéfiniment, en sautant ceux d'un type inconnu.

    ``PubSub.listen()`` plutôt qu'une boucle de ``get_message`` : il bloque jusqu'au message
    suivant et ne rend que ce qui en est un — une boucle maison rejouerait ces deux règles, avec une
    branche « rien à décoder » qu'aucun test ne peut atteindre.

    Sa condition d'arrêt (``while self.subscribed``) tombe dès que le ``PubSub`` se ferme, donc
    itérer **après** la sortie du contexte s'arrête proprement. Un consommateur **suspendu dans une
    lecture** au moment de la fermeture, lui, reçoit une erreur de connexion (les deux constatés en
    relecture indépendante). Sans conséquence tant que le consommateur et le contexte vivent dans la
    même tâche, ce qui est le cas ici ; à traiter quand la SSE lira ce flux depuis une tâche
    séparée.
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

    - **à l'entrée**, il attend la réponse du serveur au ``SUBSCRIBE``. ``PubSub.subscribe()``
      n'écrit que sur la socket sans la lire (sources de redis-py 8.1.0) : un message publié
      aussitôt après risque de partir avant que le serveur n'ait enregistré l'abonné, et la perte
      est invisible — celui-ci voit simplement moins d'événements qu'il n'en a été publié. Mesuré
      en relecture indépendante : sans cette attente, le serveur n'avait enregistré l'abonnement
      que 12 fois sur 30. L'attente est un ``get_message`` bloquant dont **la valeur est sans
      intérêt** — le ``PubSub`` est construit en ignorant les confirmations, donc il rend ``None``.
      Ce qui compte est qu'il ait lu la réponse, et un test le constate depuis le serveur
      (``PUBSUB NUMSUB``) ;
    - **à la sortie**, il ferme le ``PubSub``, donc rend sa connexion au pool quoi qu'il arrive.

    **Aucune reconnexion écrite ici, aucune lecture rejouée** : le client est réglé sur zéro
    réessai (``core.valkey``), donc une coupure remonte à l'appelant au lieu de le faire attendre
    en silence, et un serveur injoignable se constate dès l'entrée. Nuance vérifiée dans les
    sources de redis-py 8.1.0 : ``Retry.call_with_retry`` appelle son ``failure_callback`` — pour
    un ``PubSub``, un ``disconnect`` suivi d'un ``connect`` — *avant* de comparer le compteur au
    nombre de réessais. Il y a donc une tentative de rétablir la socket — et, si elle aboutit, un
    réabonnement aux canaux par le ``on_connect`` du client — mais l'ordre qui a échoué n'est pas
    rejoué. Le cadrage §13.8 pose cette perte comme indolore par conception : l'appelant se
    réabonne, le journal a tout gardé.

    Args:
        valkey: le client sur lequel s'abonner.
        game_id: la partie dont on veut le fil.

    Yields:
        Un itérateur asynchrone d'événements typés, valide tant que le contexte est ouvert.
    """
    async with valkey.pubsub(ignore_subscribe_messages=True) as pubsub:
        await pubsub.subscribe(channel_for(game_id))
        await pubsub.get_message(timeout=None)
        yield _stream(pubsub)
