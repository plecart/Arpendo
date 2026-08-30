"""Les types d'événements que la suite déclare — #44 n'en livre aucun de métier.

Module **neutre et léger**, et c'est ce qui compte : le registre d'``EVENTS`` est alimenté par la
déclaration d'une sous-classe, donc le type de test doit vivre quelque part d'importable sans effet
de bord. Le mettre dans ``conftest.py`` obligerait tout importateur — un sous-processus de test, par
exemple — à tirer alembic, FastAPI et httpx pour obtenir une classe de trois lignes, et à
l'atteindre sous le nom exact ``conftest`` : sous un autre nom, le corps de classe serait réexécuté
et la garde du registre lèverait.
"""

from typing import ClassVar

from arpendo_api.core.journal import Event

PREFIXE = "test."
"""Le préfixe de tout identifiant de type déclaré par la suite.

Il sert deux fois : à ce qu'aucune lecture ne prenne un type de test pour un type de production, et
à ce que le nettoyage du journal sache reconnaître ce que la suite a écrit — y compris un événement
sans partie, qu'aucune clause sur ``game_id`` ne peut atteindre.
"""


class Capture(Event):
    """Le type d'événement de toute la suite.

    Un seul, et partagé : deux classes sous le même identifiant lèvent, et déclarer un type par
    module de test multiplierait des classes identiques.
    """

    type: ClassVar[str] = f"{PREFIXE}captured"

    hexagones: int
