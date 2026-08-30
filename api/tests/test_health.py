import time

import pytest
from conftest import VALKEY_SUR_UN_PORT_FERME
from fastapi import Request
from httpx import AsyncClient

from arpendo_api.core import health, valkey


async def test_health_repond_200_quand_les_deux_dependances_repondent(
    client: AsyncClient,
) -> None:
    reponse = await client.get("/health")

    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok", "postgres": "ok", "valkey": "ok"}


@pytest.mark.parametrize("settings", [VALKEY_SUR_UN_PORT_FERME], indirect=True)
async def test_health_repond_503_et_nomme_la_dependance_injoignable(
    client: AsyncClient,
) -> None:
    reponse = await client.get("/health")

    assert reponse.status_code == 503
    assert reponse.json() == {
        "status": "degraded",
        "postgres": "ok",
        "valkey": "unreachable",
    }


def test_le_budget_de_la_sonde_domine_le_delai_de_chaque_client() -> None:
    """Le filet de la sonde reste au-dessus du délai que chaque client s'accorde.

    C'est cette relation qui fait qu'une dépendance absente se constate par l'échec du client
    plutôt que par l'expiration de la sonde — laquelle masquerait la différence entre
    « injoignable » et « très lent », et ferait payer une seconde entière à tout moniteur
    d'uptime.

    Une relation entre deux constantes s'affirme sur les constantes. La déduire d'un chronomètre
    la rendait tributaire de la façon dont le système traite un port fermé : refus immédiat sur
    un runner Linux, silence jusqu'à l'expiration sur un poste dont le pare-feu filtre la boucle
    locale — deux mesures incomparables pour une même vérité.
    """
    assert valkey.CONNECT_TIMEOUT < health.PROBE_TIMEOUT


@pytest.mark.parametrize("settings", [VALKEY_SUR_UN_PORT_FERME], indirect=True)
async def test_health_ne_pend_pas_quand_une_dependance_manque(client: AsyncClient) -> None:
    """Une dépendance absente doit se constater, pas s'attendre.

    La requête traverse deux clients Valkey — celui du limiteur de débit, puis celui de la sonde
    — et chacun est borné par son propre délai : le plafond est leur somme. Le dépasser voudrait
    dire que l'un des deux réessaie, ce que `create_valkey` interdit ; redis-py, laissé à ses
    réglages, réessaierait trois fois avec un délai croissant, soit près de deux secondes.
    """
    debut = time.perf_counter()
    await client.get("/health")
    duree = time.perf_counter() - debut

    assert duree < valkey.CONNECT_TIMEOUT + health.PROBE_TIMEOUT


async def test_une_sonde_ajoutee_a_la_table_apparait_dans_la_reponse(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ajouter une dépendance, c'est ajouter une entrée — et ne toucher à rien d'autre.

    Ni la route, ni le calcul du verdict, ni le code de statut, ni le format de la réponse ne
    connaissent le nombre de dépendances.
    """

    async def sonde_toujours_joignable(_request: Request) -> None:
        """Une dépendance imaginaire, que rien ne peut rendre injoignable."""

    monkeypatch.setitem(health.PROBES, "inventee", sonde_toujours_joignable)

    reponse = await client.get("/health")

    assert reponse.json()["inventee"] == "ok"
