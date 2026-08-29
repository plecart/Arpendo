"""La session async par requête : ce qu'elle écrit, et ce qu'elle refuse d'écrire toute seule."""

import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from arpendo_api.core.journal import DomainEvent
from arpendo_api.db.session import Session

PARTIE = uuid.uuid4()
CHARGE = {"joueur": "bleu", "hexagones": 3}


def route_qui_ecrit(app: FastAPI, *, commit: bool) -> str:
    """Greffe sur l'application une route qui écrit un événement, et rend son chemin.

    Passer par une vraie route est le seul moyen de prouver l'**injection** : appeler la
    dépendance à la main prouverait la fonction, pas le câblage de FastAPI.

    La greffe se fait sur une application dont le cycle de vie tourne déjà (fixture `app`) :
    FastAPI résout ses routes à chaque requête, pas une fois au démarrage, donc une route ajoutée
    après coup est servie normalement.

    Args:
        app: l'application de test, jetable — on peut lui ajouter une route.
        commit: si l'appelant commet lui-même. C'est tout l'enjeu : la dépendance, elle, ne
            commet jamais.

    Returns:
        Le chemin de la route greffée.
    """
    chemin = f"/_test/ecrit-{'commit' if commit else 'sans-commit'}"

    @app.post(chemin)
    async def _ecrire(session: Session) -> dict[str, Any]:
        evenement = DomainEvent(game_id=PARTIE, type="capture", payload=CHARGE)
        session.add(evenement)
        await session.flush()
        relu = await session.get(DomainEvent, evenement.id)
        assert relu is not None
        constats = {
            "id": str(relu.id),
            "version": relu.id.version,
            "fuseau": relu.occurred_at.tzinfo is not None,
            "payload": relu.payload,
        }
        if commit:
            await session.commit()
        return constats

    return chemin


async def evenements_persistes(app: FastAPI) -> list[DomainEvent]:
    """Ce que voit une session *neuve* — donc ce qui a réellement été commis."""
    fabrique: async_sessionmaker[AsyncSession] = app.state.sessionmaker
    async with fabrique() as session:
        resultat = await session.execute(select(DomainEvent).where(DomainEvent.game_id == PARTIE))
        return list(resultat.scalars())


async def test_la_session_injectee_ecrit_et_relit_un_evenement(
    app: FastAPI, client: AsyncClient
) -> None:
    reponse = await client.post(route_qui_ecrit(app, commit=False))

    assert reponse.status_code == 200
    corps = reponse.json()
    assert uuid.UUID(corps["id"]).version == 7
    assert corps["version"] == 7
    assert corps["fuseau"] is True
    assert corps["payload"] == CHARGE


async def test_la_dependance_ne_commet_jamais_a_la_sortie(
    app: FastAPI, client: AsyncClient
) -> None:
    """Sans commit de l'appelant, la requête ne laisse rien : la fermeture annule le reste."""
    await client.post(route_qui_ecrit(app, commit=False))

    assert await evenements_persistes(app) == []


@pytest.fixture
async def journal_nettoye(app: FastAPI) -> AsyncIterator[None]:
    """Retire ce que le test a délibérément commis — la base est partagée par toute la suite."""
    yield
    fabrique: async_sessionmaker[AsyncSession] = app.state.sessionmaker
    async with fabrique() as session:
        for evenement in await evenements_persistes(app):
            await session.delete(await session.merge(evenement))
        await session.commit()


async def test_le_commit_de_l_appelant_persiste(
    app: FastAPI, client: AsyncClient, journal_nettoye: None
) -> None:
    await client.post(route_qui_ecrit(app, commit=True))

    (persiste,) = await evenements_persistes(app)
    assert persiste.payload == CHARGE
    assert persiste.game_id == PARTIE
