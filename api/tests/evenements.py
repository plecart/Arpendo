"""Les types d'événements que la suite déclare — #44 n'en livre aucun de métier.

Module **neutre et léger**, et c'est tout ce qu'il apporte : dans ``conftest.py``, obtenir une
classe de trois lignes obligeait un importateur — un sous-processus de test, par exemple — à tirer
alembic, FastAPI et httpx avec elle.

**À importer sous le nom ``evenements``, et sous aucun autre.** Le registre d'``EVENTS`` est
alimenté par la déclaration d'une sous-classe : charger ce fichier une seconde fois sous un autre
nom — ``tests.evenements`` plutôt que ``evenements`` — en réexécute le corps de classe, et la garde
du registre lève ``ValueError: identifiant de type déjà inscrit``. C'est une propriété de
``sys.modules``, pas de l'endroit où le fichier est rangé : le déplacement depuis ``conftest.py``
n'y change rien, seule cette consigne le fait. Le sous-processus de test de #44 devra donc
faire ``sys.path.insert(0, …/api/tests)`` puis ``import evenements``.
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
