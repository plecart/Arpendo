import pytest
from fastapi import FastAPI
from sqlalchemy import text

from arpendo_api.core import resources
from arpendo_api.core.resources import open_resources
from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app


async def test_les_ressources_s_ouvrent_sans_application(settings: Settings) -> None:
    """Le worker n'a pas d'application : il ouvre les mêmes ressources, par le même chemin.

    C'est tout l'objet de l'extraction — sans elle, ce bloc ne serait atteignable qu'à travers
    FastAPI, et le second point d'entrée du paquet devrait le réécrire. Les trois sont utilisables,
    pas seulement construites : c'est un aller-retour qui le prouve, pas un `is not None`.
    """
    async with open_resources(settings) as ressources:
        async with ressources.engine.connect() as connexion:
            assert await connexion.scalar(text("SELECT 1")) == 1
        async with ressources.sessionmaker() as session:
            assert await session.scalar(text("SELECT 1")) == 1
        assert await ressources.valkey.ping() is True


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
    """Substitue au moteur une doublure qui note sa libération.

    La substitution vise ``core.resources``, où les fabriques sont désormais appelées : c'est le
    module qui ouvre les ressources, quel que soit l'hôte qui les consomme.
    """
    moteur = MoteurEspion()
    monkeypatch.setattr(resources, "create_engine", lambda _: moteur)
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
    monkeypatch.setattr(resources, "create_valkey", lambda _: ClientRecalcitrant())

    await _demarrage_echoue(settings, RuntimeError)

    assert moteur_espion.libere
