"""Le worker : second point d'entrée du paquet, et la boucle qui déroule ses tâches périodiques.

Même paquet que l'api, même couche de services, même image — commande différente et conteneur
distinct (cadrage §13.0). Il ne fusionne jamais avec l'api : les tâches planifiées ne doivent
s'exécuter qu'une fois, quel que soit le nombre d'instances HTTP (§13.9 règle 2).
"""

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from contextlib import suppress

from arpendo_api.core.resources import Resources, open_resources
from arpendo_api.core.settings import Settings

Task = Callable[[Resources], Awaitable[None]]
"""Un tour de travail périodique, à partir des ressources partagées du processus.

Elle ne rend rien : seul compte qu'elle aboutisse. Elle reçoit les ressources plutôt que de les
ouvrir, pour que toutes les tâches partagent un seul moteur et un seul client.
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
