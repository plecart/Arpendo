"""Le worker : ce qu'il déroule, et comment il s'arrête."""

import asyncio
import os
import signal
import sys
import uuid
from pathlib import Path
from typing import cast

import pytest
from conftest import MoteurEspion, evenements_persistes
from fastapi import FastAPI

from arpendo_api import worker
from arpendo_api.core.bus import subscribe
from arpendo_api.core.resources import Resources
from arpendo_api.core.settings import Settings
from arpendo_api.worker import TASKS, run, stop_on_sigterm

RESSOURCES_INUTILISEES = cast(Resources, None)
"""Ce que reçoit une tâche qui n'a besoin de rien.

Le battement n'écrit qu'un fichier : lui ouvrir un moteur et un client Valkey pour l'éprouver
donnerait à croire qu'il en dépend.
"""

PUBLIE_DANS_UN_AUTRE_PROCESSUS = """
import asyncio
import sys
import uuid

sys.path.insert(0, sys.argv[1])
import evenements

from arpendo_api.core.bus import publish
from arpendo_api.worker import run

partie = uuid.UUID(sys.argv[2])
arret = asyncio.Event()


async def publier(ressources):
    async with ressources.sessionmaker() as session:
        await publish(
            session,
            ressources.valkey,
            *(evenements.Capture(game_id=partie, hexagones=n) for n in (1, 2, 3)),
        )
    arret.set()


asyncio.run(run({"publier": (0.01, publier)}, arret))
"""
"""Ce que le second processus exécute — et rien d'autre.

Il importe `run` comme le ferait le conteneur, puis lui passe une table d'une seule tâche. Aucun
mode « test » n'existe dans le worker : c'est la table qui change, pas le code.

`evenements` est atteint par `sys.path`, **sous ce nom exact** : sa docstring dit pourquoi — un
second nom réexécuterait le corps de classe et la garde du registre lèverait.
"""

DELAI_INTEGRATION = 30.0
"""Secondes accordées au second processus, du lancement au dernier message.

Bien plus large que les autres délais de cette suite : un interpréteur neuf doit démarrer et
importer SQLAlchemy, pydantic et redis avant d'écrire quoi que ce soit. Ce n'est pas un budget de
fonctionnement, c'est un filet — le dépasser signifie que rien n'est parti.
"""

INTERVALLE_TRES_LONG = 3600.0
"""Un intervalle qu'aucun test ne peut se permettre d'attendre.

C'est ce qui rend observable la promesse de `_repeat` : l'attente entre deux tours porte sur
l'événement d'arrêt, pas sur le temps. Avec un `sleep`, le test expirerait.
"""

DELAI = 5.0
"""Secondes accordées à un `run` qu'on attend arrêté.

Un worker qui ne s'arrête pas attendrait indéfiniment, et une suite qui pend ne dit pas ce qui
manque. Très au-dessus du coût réel d'un tour de boucle sur des intervalles de test.
"""


async def test_run_passe_les_ressources_ouvertes_a_la_tache_qu_il_deroule() -> None:
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


async def test_une_tache_qui_leve_ne_fait_tomber_ni_sa_boucle_ni_les_autres() -> None:
    """Une purge qui échoue sur un hoquet de la base ne doit priver personne des autres tâches.

    C'est la règle du serveur : plusieurs joueurs en dépendent, et l'échec d'un tour est un
    incident local, pas une raison d'arrêter le worker. La tâche fautive reprend au tour
    suivant, les autres n'en savent rien.

    L'erreur n'est pas pour autant avalée — elle part sur le journal de la stdlib, que #42
    configurera. Sans cela, une tâche définitivement cassée boucherait dans le vide en silence.
    """
    arret = asyncio.Event()
    tours: list[str] = []

    async def qui_leve(_: Resources) -> None:
        tours.append("échec")
        raise RuntimeError("hoquet de la base")

    async def survivante(_: Resources) -> None:
        tours.append("ok")
        if tours.count("ok") == 3:
            arret.set()

    async with asyncio.timeout(DELAI):
        await run({"qui_leve": (0.001, qui_leve), "survivante": (0.001, survivante)}, arret)

    assert tours.count("ok") == 3
    assert tours.count("échec") >= 3


async def test_une_tache_est_repetee_jusqu_a_l_arret(settings: Settings) -> None:
    """« Périodique » est ce que cette boucle promet — encore faut-il l'observer.

    Sans ce test, un `_repeat` qui exécuterait la tâche **une seule fois** puis rendrait la main
    passerait tous les autres au vert : ils posent tous l'événement d'arrêt dès le premier appel.

    L'arrêt vient du compteur et non d'une temporisation : le test dure ce que durent trois tours,
    pas une durée choisie d'avance.

    Les réglages sont passés explicitement, comme une application de test les passe à `create_app` :
    c'est ce qui permet d'éprouver le worker contre un environnement décrit plutôt que contre celui
    de la machine.
    """
    arret = asyncio.Event()
    tours = 0

    async def compter(_: Resources) -> None:
        nonlocal tours
        tours += 1
        if tours == 3:
            arret.set()

    async with asyncio.timeout(DELAI):
        await run({"compter": (0.001, compter)}, arret, settings)

    assert tours == 3


