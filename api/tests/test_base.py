"""Les conventions de schéma de `db.base` s'appliquent à tout modèle, sans rien répéter."""

import uuid
from datetime import datetime
from typing import Any

from conftest import ddl, table_de
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import CreateIndex, CreateTable

from arpendo_api.db.base import Base


class Mesure(Base):
    """Un modèle jetable qui n'annote que des types Python : le DDL doit venir de la base."""

    __tablename__ = "mesure"
    __table_args__ = (Index(None, "partie", "compteur"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    partie: Mapped[uuid.UUID | None]
    compteur: Mapped[int]
    libelle: Mapped[str]
    charge: Mapped[dict[str, Any]]
    survenu_a: Mapped[datetime]


def test_les_annotations_python_donnent_les_types_du_cadrage() -> None:
    """BIGINT partout, horodatages avec fuseau, JSONB, text — cadrage §12.4, §13.6."""
    table = ddl(CreateTable(table_de(Mesure)))

    assert "compteur BIGINT NOT NULL" in table
    assert "survenu_a TIMESTAMP WITH TIME ZONE NOT NULL" in table
    assert "charge JSONB NOT NULL" in table
    assert "libelle TEXT NOT NULL" in table
    assert "id UUID NOT NULL" in table
    assert "partie UUID" in table


def test_les_contraintes_et_index_sont_nommes_par_convention() -> None:
    """Un `downgrade` ne peut retirer que ce qu'il sait nommer."""
    mesure = table_de(Mesure)
    assert "CONSTRAINT pk_mesure PRIMARY KEY (id)" in ddl(CreateTable(mesure))
    (index,) = mesure.indexes
    assert "INDEX ix_mesure_partie_compteur ON mesure (partie, compteur)" in ddl(CreateIndex(index))
