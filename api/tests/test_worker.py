"""Le worker : ce qu'il déroule, et comment il s'arrête."""

import asyncio
import os
from pathlib import Path
from typing import cast

import pytest
from conftest import MoteurEspion

from arpendo_api import worker
from arpendo_api.core.resources import Resources
from arpendo_api.worker import TASKS, run

RESSOURCES_INUTILISEES = cast(Resources, None)
"""Ce que reçoit une tâche qui n'a besoin de rien.

Le battement n'écrit qu'un fichier : lui ouvrir un moteur et un client Valkey pour l'éprouver
donnerait à croire qu'il en dépend.
"""

DELAI = 5.0
"""Secondes accordées à un `run` qu'on attend arrêté.

Un worker qui ne s'arrête pas attendrait indéfiniment, et une suite qui pend ne dit pas ce qui
manque. Très au-dessus du coût réel d'un tour de boucle sur des intervalles de test.
"""


async def test_run_deroule_la_table_et_passe_les_ressources_a_chaque_tache() -> None:
    """Une tâche reçoit de quoi travailler — les mêmes ressources que l'api, ouvertes par `run`.

    Elle pose elle-même l'événement d'arrêt : c'est le seul moyen d'observer *un* tour de boucle
    sans temporisation, et donc sans dépendre de la vitesse de la machine.
    """
    arret = asyncio.Event()
    recues: list[Resources] = []

    async def compter(ressources: Resources) -> None:
        recues.append(ressources)
        arret.set()

    async with asyncio.timeout(DELAI):
        await run({"compter": (0.01, compter)}, arret)

    assert len(recues) == 1
    assert await recues[0].valkey.ping() is True


async def test_run_libere_les_ressources_quand_il_s_arrete(moteur_espion: MoteurEspion) -> None:
    """Un worker qui s'arrête sans rendre ses connexions les laisserait ouvertes côté serveur.

    La libération ne se voit pas de l'extérieur — `AsyncEngine.dispose` ne laisse aucune trace —
    d'où la doublure, qui est celle du démarrage de l'api : les deux hôtes ouvrent et libèrent par
    le même chemin, donc le même espion les observe.
    """
    arret = asyncio.Event()
    arret.set()

    async with asyncio.timeout(DELAI):
        await run({}, arret)

    assert moteur_espion.libere


async def test_le_battement_cree_le_fichier_puis_en_rafraichit_la_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Le healthcheck du conteneur ne lit rien d'autre que l'âge de ce fichier.

    Les deux moitiés comptent : le créer prouve que le worker a démarré, en **rafraîchir la date**
    prouve qu'il tourne encore. Un battement qui ne ferait que créer laisserait un conteneur mort
    passer pour vivant jusqu'à ce que quelqu'un regarde.

    La date est reculée à la main plutôt qu'attendue : deux `touch` consécutifs peuvent tomber dans
    la même graduation d'horloge, et le test deviendrait alors une loterie.
    """
    fichier = tmp_path / "battement"
    monkeypatch.setattr(worker, "HEARTBEAT", fichier)
    _, battre = TASKS["battement"]

    await battre(RESSOURCES_INUTILISEES)
    assert fichier.exists()

    os.utime(fichier, (0, 0))
    await battre(RESSOURCES_INUTILISEES)

    assert fichier.stat().st_mtime > 0
