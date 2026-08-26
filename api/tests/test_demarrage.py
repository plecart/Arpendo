from fastapi import FastAPI
from sqlalchemy import text

from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app


async def test_le_demarrage_ouvre_une_connexion_utilisable_a_postgresql(app: FastAPI) -> None:
    async with app.state.engine.connect() as connexion:
        assert await connexion.scalar(text("SELECT 1")) == 1


async def test_le_demarrage_ouvre_une_connexion_utilisable_a_valkey(app: FastAPI) -> None:
    assert await app.state.valkey.ping() is True


def test_l_application_construite_sans_reglages_lit_l_environnement(settings: Settings) -> None:
    assert create_app().state.settings == settings
