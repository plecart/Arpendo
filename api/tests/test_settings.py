from collections.abc import Callable

import pytest
from conftest import reglages_surcharges
from pydantic import SecretStr, ValidationError

from arpendo_api.core.settings import Settings

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
}


@pytest.fixture
def environnement_complet(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isole les tests du `.env` du poste : seules les variables posées ici existent."""
    for nom in REQUISES:
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
