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

**Les deux magasins n'ont pas le même protocole, et c'est le nombre de noms disponibles qui les
sépare** : la base PostgreSQL se taille un nom dans un espace assez vaste pour qu'on s'y ignore,
l'index Valkey se dispute quatorze places et exige donc un verrou. Le fichier est rangé dans cet
ordre — identité commune, puis un bloc par magasin, puis le point d'entrée qui les compose.
"""

import asyncio
import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlsplit, urlunsplit

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from arpendo_api.core.settings import Settings
from arpendo_api.core.valkey import create_valkey

# ─── Identité de l'exécution — commune aux deux magasins ──────────────────────

JETON_DE_LA_SUITE = uuid.uuid4().hex
"""L'identité de **cette** exécution de la suite, tirée une fois au chargement du module.

Une seule identité pour les deux magasins : elle nomme la base PostgreSQL et signe le verrou
Valkey, si bien qu'un résidu de l'un se rapproche d'un résidu de l'autre à l'œil.

**Aléatoire, et surtout pas le pid.** Un pid se réattribue, et ce qu'il faudrait écrire pour
survivre à sa réattribution serait précisément ce qu'on ne veut pas ici — une destruction avant
création. Le raisonnement complet, et les deux options écartées, sont dans le README d'`api/`,
section « Tester et vérifier » : y aller avant de croire qu'un identifiant plus lisible ferait
aussi bien.
"""

# ─── Magasin PostgreSQL — une base par suite ──────────────────────────────────

DATABASE_URL = os.environ["DATABASE_URL"]
"""Le DSN PostgreSQL de l'environnement, **capté avant que la suite ne pose le sien**.

Lu à l'import — donc à la collecte, avant toute fixture. C'est le point de vue de l'administrateur :
le serveur sur lequel la base de la suite se crée et se détruit, et la valeur à laquelle
``test_isolation`` compare celle sur laquelle la suite tourne réellement.
"""

PREFIXE_BASE = "arpendo_test_"
"""Ce qui distingue une base de suite d'une base d'application, à l'œil et au `\\l`.

Nommer les orphelines d'un préfixe commun est ce qui rend leur nettoyage manuel possible — c'est la
seule chose que leur nom ait besoin de dire, puisque le processus qui l'a créée est mort. Voir le
README d'`api/`, section « Tester et vérifier ».
"""

BASE_DE_LA_SUITE = f"{PREFIXE_BASE}{JETON_DE_LA_SUITE}"
"""Le nom de la base de cette suite. 45 caractères, bien sous les 63 d'un identifiant PostgreSQL."""

DSN_DE_LA_SUITE = (
    make_url(DATABASE_URL).set(database=BASE_DE_LA_SUITE).render_as_string(hide_password=False)
)
"""Le DSN d'origine, pointé sur la base de la suite — identifiants, hôte et port inchangés.

``hide_password=False`` : ce DSN est remis à SQLAlchemy, jamais affiché. C'est ``Settings`` qui le
masque partout où les réglages se lisent, en le portant dans un ``SecretStr``.
"""

DETRUIRE_LA_BASE = f'DROP DATABASE IF EXISTS "{BASE_DE_LA_SUITE}" WITH (FORCE)'
"""L'ordre de sortie, joué **une seule fois** et sur une base dont on sait qu'elle est à nous.

Ce qui le rend sûr n'est pas le nom mais l'ordre des opérations : on ne l'atteint qu'après un
``CREATE DATABASE`` réussi, donc la base qu'il détruit est celle que **cette** session a créée.
Une destruction jouée *avant* la création n'aurait pas cette propriété — voir
:func:`_base_postgresql`.

``WITH (FORCE)`` coupe les connexions qui traîneraient : sans lui, un moteur qu'un test aurait
oublié de libérer ferait échouer la destruction, et une orpheline naîtrait d'une suite **terminée
normalement**.
"""


