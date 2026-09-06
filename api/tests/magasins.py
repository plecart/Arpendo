"""Les magasins que la suite se réserve pour elle seule, et rien d'autre.

Deux suites lancées en même temps sur un poste visaient la même base PostgreSQL et la même base
logique Valkey (#94). Elles s'y détruisaient par **trois** mécanismes, et le troisième dit pourquoi
l'unité d'isolation est le magasin et non la clé : les compteurs du limiteur sont observés et purgés
globalement (`SCAN ratelimit:*`, puis `DELETE`) ; les lignes du journal sont purgées par préfixe de
type ; et le test des migrations **redescend le schéma à `base`** pendant que la voisine écrit
dedans. Une clé de suite portée par les préfixes couvrirait les deux premiers — on ne partitionne
pas une table par une clé de ligne quand c'est la table qu'on supprime.

**Module neutre, sans fixture.** La fixture qui l'appelle vit dans ``conftest.py``, où pytest la
découvre ; ici ne vivent que la réservation et sa libération, appelables et lisibles seules.

Le point d'entrée est :func:`magasins_de_la_suite`, qui rend les variables d'environnement à poser
**avant toute lecture de la configuration** par qui que ce soit dans le processus : les fixtures,
l'``env.py`` d'Alembic, le test des migrations, et le sous-processus du worker, qui hérite de
l'environnement. C'est ce qui permet à l'isolation de tenir en un seul point sans qu'aucune ligne
d'``api/src/`` ne change : tout le paquet lit sa configuration par ``Settings``, et ``Settings`` lit
l'environnement.
"""

import asyncio
import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]
"""Le DSN PostgreSQL de l'environnement, **capté avant que la suite ne pose le sien**.

Lu à l'import — donc à la collecte, avant toute fixture. C'est le point de vue de l'administrateur :
le serveur sur lequel la base de la suite se crée et se détruit, et la valeur à laquelle
``test_isolation`` compare celle sur laquelle la suite tourne réellement.
"""

PREFIXE_BASE = "arpendo_test_"
"""Ce qui distingue une base de suite d'une base d'application, à l'œil et au `\\l`.

Nommer les orphelines d'un préfixe commun est ce qui rend leur nettoyage manuel possible — voir le
README d'`api/`, section « Tester et vérifier ».
"""

BASE_DE_LA_SUITE = f"{PREFIXE_BASE}{os.getpid()}"
"""Le nom de la base de **cette** suite : le pid du processus pytest, et rien d'autre.

Un pid est unique **parmi les processus vivants**, ce qui est exactement la garantie recherchée :
deux suites concurrentes ne peuvent pas se choisir le même nom. Il ne l'est pas dans le temps — le
système le recycle — d'où la création idempotente de :func:`base_postgresql`.

Écarté : un nom stable par worktree, recréé à chaque lancement. Deux terminaux du même worktree —
le cas même que cette PR doit rendre vert — se détruiraient.
"""

DETRUIRE_LA_BASE = f'DROP DATABASE IF EXISTS "{BASE_DE_LA_SUITE}" WITH (FORCE)'
"""L'ordre joué **deux fois** : avant la création, pour la rendre idempotente, et à la sortie.

Un seul texte pour les deux, parce qu'ils doivent rester le même : une clause ``FORCE`` qui ne
serait posée qu'à la sortie laisserait la reprise d'un pid recyclé échouer sur une connexion morte.
"""


def nom_de_base(url: str) -> str:
    """Le nom de la base que désigne un DSN SQLAlchemy.

    Args:
        url: un DSN au format SQLAlchemy, ``postgresql+asyncpg://…/nom``.

    Returns:
        Le nom de la base, ou la chaîne vide si le DSN n'en nomme aucune.
    """
    return make_url(url).database or ""


def _url_de_base(url: str, nom: str) -> str:
    """Le même DSN, pointé sur une autre base — identifiants, hôte et port inchangés.

    Args:
        url: le DSN d'origine.
        nom: le nom de la base visée.

    Returns:
        Le DSN complet, **mot de passe compris** : il est remis à SQLAlchemy, pas affiché.
    """
    return make_url(url).set(database=nom).render_as_string(hide_password=False)


def _administrer(ordre: str) -> None:
    """Exécute un ordre d'administration sur le serveur, hors de toute transaction.

    ``AUTOCOMMIT`` n'est pas une préférence : PostgreSQL refuse ``CREATE DATABASE`` et
    ``DROP DATABASE`` dans un bloc transactionnel, et SQLAlchemy en ouvre un par défaut. Le moteur
    naît et meurt avec l'ordre — il n'y a pas de pool à garder chaud pour deux instructions par
    session, et une connexion qui survivrait empêcherait la destruction de la base.

    Synchrone, comme la fixture qui l'appelle : celle-ci doit rendre la main avant ``schema``, qui
    joue Alembic par ``asyncio.run`` et ne tolère donc pas d'être appelée depuis une boucle en
    cours.

    Args:
        ordre: le SQL à exécuter. Il n'est **jamais** composé depuis une donnée extérieure : les
            seuls ordres de ce module nomment :data:`BASE_DE_LA_SUITE`, dérivé du pid de ce
            processus. Un identifiant SQL ne se paramètre pas, donc rien d'autre ne doit arriver
            ici.
    """

    async def _executer() -> None:
        moteur = create_async_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
        try:
            async with moteur.connect() as connexion:
                await connexion.execute(text(ordre))
        finally:
            await moteur.dispose()

    asyncio.run(_executer())


@contextmanager
def _base_postgresql() -> Iterator[str]:
    """Crée la base de la suite pour la durée de la session, et la détruit en sortant.

    **La création est idempotente**, et c'est ce qui rattrape le seul défaut du nom par pid : un
    ``kill -9`` ne passe pas par la sortie de ce contexte et laisse la base derrière lui, que le
    système finira par proposer de nouveau en recyclant le pid. Détruire d'abord ne peut viser
    qu'une orpheline — aucun processus vivant ne porte notre pid — ce qui la distingue du balayage
    de toutes les bases ``arpendo_test_*``, écarté à l'interrogatoire : une suite entre deux tests
    peut n'avoir aucune connexion ouverte, et le balayage la tuerait.

    ``WITH (FORCE)`` coupe les connexions qui traîneraient : sans lui, un moteur qu'un test aurait
    oublié de libérer ferait échouer la destruction, et l'orpheline naîtrait d'une suite **terminée
    normalement**.

    Yields:
        Le DSN de la base de la suite, à poser dans ``DATABASE_URL``.
    """
    _administrer(DETRUIRE_LA_BASE)
    _administrer(f'CREATE DATABASE "{BASE_DE_LA_SUITE}"')
    try:
        yield _url_de_base(DATABASE_URL, BASE_DE_LA_SUITE)
    finally:
        _administrer(DETRUIRE_LA_BASE)


@contextmanager
def magasins_de_la_suite() -> Iterator[dict[str, str]]:
    """Réserve les magasins de la suite, et rend l'environnement qui les désigne.

    Yields:
        Les variables d'environnement à poser **avant toute lecture de la configuration**, par nom.
        Les poser suffit à dérouter tout le processus : le paquet ne lit sa configuration que par
        ``Settings``, et le sous-processus du worker hérite de l'environnement.
    """
    with _base_postgresql() as database_url:
        yield {"DATABASE_URL": database_url}
