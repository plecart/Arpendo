import time

import pytest
from httpx import AsyncClient

from arpendo_api.core.health import PROBE_TIMEOUT

VALKEY_SUR_UN_PORT_FERME = {"valkey_url": "redis://127.0.0.1:1/0"}


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


@pytest.mark.parametrize("settings", [VALKEY_SUR_UN_PORT_FERME], indirect=True)
async def test_health_conclut_par_refus_et_non_par_expiration(client: AsyncClient) -> None:
    """Une dépendance absente doit se constater, pas s'attendre.

    Le budget de la sonde est un filet, pas un délai de fonctionnement normal : l'atteindre à
    chaque interrogation ferait payer une seconde à tout moniteur d'uptime, et masquerait la
    différence entre « injoignable » et « très lent ».
    """
    debut = time.perf_counter()
    await client.get("/health")
    duree = time.perf_counter() - debut

    assert duree < PROBE_TIMEOUT
