"""La suite partage-t-elle son cache avec l'application qui tourne à côté ?

`just test` **exige** `just up` : sur un poste, l'application tourne toujours pendant la suite, et
les deux parlent au même serveur Valkey. Ce module garde la seule chose qui les sépare — la base
logique — parce qu'elle ne vit que dans des fichiers de configuration, où rien ne la protège.
"""

import re
from pathlib import Path
from urllib.parse import urlsplit

from arpendo_api.core.settings import Settings

COMPOSE = Path(__file__).resolve().parent.parent.parent / "infra" / "docker-compose.yml"
"""Le compose local, en chemin absolu : la suite peut être lancée d'ailleurs que d'`api/`."""

VALKEY_URL_DU_COMPOSE = re.compile(r"VALKEY_URL:\s*(\S+)")
"""Chaque `VALKEY_URL` que le compose donne à un service.

Lue au **texte** et non au YAML : la valeur est un littéral, et la chercher ainsi survit à sa
factorisation future dans une ancre `x-env` — l'ancre déplace la ligne, elle ne la réécrit pas.
"""


def base_logique(url: str) -> int:
    """L'index de base de données que porte une URL Valkey — zéro si elle n'en nomme aucune.

    `redis://hôte:6379/2` → 2 ; `redis://hôte:6379` → 0, qui est le défaut du protocole.

    Args:
        url: une URL Valkey ou Redis.

    Returns:
        L'index, tel que le client l'emploiera.
    """
    chemin = urlsplit(url).path.strip("/")
    return int(chemin) if chemin else 0


def test_la_suite_n_utilise_pas_la_base_valkey_de_l_application() -> None:
    """La suite et l'application qui tourne à côté ne se voient pas — le pourquoi est dans le
    README d'`api/`, section « Tester et vérifier ».

    Ce garde porte sur la **configuration** et non sur un comportement observé, et c'est délibéré :
    la séparation des bases rend le recouvrement *impossible*, alors qu'un test qui compterait des
    échecs devrait tourner longtemps pour dire quelque chose — et ne dirait jamais « jamais ».
    L'invariant ne vit sinon que dans `.env` et `ci.yml`, où rien ne le protège.

    Ce qu'il ne prouve **pas** : deux suites lancées en parallèle depuis deux worktrees visent la
    même base logique et continuent, elles, de s'effacer mutuellement leurs compteurs.
    """
    du_compose = {
        base_logique(url) for url in VALKEY_URL_DU_COMPOSE.findall(COMPOSE.read_text("utf-8"))
    }

    assert du_compose, "aucun VALKEY_URL lu dans le compose : le garde ne mesure plus rien"
    assert base_logique(Settings().valkey_url) not in du_compose