async def test_run_libere_les_ressources_avant_de_rendre_la_main(
    moteur_espion: MoteurEspion,
) -> None:
    """Un worker qui rend la main sans fermer ses connexions les laisserait ouvertes côté serveur.

    La table est vide et l'arrêt déjà posé : ce test n'observe pas un arrêt, il observe que le
    chemin de sortie libère — c'est délibérément le cas le plus dépouillé.

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


async def test_le_gestionnaire_de_sigterm_pose_l_evenement_d_arret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le câblage s'éprouve **sans envoyer de signal** : on appelle le gestionnaire qu'il a posé.

    Envoyer un vrai SIGTERM sous pytest tuerait la suite ou dépendrait de la plateforme. Ce qu'on
    veut vérifier n'est de toute façon pas que le système délivre les signaux, mais que *notre*
    gestionnaire pose l'événement.

    Les deux assertions qui encadrent le `sleep(0)` sont ce qui éprouve le **passage par la
    boucle** : `call_soon_threadsafe` dépose le réveil au lieu de l'exécuter sur place, donc
    l'événement n'est pas encore posé au retour du gestionnaire. Un `stop.set()` appelé
    directement — le raccourci qu'un gestionnaire de signal n'a pas le droit de prendre — le
    poserait immédiatement, et la première assertion tomberait.
    """
    poses: dict[int, object] = {}
    monkeypatch.setattr(
        signal, "signal", lambda numero, gestionnaire: poses.setdefault(numero, gestionnaire)
    )

    arret = stop_on_sigterm()
    assert not arret.is_set()

    poses[signal.SIGTERM](signal.SIGTERM, None)
    assert not arret.is_set()

    await asyncio.sleep(0)

    assert arret.is_set()


async def test_le_worker_publie_et_l_api_recoit_dans_l_ordre(
    app: FastAPI, partie: uuid.UUID, journal_nettoye: None
) -> None:
    """Le chemin complet **worker → Valkey → api**, à travers une vraie frontière de processus.

    C'est la raison d'être de #44 : deux abonnés dans le même processus ne prouveraient pas le
    franchissement, seulement que le pub/sub fonctionne en mémoire.

    L'abonnement est ouvert — et **confirmé** — avant que le second processus ne démarre : c'est
    l'ordre qui rend l'observation possible, un abonné qui arrive après la publication ne verrait
    rien et le test rougirait sans raison.

    C'est le seul test de la suite qui franchisse une frontière de processus, donc le seul qui
    puisse échouer pour une raison invisible depuis pytest — un import manquant, une configuration
    absente en CI. D'où le rattrapage de l'expiration : sans lui, le message serait un
    `TimeoutError` nu et la `stderr` capturée exprès serait perdue. Le `finally` garantit qu'aucun
    sous-processus ne survit au test, même coincé sur une connexion.
    """
    async with subscribe(app.state.valkey, partie) as flux:
        processus = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            PUBLIE_DANS_UN_AUTRE_PROCESSUS,
            str(Path(__file__).parent),
            str(partie),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            async with asyncio.timeout(DELAI_INTEGRATION):
                recus = [await anext(flux) for _ in range(3)]
                _, erreurs = await processus.communicate()
        except TimeoutError:
            processus.kill()
            _, erreurs = await processus.communicate()
            pytest.fail(
                "aucun message reçu ; le second processus a dit :\n"
                + erreurs.decode(errors="replace")
            )
        finally:
            if processus.returncode is None:
                processus.kill()
                await processus.wait()

    assert processus.returncode == 0, erreurs.decode(errors="replace")
    assert [recu.hexagones for recu in recus] == [1, 2, 3]
    assert len(await evenements_persistes(app, partie)) == 3


async def test_les_taches_tournent_de_front_et_non_l_une_apres_l_autre() -> None:
    """Une tâche lente n'en retarde aucune autre — c'est ce que la table promet, ici éprouvé.

    Le montage est un interblocage volontaire : la première tâche attend un événement que seule la
    seconde pose. Déroulées l'une après l'autre, elles ne finiraient jamais et le délai rougirait ;
    de front, la seconde libère la première.
    """
    arret = asyncio.Event()
    debloquee = asyncio.Event()

    async def bloquante(_: Resources) -> None:
        await debloquee.wait()
        arret.set()

    async def liberatrice(_: Resources) -> None:
        debloquee.set()

    async with asyncio.timeout(DELAI):
        await run({"bloquante": (0.001, bloquante), "liberatrice": (0.001, liberatrice)}, arret)

    assert debloquee.is_set()


async def test_l_attente_entre_deux_tours_cede_immediatement_a_l_arret() -> None:
    """`docker compose stop` ne doit pas attendre le prochain réveil d'une tâche horaire.

    L'intervalle est d'une heure : si l'attente portait sur le temps plutôt que sur l'événement,
    ce test expirerait au bout de cinq secondes au lieu de rendre la main aussitôt.
    """
    arret = asyncio.Event()
    premier_tour = asyncio.Event()

    async def tache(_: Resources) -> None:
        premier_tour.set()

    async def poser_l_arret_apres_le_premier_tour() -> None:
        await premier_tour.wait()
        arret.set()

    async with asyncio.timeout(DELAI):
        async with asyncio.TaskGroup() as groupe:
            groupe.create_task(run({"lente": (INTERVALLE_TRES_LONG, tache)}, arret))
            groupe.create_task(poser_l_arret_apres_le_premier_tour())
