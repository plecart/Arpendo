"""La base déclarative : les conventions de schéma, posées une fois pour tous les modèles.

Un modèle n'annote que des types Python — ``Mapped[int]``, ``Mapped[datetime]`` — et c'est ici
que chaque type reçoit sa forme SQL, la même pour toute table du projet :

- ``int`` → ``BIGINT`` — cadrage §12.4 : « BIGINT partout pour scores et compteurs, jamais
  int32 » ; §13.6 : un index H3 tient dans 64 bits.
- ``datetime`` → ``TIMESTAMP WITH TIME ZONE`` — un horodatage sans fuseau est ambigu dès que deux
  machines en parlent.
- ``dict[str, Any]`` → ``JSONB`` — interrogeable et indexable ; ``JSON`` n'est qu'un texte vérifié.
- ``str`` → ``TEXT`` — PostgreSQL ne gagne rien à borner un ``VARCHAR`` ; une longueur est une
  règle métier, donc une contrainte.
- ``uuid.UUID`` → ``UUID`` — défaut de SQLAlchemy, repris tel quel ; les identifiants sont des
  UUIDv7 (§12.4), générés côté Python.

Un ``Mapped[int]`` ne **peut** donc pas produire d'``INTEGER`` : la règle du §12.4 n'est pas un
rappel en revue de code, elle est mécanique.

Les contraintes et index sont **nommés par convention** — ``pk_<table>``, ``fk_<table>_<colonnes>_
<table visée>``, ``uq_…``, ``ck_…``, ``ix_<table>_<colonnes>``. Sans nom déterministe, PostgreSQL en
invente un, et une migration de descente ne sait pas quoi retirer.

Ajouter un modèle, c'est hériter de ``Base`` et annoter ; ajouter une convention, c'est une entrée
dans l'une des deux tables ci-dessous.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, MetaData, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe mère de tous les modèles mappés du projet.

    ``Base.metadata`` est ce qu'Alembic compare au schéma réel pour générer une migration :
    tout modèle doit être importé avant, sinon sa table passe pour supprimée.
    """

    metadata = MetaData(
        naming_convention={
            "pk": "pk_%(table_name)s",
            "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "ix": "ix_%(table_name)s_%(column_0_N_name)s",
        }
    )
    type_annotation_map = {
        int: BigInteger,
        datetime: DateTime(timezone=True),
        dict[str, Any]: JSONB,
        str: Text,
    }
