"""Les journaux : un objet JSON par ligne, quel que soit le logger qui l'a émise."""

import io
import json
import logging
from collections.abc import Callable, Iterator

import pytest
import structlog
from conftest import reglages_surcharges

from arpendo_api.core.logs import UVICORN_LOGGERS, configure_logging
from arpendo_api.core.settings import Settings

Lignes = Callable[[], list[dict[str, object]]]
"""Un lecteur des lignes émises depuis le dernier appel, décodées."""


@pytest.fixture
def lignes(capsys: pytest.CaptureFixture[str]) -> Iterator[Lignes]:
    """Rend un lecteur des lignes émises, et remet les journaux en l'état après le test.

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

    La restauration, elle, couvre la racine **et** les loggers d'uvicorn : sans elle, un logger
    désarmé par un test le resterait pour toute la suite.
    """
    racine = logging.getLogger()
    handlers, niveau = list(racine.handlers), racine.level
    repris = {nom: logging.getLogger(nom) for nom in UVICORN_LOGGERS}
    etat = {nom: (list(logger.handlers), logger.propagate) for nom, logger in repris.items()}
    racine.handlers[:] = [
        handler
        for handler in handlers
        if not isinstance(handler.formatter, structlog.stdlib.ProcessorFormatter)
    ]

    yield lambda: [json.loads(ligne) for ligne in capsys.readouterr().out.splitlines() if ligne]

    racine.handlers[:] = handlers
    racine.setLevel(niveau)
    for nom, logger in repris.items():
        logger.handlers[:], logger.propagate = etat[nom]
    structlog.reset_defaults()


def test_une_ligne_structlog_est_un_objet_json_a_cles_stables(lignes: Lignes) -> None:
    configure_logging()

    structlog.get_logger("arpendo_api.essai").info("partie créée", hexagones=3)

    (ligne,) = lignes()
    assert ligne["event"] == "partie créée"
    assert ligne["level"] == "info"
    assert ligne["logger"] == "arpendo_api.essai"
    assert ligne["hexagones"] == 3
    assert str(ligne["timestamp"]).endswith("Z")


def test_une_ligne_de_la_stdlib_passe_par_le_meme_rendu(lignes: Lignes) -> None:
    """Le journal d'Alembic, celui du worker et le nôtre doivent être **un seul** flux.

    C'est ce qui fait parler `just migrate`, muet jusqu'ici : Alembic journalise ses « Running
    upgrade … » par la stdlib, et aucun handler ne les recueillait.
    """
    configure_logging()

    logging.getLogger("alembic.runtime.migration").info("Running upgrade -> ada3c4690df8")

    (ligne,) = lignes()
    assert ligne["event"] == "Running upgrade -> ada3c4690df8"
    assert ligne["level"] == "info"
    assert ligne["logger"] == "alembic.runtime.migration"
    assert str(ligne["timestamp"]).endswith("Z")


def test_la_configuration_reprend_les_loggers_que_uvicorn_a_deja_poses(lignes: Lignes) -> None:
    """uvicorn configure ses loggers **avant** d'appeler la fabrique d'application.

    Il leur pose ses propres handlers de texte et coupe leur propagation. Les laisser en l'état
    ferait deux formats sur la même sortie, dont un seul serait indexé par un agrégateur. Le test
    monte donc cet état de départ, sans quoi il ne prouverait rien : dans un processus de test,
    uvicorn n'a jamais tourné et ces loggers sont vierges.
    """
    for nom in UVICORN_LOGGERS:
        logger = logging.getLogger(nom)
        logger.addHandler(logging.StreamHandler(io.StringIO()))
        logger.propagate = False

    configure_logging()

    logging.getLogger("uvicorn.access").info("GET /health 200")

    (ligne,) = lignes()
    assert ligne["event"] == "GET /health 200"
    assert ligne["logger"] == "uvicorn.access"


def test_configurer_deux_fois_n_ajoute_pas_un_second_handler(lignes: Lignes) -> None:
    """Trois points d'entrée appellent cette fonction, et rien ne garantit qu'un seul le fera.

    Un second handler ne casserait rien de visible : il doublerait chaque ligne, ce qui se paie en
    volume d'agrégation et se découvre tard.
    """
    configure_logging()
    configure_logging()

    logging.getLogger("uvicorn.error").info("démarrage")

    assert len(lignes()) == 1


def test_la_configuration_laisse_en_place_un_handler_tiers(lignes: Lignes) -> None:
    """Mesuré : `basicConfig(force=True)` vide le handler de capture de pytest.

    Le handler d'un tiers — la capture de pytest, un agrégateur, un débogueur — est là pour une
    raison que cette fonction ne connaît pas. Elle ajoute le sien, elle ne fait pas le ménage.
    """
    tiers = logging.NullHandler()
    logging.getLogger().addHandler(tiers)

    configure_logging()

    assert tiers in logging.getLogger().handlers


TEMOINS = {
    "database_url": "dsn-temoin-que-rien-ne-doit-imprimer",
    "valkey_password": "mot-de-passe-temoin-que-rien-ne-doit-imprimer",
}
"""Des secrets choisis pour être **introuvables ailleurs** dans une ligne de journal.

Les valeurs du `.env` du poste ne conviennent pas : la sienne est `arpendo`, sous-chaîne du nom du
paquet, donc présente dans le champ `logger` de chaque ligne. Le test échouerait sur une fuite
qui n'en est pas, et la vraie fuite passerait inaperçue au milieu du bruit.
"""


def test_une_exception_journalisee_sort_rendue_sans_divulguer_les_reglages(lignes: Lignes) -> None:
    """Une trace est le chemin le plus court entre un objet de configuration et un agrégateur.

    Les réglages y arrivent par la variable locale d'une frame, par un `extra`, ou — comme ici —
    parce que quelqu'un les a liés à la ligne. L'emballage `SecretStr` doit survivre au rendu
    JSON, qui sérialise par son `repr` tout objet qu'il ne sait pas convertir.
    """
    reglages: Settings = reglages_surcharges(TEMOINS)
    configure_logging()

    try:
        raise RuntimeError("connexion refusée")
    except RuntimeError:
        structlog.get_logger("arpendo_api.essai").exception("échec", reglages=reglages)

    (ligne,) = lignes()
    rendu = json.dumps(ligne)
    assert "RuntimeError: connexion refusée" in str(ligne["exception"])
    assert not [secret for secret in TEMOINS.values() if secret in rendu]
