"""Le worker : second point d'entrée du paquet, et la boucle qui déroule ses tâches périodiques.

Même paquet que l'api, même couche de services, même image — commande différente et conteneur
distinct (cadrage §13.0). Il ne fusionne jamais avec l'api : les tâches planifiées ne doivent
s'exécuter qu'une fois, quel que soit le nombre d'instances HTTP (§13.9 règle 2).
"""

import asyncio
import logging
import signal
from collections.abc import Awaitable, Callable, Mapping
from contextlib import suppress
from pathlib import Path

from arpendo_api.core.resources import Resources, open_resources
from arpendo_api.core.settings import Settings, load_settings

_journal = logging.getLogger(__name__)
"""Le journal du worker.

Un ``logging.Logger`` de la stdlib, et non un logger structlog : c'est ``configure_logging`` qui,
depuis le point d'entrée, branche la racine sur le rendu JSON — un échec de tâche en ressort donc
formaté comme le reste, sans qu'une ligne change ici. Le nom du module devient la clé ``logger``
de la ligne.
"""

Task = Callable[[Resources], Awaitable[None]]
"""Un tour de travail périodique, à partir des ressources partagées du processus.

Elle ne rend rien : seul compte qu'elle aboutisse — et elle a le droit de ne pas aboutir, un tour
qui lève étant traité par ``_repeat`` sans conséquence pour les autres. Elle reçoit les ressources
plutôt que de les ouvrir, pour que toutes les tâches partagent un seul moteur et un seul client.
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

Le nom sert **au journal** : c'est lui qui dit quelle tâche a raté son tour, sans quoi il faudrait
lire la trace pour le savoir. Le dictionnaire interdit par ailleurs deux entrées homonymes.
"""


async def _repeat(
    name: str, interval: float, task: Task, resources: Resources, stop: asyncio.Event
) -> None:
    """Exécute une tâche, attend son intervalle, recommence — jusqu'à l'événement d'arrêt.

    L'attente porte sur l'**événement**, pas sur le temps : un ``sleep`` obligerait l'arrêt à
    patienter jusqu'au prochain réveil, et un intervalle d'une heure rendrait un ``docker compose
    stop`` insupportable. Ici, poser l'événement interrompt l'attente immédiatement.

    La tâche s'exécute **avant** la première attente : un worker qui vient de démarrer a fait son
    premier tour tout de suite, ce dont le healthcheck du conteneur dépend.

    **Un tour qui échoue ne fait pas tomber la boucle.** Plusieurs joueurs dépendent de ce
    processus : l'échec d'une purge sur un hoquet de la base est un incident local, pas une raison
    de priver tout le monde des autres tâches. Le tour est perdu, l'erreur est journalisée, le
    suivant repart.

    ``except Exception`` et non ``BaseException`` : ``CancelledError`` doit continuer de traverser,
    sinon l'annulation du groupe ne pourrait plus arrêter cette boucle.
    """
    while not stop.is_set():
        try:
            await task(resources)
        except Exception:
            _journal.exception("le tour de la tâche %s a échoué", name)
        with suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), interval)


async def run(
    tasks: Mapping[str, tuple[float, Task]],
    stop: asyncio.Event,
    settings: Settings | None = None,
) -> None:
    """Ouvre les ressources partagées, déroule la table de tâches, et libère tout à l'arrêt.

    Args:
        tasks: la table à dérouler — un nom, son intervalle en secondes, et la coroutine à
            exécuter. Chaque entrée tourne dans **sa propre tâche asyncio** : une tâche lente n'en
            retarde aucune autre, et un test l'observe.
        stop: l'événement qui met fin à toutes les boucles. C'est l'appelant qui le pose — depuis
            un signal en production, directement dans un test.
        settings: les réglages à utiliser. **Le conteneur les fournit** : son point d'entrée les
            lit lui-même, avant d'ouvrir les journaux, pour qu'un démarrage refusé échoue avant
            que quoi que ce soit d'autre n'existe. Le repli sur ``load_settings`` sert aux tests,
            qui appellent ``run`` directement — et à eux seuls ; un test qui veut décrire un
            environnement particulier passe le sien.

    Returns:
        Rien, et seulement une fois **toutes** les boucles terminées et les ressources libérées.

    Raises:
        ConfigurationError: si les réglages sont omis et que l'environnement en décrit une
            configuration invalide.

    Note:
        ``TaskGroup`` plutôt que ``gather`` : si une boucle venait à lever malgré la garde par
        tour, ``gather`` rendrait la main **sans annuler ses sœurs**, qui continueraient de tourner
        sur un moteur et un client déjà fermés — mesuré, quatre tours de plus. Le groupe, lui,
        annule tout avant de remonter, donc cet état ne peut pas exister.
    """
    async with open_resources(settings if settings is not None else load_settings()) as resources:
        async with asyncio.TaskGroup() as groupe:
            for name, (interval, task) in tasks.items():
                groupe.create_task(_repeat(name, interval, task, resources, stop))


def stop_on_sigterm() -> asyncio.Event:
    """Rend l'événement d'arrêt que le prochain SIGTERM posera.

    À appeler depuis la boucle, avant ``run`` : c'est de la boucle courante que le gestionnaire a
    besoin pour rendre la main sans risque.

    ``signal.signal`` et **jamais** ``loop.add_signal_handler`` : le second lève
    ``NotImplementedError`` sous Windows, où ce projet se développe. Le premier existe partout, au
    prix d'une contrainte — le gestionnaire s'exécute **hors du contrôle de la boucle**, entre deux
    instructions de bytecode, donc il ne peut pas toucher un objet asyncio directement.
    ``call_soon_threadsafe`` est le seul pont sûr : il dépose le réveil dans la boucle, qui
    l'exécute quand elle reprend la main.

    C'est ce qui rend l'arrêt d'un conteneur propre : ``docker compose stop`` envoie SIGTERM, la
    boucle sort de ses attentes, ``run`` libère les ressources, et le processus se termine sans que
    Docker ait à le tuer au bout de son délai de grâce.

    Returns:
        L'événement, non posé. Le poser est le seul effet du signal.
    """
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    signal.signal(signal.SIGTERM, lambda *_: loop.call_soon_threadsafe(stop.set))
    return stop
