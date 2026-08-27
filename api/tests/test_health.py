import time

import pytest
from fastapi import Request
from httpx import AsyncClient

from arpendo_api.core import health

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

    assert duree < health.PROBE_TIMEOUT


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
