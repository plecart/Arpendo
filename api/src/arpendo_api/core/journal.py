"""Le journal d'événements de domaine — la table ``domain_event`` (cadrage §12.6).

Tout ce qui arrive dans une partie s'y écrit, structuré : c'est la source de l'audit, du
débogage et du flux d'activité (§11).

Le module porte **la ligne et le type** : ``DomainEvent`` est ce qu'on écrit en base, ``Event`` ce
qu'on publie, et ``EVENTS`` le registre qui rend à un message reçu la classe qui l'a produit. Il
ignore tout du transport — c'est ``core.bus`` qui persiste et publie.
"""

import uuid
from datetime import datetime
from typing import Any, ClassVar

import uuid6
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Index, func
from sqlalchemy.orm import Mapped, mapped_column

from arpendo_api.db.base import Base


class DomainEvent(Base):
    """Une ligne du journal.

    Attributs :
        id: identifiant UUIDv7 (§12.4) — triable et non énumérable. Généré côté Python, à
            l'insertion. **Seul point d'appel de ``uuid6``** : Python 3.14 apporte
            ``uuid.uuid7()`` ; à la mise à jour de ``api/.python-version``, remplacer l'appel et
            retirer la dépendance. ``uuid6.uuid7()`` rend une *sous-classe* de ``uuid.UUID`` —
            transparente pour SQLAlchemy et asyncpg, mais le type concret changera à cette
            bascule.
        game_id: la partie concernée, absente pour un événement hors partie.
        type: nature de l'événement — l'identifiant que déclare la sous-classe d'``Event``.
            Énumération ouverte, jamais un ``ENUM`` SQL, qui ferait une migration de chaque
            nouveau type ; c'est le registre, côté Python, qui la ferme à la lecture.
        payload: la charge utile, propre à chaque type.
        occurred_at: horodatage avec fuseau, posé par la base (``now()``) sauf si l'appelant en
            fournit un — un événement rejoué garde sa date d'origine.

    Un seul index, ``(game_id, id)`` : l'UUIDv7 étant ordonné dans le temps, il donne à lui seul
    l'ordre des événements d'une partie et la pagination du flux. Tout autre index arrive par
    migration, avec la requête qui le justifie.
    """

    __tablename__ = "domain_event"
    __table_args__ = (Index(None, "game_id", "id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)
    game_id: Mapped[uuid.UUID | None]
    type: Mapped[str]
    payload: Mapped[dict[str, Any]]
    occurred_at: Mapped[datetime] = mapped_column(server_default=func.now())


EVENTS: dict[str, type["Event"]] = {}
"""Les types d'événements du domaine, sous l'identifiant qui les désigne sur le fil.

**Déclarer une sous-classe d'``Event``, c'est ajouter une entrée ici** — l'inscription est faite
par ``__init_subclass__``, donc aucun type ne peut exister sans être décodable, et aucune liste
centrale n'est à tenir à jour. C'est ce dictionnaire que le bus interroge pour rendre à un message
la classe qui l'a produit.
"""


class Event(BaseModel):
    """Un événement de domaine, typé — ce qu'on publie, par opposition à la ligne qu'on journalise.

    Une sous-classe déclare son identifiant de type et ses champs propres ::

        class TileCaptured(Event):
            type: ClassVar[str] = "tile.captured"

            tile: int

    #44 ne livre **aucun type métier** : le premier vient avec le domaine Partie.

    Attributs :
        type: l'identifiant du type, **déclaré dans le corps de la sous-classe**. En anglais,
            pointé, ``entité.participe`` : c'est un identifiant technique, stocké tel quel dans la
            colonne ``type`` du journal, donc soumis à la même règle que les noms de tables.
        game_id: la partie concernée. Absent, l'événement est journalisé et **jamais publié** — il
            n'a pas de canal.
        id: l'identifiant de la ligne, ``None`` tant que l'événement n'est pas publié. C'est
            l'UUIDv7 du journal, donc le futur ``Last-Event-ID`` de la SSE (§13.3).
        occurred_at: l'horodatage de la ligne, ``None`` tant que l'événement n'est pas publié.

    ``extra="forbid"`` : à la réception, une clé que la classe ne connaît pas fait échouer le
    décodage au lieu d'être jetée en silence. Le fil est une frontière, même entre nos propres
    processus.

    Deux conséquences de l'inscription automatique, à connaître avant de s'y heurter :

    - une sous-classe qui **omet** ``type`` échoue à sa déclaration sur un ``AttributeError: type``
      nu — l'erreur est immédiate, à l'import, mais elle ne dit pas ce qui manque ;
    - **on ne sous-classe pas un type d'événement existant** : l'identifiant hérité est déjà
      inscrit, donc la déclaration lève. Une variante d'un type est un type à part entière, avec
      son propre identifiant.
    """

    model_config = ConfigDict(extra="forbid")

    type: ClassVar[str]

    game_id: uuid.UUID | None = None
    id: uuid.UUID | None = None
    occurred_at: datetime | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Inscrit la sous-classe au registre, sous l'identifiant qu'elle déclare.

        Raises:
            ValueError: si l'identifiant est déjà pris. Deux classes sous le même identifiant, et
                la seconde remplacerait la première en silence : les abonnés décoderaient alors
                dans la mauvaise classe, longtemps après le copier-coller qui en est la cause.
        """
        super().__init_subclass__(**kwargs)
        if cls.type in EVENTS:
            raise ValueError(f"identifiant de type déjà inscrit : {cls.type}")
        EVENTS[cls.type] = cls
