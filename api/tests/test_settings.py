import re
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import pytest
from conftest import reglages_surcharges
from pydantic import AfterValidator, SecretStr, ValidationError

from arpendo_api.core import settings as settings_module
from arpendo_api.core.settings import ConfigurationError, Settings, load_settings

MOT_DE_PASSE_POSTGRESQL = "mot-de-passe-postgresql"
MOT_DE_PASSE_VALKEY = "mot-de-passe-valkey"
SECRETS = (MOT_DE_PASSE_POSTGRESQL, MOT_DE_PASSE_VALKEY)

BLANCHES = {"vide": "", "espaces": "   ", "tabulation-et-saut": "\t\n"}
"""Les formes du vide qu'une variable d'environnement peut prendre, par nom de cas."""

SEUILS = ("RATE_LIMIT_IP_REQUESTS", "RATE_LIMIT_IP_WINDOW_SECONDS")
"""Les réglages dont la valeur est un entier borné — les seuls que `0` doit faire échouer."""

REQUISES = {
    "DATABASE_URL": (
        f"postgresql+asyncpg://arpendo:{MOT_DE_PASSE_POSTGRESQL}@127.0.0.1:5432/arpendo"
    ),
    "VALKEY_URL": "redis://127.0.0.1:6379/0",
    "VALKEY_PASSWORD": MOT_DE_PASSE_VALKEY,
    "RATE_LIMIT_IP_REQUESTS": "600",
    "RATE_LIMIT_IP_WINDOW_SECONDS": "60",
    "SENTRY_SAMPLE_RATE": "1.0",
}

FACULTATIVES = ("SENTRY_DSN",)
"""Les réglages qu'on a le droit de ne pas poser — la liste complète, et elle tient en un nom.

`SENTRY_DSN` est le seul : « absent » y est un **état légitime** (Sentry désactivé), là où toute
autre variable manquante est une configuration trouée. La fixture les retire de l'environnement
sans les reposer, pour qu'aucun test n'hérite du `.env` du poste.
"""


