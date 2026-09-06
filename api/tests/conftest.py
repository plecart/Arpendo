import json
import logging
import uuid
from collections.abc import AsyncIterator, Callable, Iterator, Mapping
from pathlib import Path

import pytest
import structlog
from alembic import command
from alembic.config import Config
from evenements import PREFIXE
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from magasins import magasins_de_la_suite
from sqlalchemy import Table, delete, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.schema import CreateIndex, CreateTable

from arpendo_api.core import resources
from arpendo_api.core.journal import DomainEvent
from arpendo_api.core.logs import UVICORN_LOGGERS, JsonHandler
from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app

Lignes = Callable[[], list[dict[str, object]]]
"""Un lecteur des lignes de journal émises depuis le dernier appel, décodées."""

VALKEY_SUR_UN_PORT_FERME = {"valkey_url": "redis://127.0.0.1:1/0"}
"""Un Valkey absent, décrit une seule fois pour les modules qui éprouvent une panne de cache.

Surcharge de `settings` par paramétrisation indirecte. Sur un runner Linux, le port fermé est
refusé aussitôt ; sur un poste dont le pare-feu filtre la boucle locale, la connexion expire au
bout du délai du client. Les deux mènent au même verdict, jamais à la même durée.
"""


def ddl(element: CreateTable | CreateIndex) -> str:
    """Le SQL qu'un élément de schéma produirait sur PostgreSQL — sans base ni connexion.

    Les conventions de `db.base` s'observent dans le DDL compilé : c'est là, et nulle part dans
    l'objet Python, qu'un `Mapped[int]` devient un `BIGINT`.
    """
    dialecte = postgresql.dialect()  # type: ignore[no-untyped-call]  # SQLAlchemy ne l'annote pas
    return str(element.compile(dialect=dialecte))


def table_de(modele: type[DeclarativeBase]) -> Table:
    """La `Table` d'un modèle déclaratif, avec le type qu'elle a vraiment.

    SQLAlchemy annote `__table__` en `FromClause` — assez large pour une vue ou une jointure —
    alors qu'un modèle à `__tablename__` porte toujours une `Table` : c'est elle que `CreateTable`
    exige, et elle seule connaît ses index.
    """
    table = modele.__table__
    assert isinstance(table, Table)
    return table


RACINE = Path(__file__).resolve().parent.parent.parent
"""La racine du dépôt : les fichiers de configuration gardés par la suite y vivent."""

COMPOSE = RACINE / "infra" / "docker-compose.yml"
"""Le compose **local**, en chemin absolu — la suite peut être lancée d'ailleurs que d'`api/`.

Celui-là et pas un autre : les invariants qui le lisent portent sur l'application qui tourne
**sur le poste, pendant la suite** — la partition de sa configuration entre points d'entrée, et la
séparation de sa base Valkey d'avec celle des tests. Un compose de production (#45) décrira une
pile que personne ne lève ici.
"""

ENV_EXAMPLE = RACINE / ".env.example"
"""Le modèle de `.env` — la seule déclaration des valeurs que le poste et le compose se partagent.

Lu par les gardes qui portent sur un invariant **réparti** entre lui et `infra/docker-compose.yml` :
une valeur proposée ici et relayée là-bas n'est cohérente nulle part ailleurs, et un commentaire de
chaque côté ne la tient pas.
"""


def variables_des_reglages() -> set[str]:
    """Toutes les variables d'environnement que `Settings` lit — requises ou non.

    **Dérivées des champs du modèle, jamais recopiées.** C'est la seule représentation de cet
    ensemble dans la suite : ajouter un champ étend d'un coup la partition des services du compose,
    sans que personne ait à tenir une seconde liste à jour. Une liste écrite à la main
    sous-couvrirait en silence, ce qui est le pire des deux mondes : verte et fausse.

    `pydantic_settings` fait correspondre le nom de champ à la variable en majuscules, sans
    préfixe — `env_prefix` vide et `case_sensitive` faux dans la configuration du modèle.

    Returns:
        Les noms de variables, en majuscules.
    """
    return {nom.upper() for nom in Settings.model_fields}


def variables_requises() -> set[str]:
    """Celles de `variables_des_reglages` sans lesquelles `Settings` refuse de se construire.

    Même dérivation et même convention de nommage ; seul le filtre change.

    Returns:
        Les noms de variables, en majuscules. Un champ pourvu d'un défaut en est exclu : son
        absence n'empêche rien.
    """
    return {nom.upper() for nom, champ in Settings.model_fields.items() if champ.is_required()}


