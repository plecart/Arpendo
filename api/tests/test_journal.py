"""Le journal d'événements de domaine (cadrage §12.6) : la table `domain_event`."""

import uuid

from conftest import ddl
from sqlalchemy.schema import CreateIndex, CreateTable

from arpendo_api.core.journal import DomainEvent


def test_la_table_du_journal_porte_les_colonnes_du_brief() -> None:
    table = ddl(CreateTable(DomainEvent.__table__))

    assert "CREATE TABLE domain_event" in table
    assert "id UUID NOT NULL" in table
    assert "game_id UUID" in table
    assert DomainEvent.__table__.c.game_id.nullable
    assert "type TEXT NOT NULL" in table
    assert "payload JSONB NOT NULL" in table
    assert "occurred_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL" in table
    assert "CONSTRAINT pk_domain_event PRIMARY KEY (id)" in table


def test_un_seul_index_ordonne_par_partie_puis_dans_le_temps() -> None:
    """L'UUIDv7 est ordonné dans le temps : `(game_id, id)` donne l'ordre du flux d'une partie."""
    (index,) = DomainEvent.__table__.indexes

    assert "INDEX ix_domain_event_game_id_id ON domain_event (game_id, id)" in ddl(
        CreateIndex(index)
    )


def test_l_identifiant_par_defaut_est_un_uuid_v7() -> None:
    default = DomainEvent.__table__.c.id.default
    assert default is not None

    identifiant = default.arg(None)

    assert isinstance(identifiant, uuid.UUID)
    assert identifiant.version == 7
