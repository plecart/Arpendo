"""Point d'entrée du conteneur worker : ``python -m arpendo_api.worker``.

Volontairement réduit à l'assemblage. Tout ce qui peut être faux — le câblage du signal, la boucle
de tâches, l'ouverture et la libération des ressources — vit dans le module et a ses tests ; il ne
reste ici que ce qu'un point d'entrée de processus ne peut pas éprouver de l'intérieur.
"""

import asyncio

from arpendo_api.core.logs import configure_logging
from arpendo_api.core.sentry import configure_sentry
from arpendo_api.core.settings import load_settings
from arpendo_api.worker import TASKS, run, stop_on_sigterm


async def _main() -> None:
    """Lit la configuration, ouvre les journaux et Sentry, puis déroule la table jusqu'au SIGTERM.

    Dans cet ordre, et une seule fois. Les réglages viennent en premier parce que tout en dépend,
    et parce qu'un démarrage refusé doit échouer avant que quoi que ce soit d'autre n'existe. Les
    journaux ensuite, pour que le premier tour de tâche ait déjà où écrire. Sentry en dernier, non
    par contrainte technique — mesuré, il n'installe aucun handler et l'ordre lui est indifférent —
    mais parce que c'est le seul des trois qui ouvre une porte vers le réseau : il vient après ce
    qui peut encore échouer sans rien émettre.
    """
    settings = load_settings()
    configure_logging()
    configure_sentry(settings)
    await run(TASKS, stop_on_sigterm(), settings)


if __name__ == "__main__":
    # `python -m` exécute bien ce fichier sous ce nom, donc la garde ne change rien au conteneur.
    # Elle empêche en revanche qu'un import — un outil d'analyse, une collecte de tests — démarre
    # un worker par accident.
    asyncio.run(_main())
