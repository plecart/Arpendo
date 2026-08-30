"""Le bus d'événements : ce qui est écrit avant d'être publié, et ce qui n'est jamais publié."""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import ClassVar

import pytest
import uuid6
from conftest import Capture, evenements_persistes, fabrique_de
from fastapi import FastAPI
from pydantic import BaseModel
from redis.exceptions import RedisError

from arpendo_api.core.bus import channel_for, publish, subscribe
from arpendo_api.core.journal import Event

DELAI_DE_RECEPTION = 5.0
"""Secondes accordées à l'arrivée d'un message attendu.

Un abonné qui n'entend rien attendrait sinon indéfiniment : `get_message(timeout=None)` bloque, et
une suite qui pend ne dit pas ce qui manque. Très au-dessus du coût réel d'un aller-retour sur la
boucle locale — le dépasser signifie que le message n'est jamais parti.
"""


class Usurpateur(BaseModel):
    """Un modèle étranger qui *déclare* l'identifiant d'un type inscrit, sans en être une instance.

    C'est le seul objet qui distingue « l'identifiant est connu » de « cette classe est celle qui
    l'a inscrit » : une vérification qui se contenterait de la présence de la clé au registre
    l'accepterait, et publierait une charge utile qu'aucun abonné ne saurait décoder.
    """

    type: ClassVar[str] = Capture.type


@pytest.mark.parametrize(
    "intrus",
    [Event(), {"type": Capture.type}, Usurpateur()],
    ids=["base-nue", "dict", "modele-etranger"],
)
async def test_publier_un_objet_non_inscrit_leve_avant_toute_ecriture(
    app: FastAPI, partie: uuid.UUID, intrus: object
) -> None:
    """Le refus précède l'écriture : un lot dont un seul élément est invalide n'écrit rien.

    Refuser *après* le premier `add` laisserait une unité de travail à moitié montée — exactement
    l'état partiel que le commit explicite existe pour éviter.

    C'est `session.new` qui le prouve, et pas la base : à la sortie de la session, ce qui n'a pas
    été commis est annulé de toute façon, donc une base vide ne distingue pas « refusé avant
    l'écriture » de « refusé après ». Mesuré — sans cette assertion, une implémentation qui ajoute
    les lignes valides puis lève reste verte.
    """
    async with fabrique_de(app)() as session:
        with pytest.raises(TypeError):
            await publish(session, app.state.valkey, Capture(game_id=partie, hexagones=3), intrus)

        assert not session.new

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


async def test_un_abonne_recoit_le_lot_dans_l_ordre_de_l_appel(
    app: FastAPI, partie: uuid.UUID, journal_nettoye: None
) -> None:
    """Ce que reçoit l'abonné est typé, ordonné, et porte l'`id` de la ligne commise.

    L'abonnement est ouvert **avant** la publication : c'est la seule façon de prouver que les
    messages ont traversé le serveur, et pas qu'ils étaient déjà là.
    """
    async with subscribe(app.state.valkey, partie) as flux:
        async with fabrique_de(app)() as session:
            await publish(
                session,
                app.state.valkey,
                Capture(game_id=partie, hexagones=1),
                Capture(game_id=partie, hexagones=2),
            )

        async with asyncio.timeout(DELAI_DE_RECEPTION):
            recus = [await anext(flux), await anext(flux)]

    assert [type(recu) for recu in recus] == [Capture, Capture]
    assert [recu.hexagones for recu in recus] == [1, 2]
    assert [recu.id for recu in recus] == [
        ligne.id for ligne in await evenements_persistes(app, partie)
    ]


async def test_un_evenement_sans_partie_est_journalise_mais_jamais_publie(
    app: FastAPI, partie: uuid.UUID, journal_nettoye: None
) -> None:
    """Sans partie, pas de canal : l'événement entre au journal et s'arrête là.

    L'espion écoute **les deux** canaux : celui de la partie, et `game:None` — celui qu'une
    implémentation qui publierait sans regarder `game_id` emploierait. Écouter la seule partie
    rendrait ce test vert sans rien prouver : le message parti au mauvais endroit serait simplement
    invisible. Un témoin publié juste après borne l'attente sans temporisation : si l'orphelin
    était parti, c'est lui qui arriverait en premier.
    """
    orphelin = Capture(hexagones=0)
    temoin = Capture(game_id=partie, hexagones=1)

    async with app.state.valkey.pubsub() as espion:
        await espion.subscribe(channel_for(partie), "game:None")
        for _ in range(2):
            await espion.get_message(timeout=None)

        async with fabrique_de(app)() as session:
            await publish(session, app.state.valkey, orphelin, temoin)

        async with asyncio.timeout(DELAI_DE_RECEPTION):
            message = await espion.get_message(ignore_subscribe_messages=True, timeout=None)

    assert orphelin.id is not None and orphelin.occurred_at is not None
    assert message["channel"].decode() == channel_for(partie)
    assert json.loads(message["data"])["payload"] == {"hexagones": 1}


