"""Le journal d'événements de domaine — la table ``domain_event`` (cadrage §12.6).

Tout ce qui arrive dans une partie s'y écrit, structuré : c'est la source de l'audit, du
débogage et du flux d'activité (§11). Ce module ne porte que le **modèle** ; la publication, le
typage des événements et leur consommation par le worker viennent avec le bus (#44).
"""

import uuid
from datetime import datetime
from typing import Any

import uuid6
from sqlalchemy import Index, func
from sqlalchemy.orm import Mapped, mapped_column

from arpendo_api.db.base import Base


class DomainEvent(Base):
    """Une ligne du journal.

    Attributs :
        id: identifiant UUIDv7 (§12.4) — triable et non énumérable. Généré côté Python, à
            l'insertion. **Seul point d'appel de ``uuid6``** : Python 3.14 apporte
            ``uuid.uuid7()`` ; à la mise à jour de ``api/.python-version``, remplacer l'appel et
            retirer la dépendance.
        game_id: la partie concernée, absente pour un événement hors partie.
        type: nature de l'événement, texte libre — énumération ouverte, typée en Python par #44,
            jamais un ``ENUM`` SQL, qui ferait une migration de chaque nouveau type.
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
