"""Le journal d'événements de domaine (cadrage §12.6) : la table `domain_event`."""

import uuid
from typing import ClassVar

import pytest
from conftest import Capture, ddl
from pydantic import ValidationError
from sqlalchemy.schema import CreateIndex, CreateTable

from arpendo_api.core.journal import EVENTS, DomainEvent, Event


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
    """Le câblage du défaut est vérifié sans insérer : SQLAlchemy ne l'applique qu'à l'insertion.

    `ColumnDefault.arg` est la fabrique telle que la colonne l'a reçue ; on l'appelle avec le
    contexte d'exécution que SQLAlchemy lui passerait — `None` suffit, `uuid6.uuid7` l'ignore.
    Tester `uuid6.uuid7()` directement prouverait la bibliothèque, pas le câblage.
    """
    default = DomainEvent.__table__.c.id.default
    assert default is not None

    identifiant = default.arg(None)

    assert isinstance(identifiant, uuid.UUID)
    assert identifiant.version == 7


def test_une_sous_classe_s_inscrit_au_registre_sous_son_identifiant_de_type() -> None:
    """Déclarer la classe suffit : rien à inscrire à la main, donc rien à oublier d'inscrire."""
    assert EVENTS["test.captured"] is Capture


def test_un_identifiant_de_type_deja_inscrit_leve_a_la_declaration() -> None:
    """Sans cette garde, la seconde classe remplacerait la première en silence.

    L'erreur se paie alors très loin de sa cause : un abonné décode un message dans la mauvaise
    classe, des semaines après le copier-coller qui a dupliqué l'identifiant.
    """
    with pytest.raises(ValueError, match="test.captured"):

        class Doublon(Event):  # noqa: F841 — la déclaration EST le comportement éprouvé
            type: ClassVar[str] = "test.captured"


def test_un_evenement_neuf_n_a_ni_partie_ni_identifiant_ni_horodatage() -> None:
    """Les trois champs que la publication remplit sont vides tant qu'elle n'a pas eu lieu.

    Ils ne sont pas facultatifs par commodité : leur absence *dit* que l'événement n'est pas encore
    dans le journal, et leur présence qu'il y est, avec l'`id` qui servira de `Last-Event-ID`.
    """
    evenement = Capture(hexagones=3)

    assert (evenement.game_id, evenement.id, evenement.occurred_at) == (None, None, None)


def test_une_cle_inconnue_est_refusee_au_decodage() -> None:
    """Le fil est une frontière, même entre deux processus à nous.

    Sans `extra="forbid"`, pydantic **jette la clé en silence** — mesuré : le décodage réussit et
    l'écart entre ce qui a été publié et ce qui a été reçu ne se voit nulle part.
    """
    with pytest.raises(ValidationError):
        Capture.model_validate({"hexagones": 3, "inconnue": 1})