def reglages_surcharges(surcharges: Mapping[str, object]) -> Settings:
    """Les réglages de l'environnement, amendés — et **revalidés**.

    `model_copy(update=…)` poserait les valeurs telles quelles, sans repasser par les validateurs :
    un test pourrait alors décrire une configuration que `Settings` refuse en production, et
    prouver quelque chose d'une application qui ne démarrerait jamais. On reconstruit donc plutôt
    qu'on ne modifie.

    Args:
        surcharges: les champs à remplacer, par nom d'attribut. Vide, on rend l'environnement tel
            qu'il est.

    Returns:
        Des réglages valides, secrets compris — `model_dump()` rend les `SecretStr` intacts, et
        la revalidation les réaccepte sans les aplatir en `'**********'`.

    Raises:
        pydantic.ValidationError: si la surcharge décrit un environnement invalide.
    """
    return Settings.model_validate({**Settings().model_dump(), **surcharges})


@pytest.fixture
def settings(request: pytest.FixtureRequest) -> Settings:
    """Les réglages de l'environnement de test — donc de vrais services.

    En local, ce sont ceux du `.env` que le justfile charge, et les services que `just up`
    démarre ; en CI, ceux du job et les conteneurs `services:` du workflow. Aucun double : une
    connexion simulée ne prouverait rien de ce que cette configuration existe pour garantir.

    Un test qui a besoin d'un environnement dégradé le décrit par une paramétrisation indirecte,
    et hérite alors de toute la chaîne (`app`, `client`) sans la reconstruire ::

        @pytest.mark.parametrize("settings", [{"valkey_url": "redis://127.0.0.1:1/0"}],
                                 indirect=True)
    """
    return reglages_surcharges(getattr(request, "param", {}))


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    """Une application dont le cycle de vie a réellement tourné.

    `ASGITransport` ne déclenche pas le `lifespan` : sans ce contexte, ni le moteur ni le client
    Valkey n'existeraient, et les tests parleraient à une application à moitié démarrée.
    """
    application = create_app(settings)
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Client HTTP branché directement sur l'application, sans réseau ni serveur."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def lignes(capsys: pytest.CaptureFixture[str]) -> Iterator[Lignes]:
    """Rend un lecteur des lignes de journal émises, et remet les journaux en l'état après le test.

    **C'est au test d'appeler `configure_logging()`, jamais à cette fixture.** Mesuré : pytest
    substitue un `CaptureIO` **neuf** entre la phase de préparation et la phase d'appel — deux
    identités différentes pour `sys.stdout`. Un `StreamHandler` construit en préparation reste
    branché sur le tampon de la préparation, mort au moment où le test écrit, et la sortie
    paraît vide sans que rien ne l'explique.

    Elle **désinstalle** aussi le handler qu'un test précédent aurait laissé : `create_app` appelle
    `configure_logging`, donc le premier test qui construit une application en pose un pour toute
    la session — et l'idempotence ferait alors de tous les appels d'ici des `return` immédiats,
    branchés sur un tampon mort. C'est une propriété réelle de la conception, pas un artefact :
    le handler vit dans l'arbre de logging du processus, que la suite partage.

    La restauration couvre la racine, les loggers d'uvicorn **et** le contexte lié : sans elle, un
    logger désarmé ou un `request_id` oublié par un test le resterait pour toute la suite.
    """
    racine = logging.getLogger()
    handlers, niveau = list(racine.handlers), racine.level
    repris = {nom: logging.getLogger(nom) for nom in UVICORN_LOGGERS}
    etat = {nom: (list(logger.handlers), logger.propagate) for nom, logger in repris.items()}
    racine.handlers[:] = [handler for handler in handlers if not isinstance(handler, JsonHandler)]

    yield lambda: [json.loads(ligne) for ligne in capsys.readouterr().out.splitlines() if ligne]

    racine.handlers[:] = handlers
    racine.setLevel(niveau)
    for nom, logger in repris.items():
        logger.handlers[:], logger.propagate = etat[nom]
    structlog.contextvars.clear_contextvars()
    structlog.reset_defaults()


@pytest.fixture(scope="session", autouse=True)
def magasins() -> Iterator[None]:
    """Déroute toute la session vers des magasins que cette suite est seule à posséder.

    **Première fixture de la session, et `autouse` pour qu'aucun test n'ait à la demander** :
    l'environnement doit être posé avant la première lecture de la configuration, par qui que ce
    soit — les fixtures d'ici, l'``env.py`` d'Alembic, le test des migrations, et le sous-processus
    du worker, qui hérite de l'environnement du processus. Elle ne repose pas sur l'ordre de
    déclaration, qui n'est pas un contrat de pytest : `schema` la **demande** explicitement.

    Elle ne touche à rien dans ``api/src/`` — le paquet lit déjà toute sa configuration par
    ``Settings``, et ``Settings`` lit l'environnement (cadrage §13.9 règle 5). C'est ce qui permet
    à l'isolation de tenir en un seul point.

    ``MonkeyPatch.context()`` plutôt que ``os.environ`` à la main : la fixture homonyme est
    cantonnée au test, et cette forme est celle que pytest documente pour obtenir la même
    restauration à portée de session — sans le ``try``/``finally`` qu'on finit toujours par oublier.
    """
    with magasins_de_la_suite() as urls, pytest.MonkeyPatch.context() as patch:
        for nom, valeur in urls.items():
            patch.setenv(nom, valeur)
        yield


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    """La configuration d'Alembic — `[tool.alembic]` du `pyproject.toml`, sans `alembic.ini`.

    Chemin absolu, ancré sur `RACINE` : la suite peut être lancée d'ailleurs que depuis `api/`.
    """
    return Config(toml_file=str(RACINE / "api" / "pyproject.toml"))


