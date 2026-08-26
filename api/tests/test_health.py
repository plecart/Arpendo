from httpx import AsyncClient


async def test_health_repond_200_avec_un_corps_json(client: AsyncClient) -> None:
    reponse = await client.get("/health")

    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok"}
