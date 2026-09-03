"""Les journaux : un objet JSON par ligne, quel que soit le logger qui l'a émise."""

import io
import json
import logging

import structlog
from alembic import command
from alembic.config import Config
from conftest import Lignes, reglages_surcharges

from arpendo_api.core.logs import UVICORN_LOGGERS, configure_logging
from arpendo_api.core.settings import Settings


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


def test_le_handler_d_un_tiers_ne_fait_pas_passer_la_configuration_pour_faite(
    lignes: Lignes,
) -> None:
    """Le prédicat d'idempotence doit reconnaître **notre** handler, pas un genre de handler.

    Un `ProcessorFormatter` n'appartient à personne : le SDK Sentry, un agrégateur, un tiers
    quelconque peut en poser un. Si la garde s'y fiait, `configure_logging` rendrait la main sans
    poser son `JSONRenderer`, sans reprendre les loggers d'uvicorn et sans poser le niveau — soit
    les deux formats sur la même sortie que ce module existe pour empêcher, et précisément dans
    l'environnement où l'on a le plus besoin des journaux.
    """
    imposteur = logging.NullHandler()
    imposteur.setFormatter(
        structlog.stdlib.ProcessorFormatter(processors=[structlog.dev.ConsoleRenderer()])
    )
    logging.getLogger().addHandler(imposteur)

    configure_logging()

    logging.getLogger("uvicorn.access").info("GET /health 200")

    (ligne,) = lignes()
    assert ligne["event"] == "GET /health 200"


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


def test_l_environnement_des_migrations_ouvre_les_journaux_a_son_tour(
    lignes: Lignes, alembic_config: Config
) -> None:
    """`env.py` est le troisième point d'entrée, et le seul dont c'est la **raison d'être**.

    L'api et le worker journaliseraient de toute façon quelque chose ; Alembic, lui, était
    entièrement muet — ses « Running upgrade … » partent sur un logger qu'aucun handler ne
    recueillait, et `just migrate` ne parlait que par son code de retour.

    Le test n'appelle **pas** `configure_logging()` : c'est tout l'objet, il éprouve le *câblage*.
    Mesuré : sans l'appel dans `env.py`, la suite entière reste au vert.

    `upgrade` sur un schéma déjà à `head` n'applique aucune migration mais journalise quand même
    son ouverture de contexte — c'est ce qui rend ce test rapide et sans effet de bord.
    """
    command.upgrade(alembic_config, "head")

    emetteurs = {ligne["logger"] for ligne in lignes()}
    assert "alembic.runtime.migration" in emetteurs
