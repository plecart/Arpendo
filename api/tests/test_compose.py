"""Le compose donne-t-il à chaque point d'entrée ce qu'il exige — pour tourner, et pour s'arrêter ?

Seul fichier de la suite qui lise `infra/`. Il ne teste pas Docker : il garde ce que **rien
d'autre** ne peut voir, parce que les tests parlent aux services depuis l'hôte et jamais depuis les
conteneurs `api` et `worker`.

- **Pour tourner** : un bloc `environment` amputé laisse la suite entièrement verte et fait partir
  le conteneur en boucle de redémarrage. Mesuré.
- **Pour s'arrêter** : les deux délais qui doivent s'ordonner vivent l'un ici, l'autre dans
  `.env.example` ; aucune ligne de code ne les rapproche, donc aucun test de code ne les compare.
"""

import re
from typing import Any

import pytest
import yaml
from conftest import COMPOSE, ENV_EXAMPLE, variables_requises

from arpendo_api.core.settings import Settings

IMAGE_DU_PAQUET = "arpendo-api:dev"
"""L'image que partagent les points d'entrée du paquet (cadrage §13.0 : un paquet, deux entrées).

C'est **elle** qui désigne les services concernés, et non une liste de noms écrite ici : un
troisième point d'entrée bâti sur la même image sera couvert le jour où il naîtra, sans que
personne ait à penser à l'ajouter. Une liste de noms, elle, aurait vieilli en silence.
"""

BORNE_D_UVICORN = re.compile(r"^UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN=(\d+)$", re.MULTILINE)
"""Les secondes qu'uvicorn accorde aux connexions ouvertes, telles que `.env.example` les pose."""

ANCRE_PARTAGEE = "x-env"
"""Le champ d'extension qui porte l'environnement commun aux points d'entrée du paquet.

Compose ignore les clés `x-`, mais les conserve dans le document : c'est le seul endroit d'où l'on
puisse lire l'ancre **avant** sa fusion. Les blocs `environment` des services, eux, sont déjà
fusionnés quand `yaml.safe_load` les rend — la partition y est invisible.
"""


def _document() -> dict[str, Any]:
    """Le compose local, tel que YAML le rend."""
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def _services_du_paquet() -> dict[str, dict[str, Any]]:
    """Les services du compose qui exécutent le paquet, par nom.

    `yaml.safe_load` **développe les ancres** au chargement : les blocs `environment` étant
    factorisés dans `x-env`, ce test lit le résultat de la fusion et non la référence — il dit donc
    ce que chaque conteneur reçoit vraiment, quelle que soit la façon dont le compose l'écrit.
    """
    services: dict[str, dict[str, Any]] = _document()["services"]
    return {nom: bloc for nom, bloc in services.items() if bloc.get("image") == IMAGE_DU_PAQUET}


def test_le_compose_declare_au_moins_deux_points_d_entree() -> None:
    """Garde-fou du garde : sans lui, une image renommée viderait la paramétrisation ci-dessous.

    Un test paramétré sur une collection vide ne s'exécute pas — et ne rougit donc jamais. C'est
    le témoin positif qui distingue « la règle est respectée » de « la mesure ne mesure rien ».
    """
    assert set(_services_du_paquet()) == {"api", "worker"}


@pytest.mark.parametrize("service", sorted(_services_du_paquet()))
def test_chaque_point_d_entree_recoit_toute_la_configuration_requise(service: str) -> None:
    """Tout champ requis de ``Settings`` est présent dans l'environnement de chaque service.

    ``Settings`` valide la configuration **entière** au démarrage, quel que soit le point d'entrée :
    un `worker` à qui manque un seuil du limiteur — qu'il n'utilise pourtant jamais — refuse de
    démarrer et redémarre en boucle. La règle est donc « tout ou rien », pas « ce dont le service
    se sert ».

    L'inclusion est à sens unique : un service peut porter davantage. `api` déclare
    ``FORWARDED_ALLOW_IPS``, que lit uvicorn et non ``Settings``.
    """
    declarees = set(_services_du_paquet()[service]["environment"])

    assert variables_requises() <= declarees


def test_l_ancre_partagee_porte_exactement_ce_que_lisent_les_reglages() -> None:
    """La partition entre l'ancre et les services est une **règle**, pas une liste à tenir.

    Ce que ``Settings`` lit est commun aux deux points d'entrée et vit dans l'ancre ; ce que lit le
    serveur qui héberge l'api — ``UVICORN_*``, ``FORWARDED_ALLOW_IPS`` — reste sur `api` seule.
    L'égalité se lit donc dans les deux sens : une variable de réglages laissée hors de l'ancre s'y
    recopierait à nouveau service par service, et une variable d'uvicorn glissée dedans serait
    donnée à un `worker` qui n'exécute pas uvicorn.

    L'attendu est **dérivé du modèle**, comme ``variables_requises`` : ajouter un champ à
    ``Settings`` fait rougir ici tant que l'ancre ne le porte pas.
    """
    assert set(_document()[ANCRE_PARTAGEE]) == {nom.upper() for nom in Settings.model_fields}


def _secondes(duree: str) -> int:
    """Une durée Compose exprimée en secondes — ``30s`` → 30.

    Volontairement étroite : le compose n'écrit que des secondes. Toute autre unité fait échouer le
    garde bruyamment, plutôt que d'être lue de travers — une durée mal comprise rendrait vert un
    ordre qui ne tient plus.

    Args:
        duree: la valeur d'un ``stop_grace_period``.

    Returns:
        Le nombre de secondes.
    """
    secondes = re.fullmatch(r"(\d+)s", duree)
    assert secondes, f"durée {duree!r} : ce garde ne lit que des secondes, pas d'autre unité"
    return int(secondes[1])


def test_uvicorn_ferme_avant_que_docker_n_abrege() -> None:
    """L'arrêt gracieux tient à un **ordre**, et cet ordre est réparti sur deux fichiers.

    ``stop_grace_period`` dit à Docker quand il tue ; ``UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN`` dit à
    uvicorn quand il ferme de lui-même. Que le second passe au-dessus du premier, et c'est encore
    le SIGKILL qui tranche : le délai n'aura fait que retarder la mort brutale. Aucun test de code
    ne peut voir ça, et un commentaire de chaque côté ne l'empêche pas — seule cette lecture
    croisée le tient.

    Elle couvre du même geste la présence du délai : sans lui, Docker s'en tient à ses 10 secondes.
    """
    proposee = BORNE_D_UVICORN.search(ENV_EXAMPLE.read_text(encoding="utf-8"))
    assert proposee, (
        "`.env.example` ne propose plus de borne à uvicorn : il attendrait les connexions ouvertes "
        "sans limite, et Docker le tuerait au SIGKILL"
    )
    borne = int(proposee[1])

    for nom, bloc in sorted(_services_du_paquet().items()):
        delai = bloc.get("stop_grace_period")
        assert delai, f"`{nom}` n'a pas de `stop_grace_period` : Docker le tue au bout de 10 s"
        assert borne < _secondes(delai), (
            f"uvicorn attend jusqu'à {borne} s là où Docker tue `{nom}` à {delai} : le SIGKILL "
            "arrive le premier et l'arrêt n'est plus gracieux"
        )
