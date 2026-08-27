import pytest
from fastapi import FastAPI
from sqlalchemy import text

from arpendo_api import main
from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app


async def test_le_demarrage_ouvre_une_connexion_utilisable_a_postgresql(app: FastAPI) -> None:
    async with app.state.engine.connect() as connexion:
        assert await connexion.scalar(text("SELECT 1")) == 1


async def test_le_demarrage_ouvre_une_connexion_utilisable_a_valkey(app: FastAPI) -> None:
    assert await app.state.valkey.ping() is True


def test_l_application_construite_sans_reglages_lit_l_environnement(settings: Settings) -> None:
    assert create_app().state.settings == settings


class MoteurEspion:
    """Un moteur qui n'ouvre rien et note seulement qu'on l'a libéré.

    Doublure de notre propre fabrique, et non d'une frontière du système : c'est le seul moyen
    d'observer une libération, `AsyncEngine.dispose` ne laissant aucune trace visible.
    """

    def __init__(self) -> None:
        self.libere = False

    async def dispose(self) -> None:
        self.libere = True


class ClientRecalcitrant:
    """Un client Valkey qui refuse de se fermer."""

    async def aclose(self) -> None:
        raise RuntimeError("fermeture impossible")


@pytest.fixture
def moteur_espion(monkeypatch: pytest.MonkeyPatch) -> MoteurEspion:
    """Substitue au moteur une doublure qui note sa libération."""
    moteur = MoteurEspion()
    monkeypatch.setattr(main, "create_engine", lambda _: moteur)
    return moteur


async def _demarrage_echoue(settings: Settings, erreur: type[Exception]) -> None:
    """Traverse le cycle de vie d'une application neuve et exige qu'il échoue sur `erreur`."""
    application = create_app(settings)

    with pytest.raises(erreur):
        async with application.router.lifespan_context(application):
            pass


@pytest.mark.parametrize("settings", [{"valkey_url": "pas-une-url"}], indirect=True)
async def test_le_moteur_est_libere_si_le_client_valkey_ne_peut_naitre(
    settings: Settings, moteur_espion: MoteurEspion
) -> None:
    """Une URL Valkey au schéma inconnu fait échouer `Redis.from_url` — après la naissance du
    moteur, donc au pire moment : celui où une ressource est déjà ouverte et personne ne la
    réclamera jamais.
    """
    await _demarrage_echoue(settings, ValueError)

    assert moteur_espion.libere


async def test_le_moteur_est_libere_si_la_fermeture_du_client_valkey_leve(
    settings: Settings, moteur_espion: MoteurEspion, monkeypatch: pytest.MonkeyPatch
) -> None:
    """L'autre bout du même contrat : une fermeture qui lève n'emporte pas les suivantes."""
    monkeypatch.setattr(main, "create_valkey", lambda _: ClientRecalcitrant())

    await _demarrage_echoue(settings, RuntimeError)

    assert moteur_espion.libere
