"""Le bus d'événements : ce qui est écrit avant d'être publié, et ce qui n'est jamais publié."""

import uuid

import pytest
from conftest import Capture, evenements_persistes, fabrique_de
from fastapi import FastAPI

from arpendo_api.core.bus import publish
from arpendo_api.core.journal import Event


async def test_publier_un_objet_non_inscrit_leve_avant_toute_ecriture(
    app: FastAPI, partie: uuid.UUID
) -> None:
    """Le refus précède l'écriture : un lot dont un seul élément est invalide ne laisse rien.

    Refuser *après* le premier `add` publierait la moitié du lot — précisément l'état partiel que
    le commit explicite de la session existe pour éviter. La base nue `Event` est le cas le plus
    piégeux : c'est bien un modèle, il n'a simplement pas d'identifiant de type.
    """
    async with fabrique_de(app)() as session:
        with pytest.raises(TypeError):
            await publish(
                session,
                app.state.valkey,
                Capture(game_id=partie, hexagones=3),
                Event(game_id=partie),
            )

    assert await evenements_persistes(app, partie) == []


async def test_publier_commet_et_remplit_l_identifiant_et_l_horodatage(
    app: FastAPI, partie: uuid.UUID, journal_nettoye: None
) -> None:
    """Le journal fait foi : les deux champs viennent de la ligne commise, pas d'un calcul local.

    Une session *neuve* les relit, donc le commit a bien eu lieu — la dépendance de session ne
    commet jamais d'elle-même, et rien d'autre ici n'aurait pu le faire. L'`id` est l'UUIDv7 qui
    servira de `Last-Event-ID` à la SSE : sans lui sur l'instance, l'abonné le perdrait.
    """
    evenement = Capture(game_id=partie, hexagones=3)

    async with fabrique_de(app)() as session:
        await publish(session, app.state.valkey, evenement)

    (ligne,) = await evenements_persistes(app, partie)
    assert (ligne.type, ligne.payload, ligne.game_id) == ("test.captured", {"hexagones": 3}, partie)
    assert evenement.id == ligne.id
    assert evenement.id is not None and evenement.id.version == 7
    assert evenement.occurred_at == ligne.occurred_at
    assert evenement.occurred_at is not None and evenement.occurred_at.tzinfo is not None
