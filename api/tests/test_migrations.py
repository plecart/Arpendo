"""Chaque migration se joue en montée et en descente sur le PostgreSQL de l'environnement."""

import asyncio
from collections.abc import Callable

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection

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


def test_les_migrations_montent_descendent_et_remontent(alembic_config: Config) -> None:
    tete = tuple(ScriptDirectory.from_config(alembic_config).get_heads())

    command.upgrade(alembic_config, "head")
    assert revisions_appliquees() == tete

    command.downgrade(alembic_config, "base")
    assert revisions_appliquees() == ()

    command.upgrade(alembic_config, "head")
    assert revisions_appliquees() == tete