async def test_un_message_d_un_type_inconnu_est_saute_sans_lever(
    app: FastAPI, partie: uuid.UUID, journal_nettoye: None
) -> None:
    """Un producteur plus récent peut publier un type que ce processus ne connaît pas encore.

    Lever ferait perdre à l'abonné tous les messages suivants — y compris ceux qu'il sait lire. Le
    témoin publié ensuite prouve que le fil a survécu à l'inconnu.
    """
    inconnu = json.dumps(
        {
            "id": str(uuid6.uuid7()),
            "game_id": str(partie),
            "type": "test.type-qu-aucune-classe-ne-declare",
            "payload": {"peu": "importe"},
            "occurred_at": datetime.now(UTC).isoformat(),
        }
    )
    temoin = Capture(game_id=partie, hexagones=1)

    async with subscribe(app.state.valkey, partie) as flux:
        await app.state.valkey.publish(channel_for(partie), inconnu)
        async with fabrique_de(app)() as session:
            await publish(session, app.state.valkey, temoin)

        async with asyncio.timeout(DELAI_DE_RECEPTION):
            recu = await anext(flux)

    assert recu.id == temoin.id


@pytest.mark.parametrize("settings", [{"valkey_url": "redis://127.0.0.1:1/0"}], indirect=True)
async def test_l_abonnement_leve_a_l_entree_si_valkey_est_injoignable(app: FastAPI) -> None:
    """Aucune reconnexion maison : la perte se constate, elle ne s'attend pas (cadrage §13.8).

    Le port 1 n'écoute pas. C'est **l'entrée du contexte** qui lève, pas la première lecture : le
    `SUBSCRIBE` a besoin d'une connexion, et l'appelant apprend donc l'absence du serveur avant
    d'avoir un flux entre les mains. Le `pytest.fail` est ce qui rend le test précis : atteindre le
    corps du contexte échouerait, au lieu de passer pour un succès.

    `RedisError` et non sa sous-classe exacte : **la classe dépend de la plateforme** — mesuré, un
    port fermé donne un refus (`ConnectionError`) là où la pile réseau répond, et une expiration
    (`TimeoutError`) là où elle laisse tomber le paquet, ce qui est le cas sur ce poste. Le client
    ne réessaie jamais — c'est `core.valkey` qui le règle, et son propre test tient cette propriété.
    """
    async with asyncio.timeout(DELAI_DE_RECEPTION):
        with pytest.raises(RedisError):
            async with subscribe(app.state.valkey, uuid.uuid4()):
                pytest.fail("l'abonnement aurait dû lever avant de rendre le flux")


async def test_l_abonnement_est_enregistre_a_l_entree_et_defait_a_la_sortie(
    app: FastAPI, partie: uuid.UUID
) -> None:
    """Les deux bouts du contexte, vus **depuis le serveur** et non depuis l'objet client.

    À l'entrée, `PUBSUB NUMSUB` à 1 prouve que le serveur a traité l'abonnement — c'est ce que
    l'attente de la confirmation garantit, et sans elle un message publié dans la foulée se perd.
    À la sortie, 0 prouve que le `PubSub` a bien été fermé et sa connexion rendue.

    **La première moitié est probabiliste, et il vaut mieux le savoir que le croire déterministe.**
    Mesuré en relecture indépendante : en retirant l'attente de la confirmation, `NUMSUB` vaut
    quand même 1 douze fois sur trente — le serveur a souvent traité le `SUBSCRIBE` avant qu'on
    l'interroge. Ce test rougirait donc dans deux tiers des exécutions, pas dans toutes. C'est le
    seul garde-fou de cette ligne ; le rendre déterministe demanderait de suspendre le serveur
    entre les deux ordres, ce que rien ici ne permet.
    """
    canal = channel_for(partie)

    async with subscribe(app.state.valkey, partie):
        assert await app.state.valkey.pubsub_numsub(canal) == [(canal.encode(), 1)]

    assert await app.state.valkey.pubsub_numsub(canal) == [(canal.encode(), 0)]
