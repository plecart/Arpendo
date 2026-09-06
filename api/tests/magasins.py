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
from urllib.parse import urlsplit, urlunsplit

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from arpendo_api.core.settings import Settings
from arpendo_api.core.valkey import create_valkey

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
système le recycle — d'où la création idempotente de :func:`_base_postgresql`.

Écarté : un nom stable par worktree, recréé à chaque lancement. Deux terminaux du même worktree —
le cas même que cette PR doit rendre vert — se détruiraient.
"""

VALKEY_URL = os.environ["VALKEY_URL"]
"""L'URL Valkey de l'environnement, **captée avant que la suite ne pose la sienne**.

Comme :data:`DATABASE_URL`, lue à l'import. La base logique qu'elle nomme devient celle des
**verrous** : c'est la seule que les suites partagent, et c'est ce qui leur permet de s'entendre
sur un index chacune.
"""


def base_logique(url: str) -> int:
    """L'index de base de données que porte une URL Valkey — zéro si elle n'en nomme aucune.

    `redis://hôte:6379/2` → 2 ; `redis://hôte:6379` → 0, qui est le défaut du protocole.

    Args:
        url: une URL Valkey ou Redis.

    Returns:
        L'index, tel que le client l'emploiera.
    """
    chemin = urlsplit(url).path.strip("/")
    return int(chemin) if chemin else 0


INDEX_DES_VERROUS = base_logique(VALKEY_URL)
"""La base logique où les suites se réservent leurs index — celle de l'environnement.

Elle n'est donc **plus candidate** : une suite qui la réservait la viderait, et effacerait du même
coup les réservations de toutes les autres.
"""

INDEX_CANDIDATS = tuple(index for index in range(2, 16) if index != INDEX_DES_VERROUS)
"""Les bases logiques qu'une suite peut se réserver.

À partir de 2 : la 0 est celle de l'application du compose, et la 1 celle des verrous sur un poste
comme en CI. Jusqu'à 15, le nombre de bases qu'un Valkey sert par défaut — monter ``databases``
dans le compose et dans la CI a été écarté, ce serait un réglage de production posé pour les tests.

L'exclusion de :data:`INDEX_DES_VERROUS` ne coûte rien et retire une panne : un environnement qui
poserait `VALKEY_URL` sur la 3 verrait la première suite vider les verrous de toutes les autres,
sans que rien ne le signale avant la corruption. Ce jeu est **gardé de l'extérieur** —
``test_isolation`` le confronte à la base de l'application et à celle des verrous : une assertion
qui se contenterait de vérifier que l'index tiré en fait partie ne mesurerait rien.
"""

CLE_DU_VERROU = "arpendo:tests:base:{index}"
"""La clé qui dit qu'une base logique est prise, et par qui.

Sa valeur est le pid du propriétaire : elle ne sert à rien au protocole — c'est ``NX`` qui tranche
— mais elle est ce qu'on lit quand on cherche à qui appartient un verrou qui traîne.
"""

BAIL_DU_VERROU = 3600
"""Secondes au bout desquelles un verrou est réputé abandonné, et l'index de nouveau libre.

Filet contre le verrou orphelin d'une suite tuée : sans échéance, un `kill -9` retirerait un index
du jeu jusqu'au prochain `FLUSHALL`. Une heure est trois ordres de grandeur au-dessus d'une suite
— dix secondes — ce qui rend inoffensive la libération inconditionnelle de :func:`_liberer`.
"""

DSN_DE_LA_SUITE = (
    make_url(DATABASE_URL).set(database=BASE_DE_LA_SUITE).render_as_string(hide_password=False)
)
"""Le DSN d'origine, pointé sur la base de la suite — identifiants, hôte et port inchangés.

``hide_password=False`` : ce DSN est remis à SQLAlchemy, jamais affiché. C'est ``Settings`` qui le
masque partout où les réglages se lisent, en le portant dans un ``SecretStr``.
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
        yield DSN_DE_LA_SUITE
    finally:
        _administrer(DETRUIRE_LA_BASE)


