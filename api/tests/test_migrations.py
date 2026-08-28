"""Chaque migration se joue en montée et en descente sur le PostgreSQL de l'environnement."""

import asyncio
from collections.abc import Callable

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, inspect

from arpendo_api.core.settings import Settings
from arpendo_api.db.engine import create_engine


def interroger[T](lecture: Callable[[Connection], T]) -> T:
    """Exécute une lecture synchrone sur une connexion neuve, dans sa propre boucle.

    Le test est synchrone (voir la fixture `schema`) : le moteur async se pilote donc par
    `asyncio.run`, avec un moteur jetable, libéré avant de rendre la main.
    """

    async def _lire() -> T:
        moteur = create_engine(Settings())
        try:
            async with moteur.connect() as connexion:
                return await connexion.run_sync(lecture)
        finally:
            await moteur.dispose()

    return asyncio.run(_lire())


def revisions_appliquees() -> tuple[str, ...]:
    return interroger(lambda c: MigrationContext.configure(c).get_current_heads())


def tables() -> set[str]:
    return set(interroger(lambda c: inspect(c).get_table_names()))


def test_les_migrations_montent_descendent_et_remontent(alembic_config: Config) -> None:
    """Le journal existe à `head`, disparaît à `base`, revient — sans rien laisser derrière."""
    tete = tuple(ScriptDirectory.from_config(alembic_config).get_heads())

    command.upgrade(alembic_config, "head")
    assert revisions_appliquees() == tete
    assert "domain_event" in tables()

    command.downgrade(alembic_config, "base")
    assert revisions_appliquees() == ()
    assert tables() == {"alembic_version"}

    command.upgrade(alembic_config, "head")
    assert revisions_appliquees() == tete
    assert "domain_event" in tables()
