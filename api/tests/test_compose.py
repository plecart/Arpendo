"""Le compose local donne-t-il à chaque point d'entrée la configuration qu'il exige ?

Seul fichier de la suite qui lise `infra/`. Il ne teste pas Docker — il teste une **partition** que
rien d'autre ne peut voir : les tests parlent aux services depuis l'hôte, jamais depuis les
conteneurs `api` et `worker`, si bien qu'un bloc `environment` amputé laisse la suite entièrement
verte et fait partir le conteneur en boucle de redémarrage. Mesuré.
"""

from typing import Any

import pytest
import yaml
from conftest import COMPOSE, variables_requises

IMAGE_DU_PAQUET = "arpendo-api:dev"
"""L'image que partagent les points d'entrée du paquet (cadrage §13.0 : un paquet, deux entrées).

C'est **elle** qui désigne les services concernés, et non une liste de noms écrite ici : un
troisième point d'entrée bâti sur la même image sera couvert le jour où il naîtra, sans que
personne ait à penser à l'ajouter. Une liste de noms, elle, aurait vieilli en silence.
"""


def _services_du_paquet() -> dict[str, dict[str, Any]]:
    """Les services du compose qui exécutent le paquet, par nom.

    `yaml.safe_load` **développe les ancres** au chargement : le jour où les blocs `environment`
    seront factorisés dans une ancre `x-env` (#42), ce test lira le résultat de la fusion et non
    la référence — il continuera donc de dire la vérité sans être touché.
    """
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    services: dict[str, dict[str, Any]] = compose["services"]
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
