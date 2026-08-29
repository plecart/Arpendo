"""La session async par requête : ce qu'elle écrit, et ce qu'elle refuse d'écrire toute seule."""

import uuid
from typing import Any

from conftest import evenements_persistes
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select

from arpendo_api.core.journal import DomainEvent
from arpendo_api.db.session import Session

CHARGE = {"joueur": "bleu", "hexagones": 3}


def route_qui_ecrit(app: FastAPI, partie: uuid.UUID, *, commit: bool) -> str:
    """Greffe sur l'application une route qui écrit un événement, et rend son chemin.

    Passer par une vraie route est le seul moyen de prouver l'**injection** : appeler la
    dépendance à la main prouverait la fonction, pas le câblage de FastAPI.

    La greffe se fait sur une application dont le cycle de vie tourne déjà (fixture `app`) :
    Starlette parcourt `router.routes` à chaque requête, donc une route ajoutée après coup est
    servie. C'est une propriété d'implémentation stable, pas un contrat documenté — vrai pour
    une application de test jetable, à ne pas transposer en production.

    La relecture se fait **par colonnes** et non par `session.get()` : `get()` rendrait l'objet
    déjà présent dans l'identity map, sans émettre le moindre SELECT, et le test comparerait le
    `payload` à lui-même. Lire les colonnes force l'aller-retour et rend les valeurs telles que
    PostgreSQL les a stockées.

    Args:
        app: l'application de test, jetable — on peut lui ajouter une route.
        partie: la partie à inscrire sur l'événement.
        commit: si l'appelant commet lui-même. C'est tout l'enjeu : la dépendance, elle, ne
            commet jamais.

    Returns:
        Le chemin de la route greffée.
    """
    chemin = f"/_test/ecrit-{'commit' if commit else 'sans-commit'}"

    @app.post(chemin)
    async def _ecrire(session: Session) -> dict[str, Any]:
        evenement = DomainEvent(game_id=partie, type="capture", payload=dict(CHARGE))
        session.add(evenement)
        await session.flush()
        payload, occurred_at = (
            await session.execute(
                select(DomainEvent.payload, DomainEvent.occurred_at).where(
                    DomainEvent.id == evenement.id
                )
            )
        ).one()
        if commit:
            await session.commit()
        return {
            "id": str(evenement.id),
            "fuseau": occurred_at.tzinfo is not None,
            "payload": payload,
        }

    return chemin


async def test_la_session_injectee_ecrit_et_relit_un_evenement(
    app: FastAPI, client: AsyncClient, partie: uuid.UUID
) -> None:
    """L'aller-retour complet : l'INSERT atteint PostgreSQL, la relecture rend ses valeurs."""
    reponse = await client.post(route_qui_ecrit(app, partie, commit=False))

    assert reponse.status_code == 200
    corps = reponse.json()
    assert uuid.UUID(corps["id"]).version == 7
    assert corps["fuseau"] is True
    assert corps["payload"] == CHARGE


async def test_la_dependance_ne_commet_jamais_a_la_sortie(
    app: FastAPI, client: AsyncClient, partie: uuid.UUID
) -> None:
    """Sans commit de l'appelant, la requête ne laisse rien : la fermeture annule le reste.

    Les deux premières assertions ne sont pas décoratives : sans elles, une route qui n'écrirait
    rien du tout — dépendance débranchée, chemin faux, erreur avant l'INSERT — laisserait la
    base vide et rendrait ce test vert sans qu'aucun rollback ait eu lieu.
    """
    reponse = await client.post(route_qui_ecrit(app, partie, commit=False))

    assert reponse.status_code == 200
    assert uuid.UUID(reponse.json()["id"]).version == 7

    assert await evenements_persistes(app, partie) == []


async def test_le_commit_de_l_appelant_persiste(
    app: FastAPI, client: AsyncClient, partie: uuid.UUID, journal_nettoye: None
) -> None:
    reponse = await client.post(route_qui_ecrit(app, partie, commit=True))

    (persiste,) = await evenements_persistes(app, partie)
    assert str(persiste.id) == reponse.json()["id"]
    assert persiste.payload == CHARGE
    assert persiste.game_id == partie