@pytest.fixture(scope="session", autouse=True)
def schema(alembic_config: Config, magasins: None) -> None:
    """Monte le schéma à `head` avant la suite : après `just up`, `just test` se suffit.

    Synchrone, et c'est nécessaire : `env.py` appelle `asyncio.run()`, qui refuse de démarrer
    dans une boucle déjà en cours — celle qu'un test asynchrone aurait ouverte.

    Elle demande `magasins` alors qu'elle n'en lit rien : c'est ce qui **ordonne** les deux. Une
    ceinture, et non un correctif — mesuré : dépendance retirée *et* `magasins` déclarée après
    cette fixture, le schéma se monte quand même sur la base de la suite. C'est l'ordre des
    fixtures `autouse` de même portée qui n'est pas un contrat de pytest ; s'en remettre à ce qu'on
    observe aujourd'hui, c'est faire dépendre l'isolation d'un détail d'implémentation. Aucun test
    ne tient cette dépendance : la retirer laisse la suite verte.
    """
    command.upgrade(alembic_config, "head")


@pytest.fixture
def partie() -> uuid.UUID:
    """Une partie propre à chaque test — aucun test ne voit ce qu'un autre a écrit.

    Sans elle, l'isolation reposerait sur l'ordre d'exécution et sur le nettoyage d'un voisin.

    **C'est aussi la seule chose qui isole le bus entre deux suites concurrentes**, et `magasins`
    n'y change rien : le pub/sub ignore l'index de base de données, donc une suite réservée sur la
    7 reçoit ce qu'une suite réservée sur la 4 publie. Un canal à **nom fixe** — canal système,
    verrou, annonce du worker — remettrait les suites en contact, et la séparation des magasins ne
    le rattraperait pas.
    """
    return uuid.uuid4()


def fabrique_de(app: FastAPI) -> async_sessionmaker[AsyncSession]:
    """La fabrique de sessions que le cycle de vie a rangée dans ``app.state``."""
    fabrique: async_sessionmaker[AsyncSession] = app.state.sessionmaker
    return fabrique


async def evenements_persistes(app: FastAPI, partie: uuid.UUID) -> list[DomainEvent]:
    """Ce que voit une session *neuve* — donc ce qui a réellement été commis."""
    async with fabrique_de(app)() as session:
        resultat = await session.execute(
            select(DomainEvent).where(DomainEvent.game_id == partie).order_by(DomainEvent.id)
        )
        return list(resultat.scalars())


@pytest.fixture
async def journal_nettoye(app: FastAPI, partie: uuid.UUID) -> AsyncIterator[None]:
    """Retire ce que le test a délibérément commis — la base est partagée par toute la suite.

    Le nettoyage porte sur le **préfixe de type**, et non sur la partie : un événement publié sans
    partie est journalisé lui aussi, et aucune clause sur ``game_id`` ne peut l'atteindre. Mesuré —
    avec la clause par partie, une ligne orpheline survivait à la suite, et n'en disparaissait que
    par accident, quand le test des migrations défait le schéma.
    """
    yield
    async with fabrique_de(app)() as session:
        await session.execute(delete(DomainEvent).where(DomainEvent.type.startswith(PREFIXE)))
        await session.commit()


class MoteurEspion:
    """Un moteur qui n'ouvre rien et note seulement qu'on l'a libéré.

    Doublure de notre propre fabrique, et non d'une frontière du système : c'est le seul moyen
    d'observer une libération, `AsyncEngine.dispose` ne laissant aucune trace visible.
    """

    def __init__(self) -> None:
        self.libere = False

    async def dispose(self) -> None:
        self.libere = True


@pytest.fixture
def moteur_espion(monkeypatch: pytest.MonkeyPatch) -> MoteurEspion:
    """Substitue au moteur une doublure qui note sa libération.

    La substitution vise ``core.resources``, où les fabriques sont désormais appelées : c'est le
    module qui ouvre les ressources, quel que soit l'hôte qui les consomme.
    """
    moteur = MoteurEspion()
    monkeypatch.setattr(resources, "create_engine", lambda _: moteur)
    return moteur