@pytest.fixture
def environnement_complet(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isole les tests du `.env` du poste : seules les variables posées ici existent."""
    for nom in (*REQUISES, *FACULTATIVES):
        monkeypatch.delenv(nom, raising=False)
    for nom, valeur in REQUISES.items():
        monkeypatch.setenv(nom, valeur)


def _en_clair(valeur: object) -> str:
    """La valeur d'un réglage, secret déballé et rendue en texte.

    On la confronte à ce que l'environnement portait, et l'environnement n'est fait que de
    chaînes : un seuil lu en `int` se compare donc sous sa forme écrite, pas après reconversion
    du texte attendu — sinon le test ne prouverait plus que la variable a bien été lue.
    """
    return valeur.get_secret_value() if isinstance(valeur, SecretStr) else str(valeur)


@pytest.mark.parametrize("variable", sorted(REQUISES))
def test_les_reglages_lisent_chaque_variable_de_l_environnement(
    environnement_complet: None, variable: str
) -> None:
    reglages = Settings()

    assert _en_clair(getattr(reglages, variable.lower())) == REQUISES[variable]


@pytest.mark.parametrize("manquante", sorted(REQUISES))
def test_une_variable_requise_absente_empeche_le_demarrage(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, manquante: str
) -> None:
    monkeypatch.delenv(manquante)

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize("blanche", BLANCHES.values(), ids=BLANCHES)
@pytest.mark.parametrize("videe", sorted(REQUISES))
def test_une_variable_requise_blanche_empeche_le_demarrage(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, videe: str, blanche: str
) -> None:
    monkeypatch.setenv(videe, blanche)

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize("seuil", SEUILS)
def test_un_seuil_nul_empeche_le_demarrage(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, seuil: str
) -> None:
    """Un quota de zéro requête, ou une fenêtre de zéro seconde, ne limite pas : il ferme.

    C'est une configuration qu'on ne peut avoir voulue, et que la borne basse refuse au
    démarrage plutôt que de la laisser rejeter chaque requête en production.
    """
    monkeypatch.setenv(seuil, "0")

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    "afficher",
    [repr, str, lambda reglages: str(reglages.model_dump())],
    ids=["repr", "str", "model_dump"],
)
def test_afficher_les_reglages_ne_divulgue_aucun_secret(
    environnement_complet: None, afficher: Callable[[Settings], str]
) -> None:
    affichage = afficher(Settings())

    assert [secret for secret in SECRETS if secret in affichage] == []


def test_une_surcharge_de_reglages_en_test_repasse_par_la_validation() -> None:
    """Un test ne peut décrire qu'un environnement que la production accepterait aussi.

    Sans cette garantie, un test prouverait quelque chose d'une application qui ne démarrerait
    jamais.
    """
    with pytest.raises(ValidationError):
        reglages_surcharges({"valkey_url": "   "})


def _settings_au_format_refuse(monkeypatch: pytest.MonkeyPatch) -> None:
    """Substitue à `Settings` une variante dont un validateur refuse le CONTENU d'un secret.

    Aucun validateur réel ne le fait — la docstring de `Secret` l'interdit précisément parce que
    pydantic recopie l'entrée brute dans le `input_value` de sa `ValidationError`. On monte donc
    ici l'interdit pour éprouver le chargeur sur le seul cas où il a quelque chose à assainir.
    """

    def _refuse(_: SecretStr) -> SecretStr:
        raise ValueError("format attendu : un préfixe reconnu")

    class SettingsAuFormat(Settings):
        valkey_password: Annotated[SecretStr, AfterValidator(_refuse)]

    monkeypatch.setattr(settings_module, "Settings", SettingsAuFormat)


def test_un_demarrage_refuse_n_ecrit_jamais_la_valeur_du_reglage_fautif(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """La trace d'un démarrage refusé est le dernier endroit où un secret peut fuir.

    À ce moment-là Sentry n'existe pas encore — il lit son DSN dans ces mêmes réglages — donc
    aucun assainissement d'événement ne couvre ce chemin : c'est la trace elle-même qui doit
    être propre.
    """
    _settings_au_format_refuse(monkeypatch)

    with pytest.raises(ConfigurationError) as refus:
        load_settings()

    trace = "".join(traceback.format_exception(refus.value))
    assert MOT_DE_PASSE_VALKEY not in trace
    assert "valkey_password" in str(refus.value)
    assert refus.value.__cause__ is None
    assert refus.value.__suppress_context__


def test_un_demarrage_accepte_rend_les_reglages_de_l_environnement(
    environnement_complet: None,
) -> None:
    assert load_settings() == Settings()


SOURCES = Path(__file__).resolve().parent.parent / "src"
"""L'arbre du paquet — celui que la règle ci-dessous balaie, et le seul."""

CHARGEUR = SOURCES / "arpendo_api" / "core" / "settings.py"
"""Le seul fichier exempté de la règle, désigné par son chemin complet.

Par le chemin et non par le nom : `settings.py` est un nom qu'un domaine peut reprendre, et il
s'exempterait alors de la règle sans que personne l'ait voulu.
"""

CONSTRUCTION_DIRECTE = re.compile(r"\bSettings\(\)")
"""Une construction des réglages qui court-circuite le chargeur.

Épinglée en clair plutôt qu'importée : c'est la forme écrite qu'on interdit, et la reconstruire
depuis un symbole rendrait la règle aveugle au jour où le symbole change de nom.
"""


def test_aucun_point_d_entree_ne_construit_les_reglages_sans_passer_par_le_chargeur() -> None:
    """La protection de `load_settings` ne vaut que si personne ne la contourne.

    Un `Settings()` oublié dans un point d'entrée rétablit exactement la fuite que le chargeur
    existe pour fermer, et rien ne le signalerait : le processus démarrerait normalement, et la
    trace ne serait sale que le jour où la configuration est fausse — en production, une fois.
    C'est donc un balayage de l'arbre, et non la relecture des trois appelants connus : le
    quatrième hôte du paquet héritera de la règle sans que personne ait à s'en souvenir.

    `core/settings.py` est le seul exempté : c'est lui qui construit, et sa docstring d'exemple
    montre la forme interdite ailleurs. L'exemption porte sur le **chemin** et non sur le nom de
    fichier — sinon un futur `domains/<x>/settings.py` s'exempterait tout seul, sans que personne
    l'ait décidé.
    """
    fautifs = [
        source.relative_to(SOURCES).as_posix()
        for source in SOURCES.rglob("*.py")
        if source != CHARGEUR and CONSTRUCTION_DIRECTE.search(source.read_text(encoding="utf-8"))
    ]

    assert fautifs == []


@pytest.mark.parametrize("blanche", BLANCHES.values(), ids=BLANCHES)
def test_un_dsn_sentry_blanc_vaut_sentry_desactive(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, blanche: str
) -> None:
    """`SENTRY_DSN=` dans un `.env` doit désactiver Sentry, pas le configurer avec une chaîne vide.

    Mesuré au triage : sans validateur, pydantic rend `SecretStr('')` — une valeur *présente* et
    fausse. La branche « désactivé » ne se déclencherait alors jamais, ni avec le `.env.example`,
    ni en CI, et `sentry_sdk.init` recevrait un DSN vide.

    C'est aussi pourquoi ce champ **n'utilise pas l'alias `Secret`** : cet alias refuse le blanc,
    là où « vide » est ici un état légitime que l'exploitant choisit.
    """
    monkeypatch.setenv("SENTRY_DSN", blanche)

    assert Settings().sentry_dsn is None


def test_un_dsn_sentry_absent_vaut_sentry_desactive(environnement_complet: None) -> None:
    assert Settings().sentry_dsn is None


def test_un_dsn_sentry_pose_est_lu_et_masque(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Présent, il se lit — et reste un secret : c'est une URL qui porte une clé de projet."""
    dsn = "https://cle-de-projet@o0.ingest.sentry.io/1"
    monkeypatch.setenv("SENTRY_DSN", dsn)

    reglages = Settings()

    assert reglages.sentry_dsn is not None
    assert reglages.sentry_dsn.get_secret_value() == dsn
    assert dsn not in repr(reglages)


@pytest.mark.parametrize("hors_bornes", ["0", "0.0", "1.5", "-0.1"])
def test_un_taux_d_echantillonnage_hors_bornes_empeche_le_demarrage(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, hors_bornes: str
) -> None:
    """Le taux vit dans `]0, 1]` — les deux bouts comptent, pour des raisons opposées.

    Zéro ne veut pas dire « moins d'événements » : il veut dire « aucun », donc un Sentry
    configuré, facturé, et muet. Au-dessus de 1, la valeur n'a pas de sens et le SDK la
    tronquerait en silence, ce qui ferait croire à un réglage appliqué.
    """
    monkeypatch.setenv("SENTRY_SAMPLE_RATE", hors_bornes)

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize("valide", ["0.01", "0.5", "1", "1.0"])
def test_un_taux_d_echantillonnage_dans_les_bornes_est_accepte(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, valide: str
) -> None:
    monkeypatch.setenv("SENTRY_SAMPLE_RATE", valide)

    assert Settings().sentry_sample_rate == float(valide)
