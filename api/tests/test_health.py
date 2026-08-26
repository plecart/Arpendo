import pytest
from httpx import AsyncClient

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