def _url_de_index(index: int) -> str:
    """L'URL d'origine, pointée sur une autre base logique — hôte et port inchangés.

    Args:
        index: la base logique visée.

    Returns:
        L'URL complète.
    """
    return urlunsplit(urlsplit(VALKEY_URL)._replace(path=f"/{index}"))


def _client(url: str) -> Redis:
    """Le client Valkey de l'environnement, pointé sur `url`.

    ``Settings`` est construit avec l'URL en argument plutôt que lue dans l'environnement : ce
    module tourne des deux côtés de la substitution — avant, pour réserver ; après, pour libérer —
    et un client qui suivrait l'environnement viserait deux serveurs différents selon le moment.
    Le mot de passe et le reste de la configuration, eux, viennent bien de l'environnement.

    Args:
        url: l'URL Valkey à joindre.

    Returns:
        Le client, à fermer — ``async with`` s'en charge.
    """
    return create_valkey(Settings(valkey_url=url))


async def _reserver() -> int:
    """Prend la première base logique libre, et la vide.

    ``SET … NX EX`` est **atomique** : deux suites qui démarrent au même instant ne peuvent pas
    obtenir le même index, là où un tirage sur le pid les ferait entrer en collision une fois sur
    quatorze — soit exactement l'intermittence de #94, reproduite plus rarement.

    Le ``FLUSHDB`` qui suit ne détruit rien qui ait un propriétaire : la base vient d'être réservée,
    donc ce qu'elle contient encore appartient à une suite tuée, dont plus personne n'attend rien.

    Returns:
        L'index réservé.

    Raises:
        RuntimeError: si les quatorze bases sont prises — autant de suites concurrentes sur le
            poste, ou des verrous orphelins que le bail n'a pas encore libérés.
    """
    async with _client(VALKEY_URL) as verrous:
        for index in INDEX_CANDIDATS:
            pris = await verrous.set(
                CLE_DU_VERROU.format(index=index), os.getpid(), nx=True, ex=BAIL_DU_VERROU
            )
            if pris:
                async with _client(_url_de_index(index)) as base:
                    await base.flushdb()
                return index
    raise RuntimeError(
        f"aucune base logique Valkey libre parmi {INDEX_CANDIDATS} : autant de suites tournent "
        f"sur ce poste, ou des verrous `{CLE_DU_VERROU.format(index='*')}` traînent sur la base "
        f"{INDEX_DES_VERROUS}. Ils expirent seuls au bout de {BAIL_DU_VERROU} secondes"
    )


async def _liberer(index: int) -> None:
    """Rend la base logique au jeu des candidates.

    La suppression est inconditionnelle : vérifier que le verrou porte encore notre pid ne serait
    pas atomique de toute façon, et la seule façon de libérer celui d'une voisine est d'avoir
    dépassé le bail — trois ordres de grandeur au-dessus de la durée d'une suite.

    Args:
        index: la base logique à libérer.
    """
    async with _client(VALKEY_URL) as verrous:
        await verrous.delete(CLE_DU_VERROU.format(index=index))


@contextmanager
def _base_valkey() -> Iterator[str]:
    """Réserve une base logique pour la durée de la session, et la libère en sortant.

    Elle n'est pas vidée à la sortie : ce que la suite y laisse ne gêne personne tant que la base
    est réservée, et la prochaine à l'obtenir la videra — d'où un seul ``FLUSHDB``, à la prise, où
    il est aussi le seul à pouvoir servir (une suite tuée n'en joue aucun).

    Yields:
        L'URL de la base logique de la suite, à poser dans ``VALKEY_URL``.
    """
    index = asyncio.run(_reserver())
    try:
        yield _url_de_index(index)
    finally:
        asyncio.run(_liberer(index))


@contextmanager
def magasins_de_la_suite() -> Iterator[dict[str, str]]:
    """Réserve les magasins de la suite, et rend l'environnement qui les désigne.

    Yields:
        Les variables d'environnement à poser **avant toute lecture de la configuration**, par nom.
        Les poser suffit à dérouter tout le processus : le paquet ne lit sa configuration que par
        ``Settings``, et le sous-processus du worker hérite de l'environnement.
    """
    with _base_postgresql() as database_url, _base_valkey() as valkey_url:
        yield {"DATABASE_URL": database_url, "VALKEY_URL": valkey_url}
