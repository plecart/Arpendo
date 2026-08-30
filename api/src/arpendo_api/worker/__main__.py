"""Point d'entrée du conteneur worker : ``python -m arpendo_api.worker``.

Volontairement réduit à l'assemblage. Tout ce qui peut être faux — le câblage du signal, la boucle
de tâches, l'ouverture et la libération des ressources — vit dans le module et a ses tests ; il ne
reste ici que ce qu'un point d'entrée de processus ne peut pas éprouver de l'intérieur.
"""

import asyncio

from arpendo_api.worker import TASKS, run, stop_on_sigterm


async def _main() -> None:
    """Déroule la table de tâches jusqu'au SIGTERM du gestionnaire de conteneurs."""
    await run(TASKS, stop_on_sigterm())


asyncio.run(_main())
