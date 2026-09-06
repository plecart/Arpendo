"""L'identifiant de requête : généré par le serveur, porté par la réponse et par chaque ligne."""

import uuid
from collections.abc import AsyncIterator
from typing import NoReturn

import pytest
import structlog
from conftest import Lignes
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.types import Receive, Scope, Send

from arpendo_api.core.logs import configure_logging
from arpendo_api.core.request_id import HEADER, RequestIdMiddleware

MESSAGE = "pendant la requête"
"""Ce que la route de test journalise — le repère qu'on va chercher dans la sortie."""

APRES = "après la requête"
"""Le repère de la ligne émise hors de toute requête.

Les deux repères servent à **filtrer** : le client HTTP journalise lui aussi chacun de ses appels,
et un test qui prendrait « la seule ligne » émise attraperait la sienne un jour sur deux.
"""


async def _sans_message(*_: object) -> NoReturn:
    """Un `receive` / `send` qui refuse de servir, pour un scope qui n'échange aucun message.

    Le cycle de vie éprouvé plus bas ne lit ni n'écrit : lui monter de vrais canaux décrirait un
    protocole que le test ne regarde pas. `NoReturn` tient les deux rôles à la fois — un canal qui
    ne rend jamais est compatible avec tout type de retour — et lever fait du « aucun message »
    une assertion plutôt qu'une promesse.
    """
    raise AssertionError("le cycle de vie n'échange aucun message")


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Une application minimale : le middleware, et une route qui journalise.

    Elle n'ouvre ni base ni cache — ce qu'on éprouve ici est une propriété de la couche ASGI, et
    la brancher sur les ressources partagées ne ferait qu'ajouter des raisons d'échouer.

    Elle n'appelle pas non plus `configure_logging()` : c'est au test de le faire, pour la raison
    que documente la fixture `lignes` — un handler construit en phase de préparation écrit dans un
    tampon que pytest a déjà remplacé quand le test s'exécute.
    """
    application = FastAPI()
    application.add_middleware(RequestIdMiddleware)

    @application.get("/essai")
    async def essai() -> dict[str, str]:
        structlog.get_logger("arpendo_api.essai").info(MESSAGE)
        return {"statut": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://test"
    ) as client:
        yield client


async def test_chaque_reponse_porte_un_identifiant_de_requete_neuf(client: AsyncClient) -> None:
    premiere = await client.get("/essai")
    seconde = await client.get("/essai")

    assert uuid.UUID(premiere.headers[HEADER]).version == 4
    assert premiere.headers[HEADER] != seconde.headers[HEADER]


async def test_un_identifiant_fourni_par_l_appelant_n_est_jamais_repris(
    client: AsyncClient,
) -> None:
    """Un en-tête entrant est une **entrée non fiable**, et les journaux sont un lieu de confiance.

    Le reprendre laisserait un appelant choisir la clé sur laquelle ses requêtes sont regroupées :
    il pourrait se confondre avec un autre, ou injecter dans l'agrégateur une valeur de son choix
    — un saut de ligne suffit à y fabriquer une fausse entrée.
    """
    reponse = await client.get("/essai", headers={HEADER: "identifiant-choisi-par-l-appelant"})

    assert reponse.headers[HEADER] != "identifiant-choisi-par-l-appelant"


async def test_les_lignes_emises_pendant_la_requete_portent_l_identifiant_de_la_reponse(
    client: AsyncClient, lignes: Lignes
) -> None:
    """C'est la seule raison d'être de l'identifiant : relier une réponse à ce qu'elle a produit.

    Sans ce lien, une erreur remontée par un joueur ne se retrouve dans l'agrégateur qu'à
    l'horodatage — donc au milieu de tout ce que les autres joueurs faisaient à la même seconde.
    """
    configure_logging()

    reponse = await client.get("/essai")

    (ligne,) = [ligne for ligne in lignes() if ligne["event"] == MESSAGE]
    assert ligne["request_id"] == reponse.headers[HEADER]


async def test_aucun_identifiant_ne_survit_a_la_requete(
    client: AsyncClient, lignes: Lignes
) -> None:
    """Le contexte est lié à un fil d'exécution, pas à une requête : c'est au code de le défaire.

    Une ligne du worker ou d'une tâche de fond qui hériterait de l'identifiant d'une requête
    terminée est pire qu'une ligne sans identifiant : elle rattache un travail à une requête qui
    ne l'a pas demandé.
    """
    configure_logging()
    await client.get("/essai")
    lignes()

    structlog.get_logger("arpendo_api.essai").info(APRES)

    (ligne,) = [ligne for ligne in lignes() if ligne["event"] == APRES]
    assert "request_id" not in ligne


async def test_un_contexte_englobant_est_restaure_apres_la_requete(
    client: AsyncClient, lignes: Lignes
) -> None:
    """Ce qui était lié avant la requête doit l'être encore après.

    Le middleware **restaure**, il ne supprime pas : un `unbind` ferait disparaître la valeur qu'un
    contexte englobant avait posée. Rien ne lie `request_id` en amont aujourd'hui — c'est
    précisément pourquoi ce test existe : sans lui, la différence entre supprimer et restaurer
    serait invisible jusqu'au jour où elle coûterait cher.
    """
    configure_logging()
    structlog.contextvars.bind_contextvars(request_id="posé-par-un-contexte-englobant")

    await client.get("/essai")
    lignes()

    structlog.get_logger("arpendo_api.essai").info(APRES)

    (ligne,) = [ligne for ligne in lignes() if ligne["event"] == APRES]
    assert ligne["request_id"] == "posé-par-un-contexte-englobant"


async def test_le_cycle_de_vie_traverse_le_middleware_sans_identifiant(lignes: Lignes) -> None:
    """Le `lifespan` parcourt la pile de middlewares comme une requête, sans en être une.

    Il n'a ni réponse à enrichir ni contexte à porter, et le traiter comme une requête lui
    fabriquerait un identifiant que rien ne lirait — et poserait l'en-tête sur un message qui n'en
    a pas. La garde s'éprouve en appelant le middleware **directement** : un transport de test
    n'ouvre pas le cycle de vie, et la fixture `app` du conftest y entre en court-circuitant la
    pile de middlewares.
    """
    configure_logging()
    traverses: list[str] = []

    async def application(scope: Scope, receive: Receive, send: Send) -> None:
        traverses.append(scope["type"])
        structlog.get_logger("arpendo_api.essai").info(APRES)

    await RequestIdMiddleware(application)({"type": "lifespan"}, _sans_message, _sans_message)

    assert traverses == ["lifespan"]
    (ligne,) = [ligne for ligne in lignes() if ligne["event"] == APRES]
    assert "request_id" not in ligne
