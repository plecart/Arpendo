"""La libération d'un verrou ne retire que le nôtre.

Le reste de `magasins` se garde par la configuration (`test_isolation`) et par le protocole manuel
de #94. Cet invariant-ci ne se lit ni dans l'un ni dans l'autre : il ne se voit que sous un écrivain
concurrent, qu'on ne rencontre jamais en lançant la suite seule.
"""

from collections.abc import AsyncIterator

import magasins
import pytest
from conftest import reglages_surcharges
from redis.asyncio import Redis

from arpendo_api.core.valkey import create_valkey

INDEX_HORS_JEU = 99
"""Un index qu'aucune suite ne réserve : `INDEX_CANDIDATS` s'arrête à 15.

Le verrou de ce test vit donc sur la base des verrous comme les autres, sans qu'une suite voisine
puisse jamais le convoiter — `_liberer` ne regarde que la clé qu'on lui nomme, l'index n'ayant pour
elle aucune autre signification.
"""

JETON_D_UNE_VOISINE = "jeton-d-une-autre-suite"


@pytest.fixture
async def verrous() -> AsyncIterator[Redis]:
    """Un client sur la base des **verrous** — celle de l'environnement, pas celle de la suite."""
    async with create_valkey(reglages_surcharges({"valkey_url": magasins.VALKEY_URL})) as client:
        yield client


async def test_la_liberation_laisse_le_verrou_d_une_voisine(verrous: Redis) -> None:
    """Une suite qui rend son index ne peut pas rendre celui d'une autre.

    Sans la comparaison atomique, la suppression emporterait ce verrou-ci : la voisine se croirait
    seule sur son index, une troisième suite le réserverait, le viderait, et les deux écriraient
    dedans — le défaut même de #94, réintroduit par son correctif.
    """
    cle = magasins.CLE_DU_VERROU.format(index=INDEX_HORS_JEU)
    await verrous.set(cle, JETON_D_UNE_VOISINE, ex=60)

    try:
        await magasins._liberer(INDEX_HORS_JEU)

        assert await verrous.get(cle) == JETON_D_UNE_VOISINE.encode(), (
            "la libération a emporté le verrou d'une autre suite : elle ne compare pas le jeton, "
            "ou le compare sans atomicité"
        )
    finally:
        await verrous.delete(cle)


async def test_la_liberation_retire_notre_propre_verrou(verrous: Redis) -> None:
    """Et elle le retire vraiment — sinon l'index sortirait du jeu jusqu'à l'échéance du bail.

    Le pendant obligatoire du test précédent : une libération qui ne supprimerait jamais rien le
    satisferait aussi.
    """
    cle = magasins.CLE_DU_VERROU.format(index=INDEX_HORS_JEU)
    await verrous.set(cle, magasins.JETON_DE_LA_SUITE, ex=60)

    await magasins._liberer(INDEX_HORS_JEU)

    assert await verrous.get(cle) is None, "notre propre verrou survit à sa libération"