def nom_de_base(url: str) -> str | None:
    """Le nom de la base que désigne un DSN SQLAlchemy.

    Args:
        url: un DSN au format SQLAlchemy, ``postgresql+asyncpg://…/nom``.

    Returns:
        Le nom de la base, ou ``None`` si le DSN n'en nomme aucune — rendu tel quel plutôt que
        ramené à la chaîne vide : un repli que rien n'atteint est du code mort, et ``None`` se lit
        mieux dans le message d'un garde que deux apostrophes accolées.
    """
    return make_url(url).database


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
            seuls ordres de ce module nomment :data:`BASE_DE_LA_SUITE`, dérivé d'un jeton tiré
            par ce module. Un identifiant SQL ne se paramètre pas, donc rien d'autre ne doit
            arriver ici.
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

    **Une création, une destruction, et rien entre les deux** — le nom n'étant jamais réattribué
    (:data:`JETON_DE_LA_SUITE`), la création ne peut pas entrer en collision, et il n'y a donc ni
    idempotence à organiser ni erreur de doublon à rattraper. Le code qui manque ici est la moitié
    de l'intérêt du jeton.

    Le ``DROP`` de sortie ne s'atteint qu'après une création réussie : il ne porte donc que sur la
    base de cette session, jamais sur celle d'une voisine. Un ``kill -9`` ne l'atteint pas du tout
    et laisse une orpheline — inoffensive, et à balayer à la main : le README d'`api/` dit pourquoi
    et comment.

    Yields:
        Le DSN de la base de la suite, à poser dans ``DATABASE_URL``.
    """
    _administrer(f'CREATE DATABASE "{BASE_DE_LA_SUITE}"')
    try:
        yield DSN_DE_LA_SUITE
    finally:
        _administrer(DETRUIRE_LA_BASE)


# ─── Magasin Valkey — une base logique par suite, réservée par un verrou ──────

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

Sa valeur est le :data:`JETON_DE_LA_SUITE` du propriétaire, et elle **porte le protocole des deux
côtés** : ``NX`` tranche la prise, la comparaison de ce jeton tranche la libération
(:data:`LIBERER_LE_VERROU`). La changer en une valeur non discriminante — un horodatage, une
constante — rendrait toute suite capable de libérer le verrou de n'importe quelle autre.

Elle **désigne aussi la base PostgreSQL du même propriétaire**, qui porte le même jeton : c'est ce
qu'on lit quand on cherche à qui appartient un verrou qui traîne.
"""

BAIL_DU_VERROU = 3600
"""Secondes au bout desquelles un verrou est réputé abandonné, et l'index de nouveau libre.

Filet contre le verrou orphelin d'une suite tuée, et **rien d'autre** : sans échéance, un `kill -9`
retirerait un index du jeu jusqu'au prochain `FLUSHALL`. Une heure vaut 360 fois la durée d'une
suite, ce qui laisse à peu près n'importe quel arrêt sur point d'arrêt tenir dans le bail.

Ce n'est pas lui qui protège la libération d'une voisine — c'est :data:`LIBERER_LE_VERROU`, qui
compare le jeton. Un bail dépassé fait perdre son index à une suite qui vit encore, jamais effacer
le verrou de quelqu'un d'autre.
"""

LIBERER_LE_VERROU = """
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        return redis.call('DEL', KEYS[1])
    end
    return 0
"""
"""Compare le jeton puis supprime, **en un seul pas** — `EVAL` exécute le script sans entrelacement.

C'est la libération que redis-py emploie pour ses propres verrous
(``redis/asyncio/lock.py``, ``LUA_RELEASE_SCRIPT``), et la raison est la même : entre un ``GET`` et
un ``DEL`` séparés, le bail peut expirer et une voisine prendre l'index — le ``DEL`` effacerait
alors *sa* réservation, une troisième suite viderait la base sous elle, et #94 renaîtrait de son
propre correctif. Éprouvé par ``test_magasins``, qui pose le verrou d'une voisine et le retrouve
intact.
"""


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
    obtenir le même index, là où un tirage au sort les ferait entrer en collision une fois sur
    quatorze — soit exactement l'intermittence de #94, reproduite plus rarement. C'est ce qui
    distingue ce magasin du précédent : quatorze places qu'il faut se répartir, contre un espace de
    noms assez vaste pour qu'un jeton suffise.

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
                CLE_DU_VERROU.format(index=index), JETON_DE_LA_SUITE, nx=True, ex=BAIL_DU_VERROU
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
    """Rend la base logique au jeu des candidates — **si le verrou est encore le nôtre**.

    La condition n'est pas une précaution de principe : le bail peut avoir expiré pendant que la
    suite tournait, et l'index appartenir déjà à une voisine. Une suppression inconditionnelle
    effacerait sa réservation, une troisième suite prendrait l'index et le viderait sous elle.
    :data:`LIBERER_LE_VERROU` fait la comparaison et la suppression en un seul pas.

    Args:
        index: la base logique à libérer.
    """
    async with _client(VALKEY_URL) as verrous:
        await verrous.eval(
            LIBERER_LE_VERROU, 1, CLE_DU_VERROU.format(index=index), JETON_DE_LA_SUITE
        )


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


# ─── Point d'entrée ───────────────────────────────────────────────────────────


@contextmanager
def magasins_de_la_suite() -> Iterator[dict[str, str]]:
    """Réserve les magasins de la suite, et rend l'environnement qui les désigne.

    Les deux contextes sont imbriqués : si la réservation Valkey échoue, la base PostgreSQL déjà
    créée est détruite en se déroulant. Un troisième magasin s'ajouterait ici, et nulle part
    ailleurs.

    Yields:
        Les variables d'environnement à poser **avant toute lecture de la configuration**, par nom.
        Les poser suffit à dérouter tout le processus : le paquet ne lit sa configuration que par
        ``Settings``, et le sous-processus du worker hérite de l'environnement.
    """
    with _base_postgresql() as database_url, _base_valkey() as valkey_url:
        yield {"DATABASE_URL": database_url, "VALKEY_URL": valkey_url}
