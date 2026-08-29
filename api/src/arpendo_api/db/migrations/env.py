"""L'environnement des migrations : ce qu'Alembic exécute pour chaque commande.

Il n'y a pas d'``alembic.ini`` — l'URL de la base vient de ``Settings``, seul lecteur de
l'environnement (cadrage §13.9 règle 5), et le moteur de ``db.engine.create_engine``, le même que
l'application : un seul endroit sait ouvrir PostgreSQL. Le moteur est asynchrone, Alembic ne
l'est pas : la recette officielle passe une connexion synchrone à Alembic par ``run_sync``.

Ce script s'exécute sur le poste (``just migrate``), dans un conteneur éphémère
(``docker compose run --rm api alembic upgrade head``) et dans la suite de tests — jamais au
démarrage de l'application (§13.9 règle 3). Il appelle ``asyncio.run`` : l'appelant ne doit pas
être lui-même dans une boucle d'événements.

**Ajouter un domaine, c'est ajouter son module de modèles aux imports ci-dessous** : Alembic
compare ``Base.metadata`` au schéma réel, et une table qu'aucun import n'a enregistrée passe pour
supprimée.
"""

import asyncio

from alembic import context
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from arpendo_api.core import journal  # noqa: F401 — enregistre `domain_event` dans Base.metadata
from arpendo_api.core.settings import Settings
from arpendo_api.db.base import Base
from arpendo_api.db.engine import create_engine


def _run_migrations(connection: Connection) -> None:
    """Joue les migrations sur une connexion synchrone — ce qu'Alembic sait piloter.

    ``compare_type`` est explicite bien qu'il soit le défaut depuis Alembic 1.12 : sans lui,
    changer le type d'une colonne ne produirait aucune migration, et un défaut de bibliothèque
    n'est pas un endroit où lire une décision du projet.
    """
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def _run_async(engine: AsyncEngine) -> None:
    """Ouvre une connexion, y joue les migrations, et libère le moteur quoi qu'il arrive.

    Le moteur naît et meurt avec la commande : une migration est un processus court, il n'y a
    pas de pool à garder chaud. Le ``finally`` couvre l'échec d'une migration comme celui de la
    connexion elle-même — sans lui, un ``upgrade`` rouge laisserait des connexions ouvertes
    jusqu'à la fin du processus.

    Args:
        engine: le moteur async de l'application, construit depuis ``Settings``.
    """
    try:
        async with engine.connect() as connection:
            await connection.run_sync(_run_migrations)
    finally:
        await engine.dispose()


asyncio.run(_run_async(create_engine(Settings())))
