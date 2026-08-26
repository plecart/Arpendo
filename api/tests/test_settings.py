import pytest
from pydantic import ValidationError

from arpendo_api.core.settings import Settings

REQUISES = {
    "DATABASE_URL": "postgresql+asyncpg://arpendo:arpendo@localhost:5432/arpendo",
    "VALKEY_URL": "redis://localhost:6379/0",
    "VALKEY_PASSWORD": "mot-de-passe",
}


@pytest.fixture
def environnement_complet(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isole les tests du `.env` du poste : seules les variables posées ici existent."""
    for nom in REQUISES:
        monkeypatch.delenv(nom, raising=False)
    for nom, valeur in REQUISES.items():
        monkeypatch.setenv(nom, valeur)


def test_les_reglages_lisent_les_variables_de_l_environnement(
    environnement_complet: None,
) -> None:
    reglages = Settings()

    assert reglages.database_url == REQUISES["DATABASE_URL"]
    assert reglages.valkey_url == REQUISES["VALKEY_URL"]
    assert reglages.valkey_password == REQUISES["VALKEY_PASSWORD"]


@pytest.mark.parametrize("manquante", sorted(REQUISES))
def test_une_variable_requise_absente_empeche_le_demarrage(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, manquante: str
) -> None:
    monkeypatch.delenv(manquante)

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize("videe", sorted(REQUISES))
def test_une_variable_requise_vide_empeche_le_demarrage(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, videe: str
) -> None:
    monkeypatch.setenv(videe, "")

    with pytest.raises(ValidationError):
        Settings()
