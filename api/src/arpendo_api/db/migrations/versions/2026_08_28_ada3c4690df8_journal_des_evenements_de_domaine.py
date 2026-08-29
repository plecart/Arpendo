"""Journal des événements de domaine — la table `domain_event` (cadrage §12.6).

Migration initiale : la table du journal et son unique index `(game_id, id)`, qui donne l'ordre
des événements d'une partie (UUIDv7 ordonné dans le temps). Colonnes et types viennent de
`core.journal.DomainEvent` par les conventions de `db.base`.

Révision : ada3c4690df8
Précédente :
Créée le : 2026-08-28 21:11:58.490918
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "ada3c4690df8"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "domain_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("game_id", sa.Uuid(), nullable=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_domain_event")),
    )
    op.create_index(
        op.f("ix_domain_event_game_id_id"), "domain_event", ["game_id", "id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_domain_event_game_id_id"), table_name="domain_event")
    op.drop_table("domain_event")
