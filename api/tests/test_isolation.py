"""La suite partage-t-elle son cache avec l'application qui tourne à côté ?

Le pourquoi est dans le README d'`api/`, section « Tester et vérifier ». Ce module garde ce qui les
sépare — la base logique Valkey — parce que cet invariant ne vit que dans des fichiers de
configuration, où rien ne le protège.
"""

import re
from pathlib import Path
from urllib.parse import urlsplit

from arpendo_api.core.settings import Settings

COMPOSE = Path(__file__).resolve().parent.parent.parent / "infra" / "docker-compose.yml"
"""Le compose **local**, en chemin absolu — la suite peut être lancée d'ailleurs que d'`api/`.

Celui-là et pas un autre : l'invariant porte sur l'application qui tourne **sur le poste, pendant
la suite**. Un compose de production (#45) décrira une pile que personne ne lève ici, et n'aura
donc rien à dire sur cette séparation.
"""

VALKEY_URL_DU_COMPOSE = re.compile(r"VALKEY_URL:\s*(\S+)")
"""Chaque `VALKEY_URL` que le compose donne à un service.

Lue au **texte** et non au YAML, parce que la valeur est un littéral et le reste : une ancre
`x-env` qui factoriserait la ligne la déplacerait sans la réécrire.

Toute autre forme fait **échouer bruyamment** — `base_logique` lève sur ce qu'elle ne sait pas
lire, et l'assertion d'en-tête couvre la disparition de la clé. Aucune ne rend ce garde vert en
ne mesurant plus rien ; c'est le comportement voulu. En particulier, un compose qui interpolerait
(`VALKEY_URL: ${VALKEY_URL}`) prendrait la valeur du `.env` de la suite : les deux configurations
refusionneraient, et un rouge est alors le **verdict juste**, pas une panne du parseur.
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
    """Le garde porte sur la **configuration**, pas sur un comportement observé, et c'est délibéré.

    La séparation des bases rend le recouvrement *impossible* pour les commandes du keyspace ; un
    test qui compterait des échecs devrait tourner longtemps pour dire quelque chose, et ne dirait
    jamais « jamais ». Mesuré : sans ce garde et sur une base partagée, **30 exécutions de la suite
    sur 30 sont vertes** — le défaut y est entièrement invisible, et c'est ce qui l'avait laissé
    passer.
    """
    du_compose = {
        base_logique(url) for url in VALKEY_URL_DU_COMPOSE.findall(COMPOSE.read_text("utf-8"))
    }

    assert du_compose, "aucun VALKEY_URL lu dans le compose : le garde ne mesure plus rien"
    assert base_logique(Settings().valkey_url) not in du_compose, (
        "la suite vise la même base logique Valkey que l'application du compose : elle effacera "
        "les compteurs de l'application et lira les siens. Poser `VALKEY_URL` sur la base 1 dans "
        "le `.env` (et dans le step Tests de `ci.yml`)"
    )
