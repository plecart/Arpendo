"""Le worker : second point d'entrée du paquet, et la boucle qui déroule ses tâches périodiques.

Même paquet que l'api, même couche de services, même image — commande différente et conteneur
distinct (cadrage §13.0). Il ne fusionne jamais avec l'api : les tâches planifiées ne doivent
s'exécuter qu'une fois, quel que soit le nombre d'instances HTTP (§13.9 règle 2).
"""

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from contextlib import suppress
from pathlib import Path

from arpendo_api.core.resources import Resources, open_resources
from arpendo_api.core.settings import Settings

Task = Callable[[Resources], Awaitable[None]]
"""Un tour de travail périodique, à partir des ressources partagées du processus.

Elle ne rend rien : seul compte qu'elle aboutisse. Elle reçoit les ressources plutôt que de les
ouvrir, pour que toutes les tâches partagent un seul moteur et un seul client.
"""


HEARTBEAT = Path("/tmp/arpendo-worker-battement")
"""Le fichier dont la fraîcheur dit que le worker tourne encore.

Sous ``/tmp`` : c'est le seul chemin qui reste inscriptible quand #45 posera un système de fichiers
en lecture seule et un ``tmpfs``. Une clé Valkey ferait la même chose, mais la sonde du conteneur
devrait alors embarquer un client et un mot de passe pour la lire — là, un ``stat`` suffit.
"""

HEARTBEAT_INTERVAL = 10.0
"""Secondes entre deux battements.

Une constante, pas un réglage : #44 n'ajoute aucune variable d'environnement. La valeur suit
l'``interval`` du healthcheck de l'image api, pour qu'il n'y ait qu'une cadence à retenir dans le
compose — où elle est **recopiée**, Compose ne sachant pas lire une constante Python.
"""


async def _heartbeat(resources: Resources) -> None:
    """Repose la date du fichier de battement — la seule chose que la sonde du conteneur regarde.

    ``touch`` crée le fichier au premier tour et n'en rafraîchit que la date ensuite : rien n'est
    écrit dedans, il n'a pas de contenu, c'est sa **date** qui porte l'information.

    Args:
        resources: inutilisées. La signature est celle de toute tâche, pour que la table reste
            uniforme et qu'une tâche puisse gagner un accès à la base sans changer de forme.
    """
    HEARTBEAT.touch()


TASKS: Mapping[str, tuple[float, Task]] = {"battement": (HEARTBEAT_INTERVAL, _heartbeat)}
"""Les tâches périodiques du worker, sous le nom qui les désigne.

**Ajouter une tâche planifiée, c'est ajouter une entrée ici** (§13.9 règle 2) — ni la boucle, ni
l'ouverture des ressources, ni l'arrêt n'ont à changer. Une seule à la naissance : le battement.
Les tâches réelles — fin de partie, purges de rétention, bilans du flux, envoi des push — arrivent
avec les domaines Territoire et Flux.
"""


async def _repeat(interval: float, task: Task, resources: Resources, stop: asyncio.Event) -> None:
    """Exécute une tâche, attend son intervalle, recommence — jusqu'à l'événement d'arrêt.

    L'attente porte sur l'**événement**, pas sur le temps : un ``sleep`` obligerait l'arrêt à
    patienter jusqu'au prochain réveil, et un intervalle d'une heure rendrait un ``docker compose
    stop`` insupportable. Ici, poser l'événement interrompt l'attente immédiatement.

    La tâche s'exécute **avant** la première attente : un worker qui vient de démarrer a fait son
    premier tour tout de suite, ce dont le healthcheck du conteneur dépend.
    """
    while not stop.is_set():
        await task(resources)
        with suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), interval)


async def run(tasks: Mapping[str, tuple[float, Task]], stop: asyncio.Event) -> None:
    """Ouvre les ressources partagées, déroule la table de tâches, et libère tout à l'arrêt.

    Args:
        tasks: la table à dérouler — un nom, son intervalle en secondes, et la coroutine à
            exécuter. Chaque entrée tourne dans sa propre boucle : une tâche lente n'en retarde
            aucune autre.
        stop: l'événement qui met fin à toutes les boucles. C'est l'appelant qui le pose — depuis
            un signal en production, directement dans un test.

    Returns:
        Rien, et seulement une fois **toutes** les boucles terminées et les ressources libérées.
    """
    async with open_resources(Settings()) as resources:
        await asyncio.gather(
            *(_repeat(interval, task, resources, stop) for interval, task in tasks.values())
        )
