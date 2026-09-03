"""La suite partage-t-elle son cache avec l'application qui tourne à côté ?

Le pourquoi est dans le README d'`api/`, section « Tester et vérifier ». Ce module garde ce qui les
sépare — la base logique Valkey — parce que cet invariant ne vit que dans des fichiers de
configuration, où rien ne le protège.
"""

import re
from urllib.parse import urlsplit

from conftest import COMPOSE

from arpendo_api.core.settings import Settings

VALKEY_URL_DU_COMPOSE = re.compile(r"VALKEY_URL:\s*(\S+)")
"""Chaque `VALKEY_URL` que le compose donne à un service.

Lue au **texte** et non au YAML, parce que la valeur est un littéral et le reste : une ancre
`x-env` qui factoriserait la ligne la déplacerait sans la réécrire.

Toute autre forme fait **échouer bruyamment**, jamais silencieusement : l'interpolation a son
propre message, la disparition de la clé aussi, et `base_logique` lève sur le reste. Aucune ne
rend ce garde vert en ne mesurant plus rien.
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
    urls = VALKEY_URL_DU_COMPOSE.findall(COMPOSE.read_text("utf-8"))

    assert urls, "aucun VALKEY_URL lu dans le compose : le garde ne mesure plus rien"
    # Une valeur que le compose interpole vient du `.env` — celui de la suite. Les deux
    # configurations refusionnent, et l'isolation disparaît pour de bon. Le dire ici, sinon
    # `base_logique` lève un `ValueError` que le prochain lecteur prendra pour une panne de
    # parseur, et qu'il réparera en assouplissant le parseur.
    interpolees = [url for url in urls if "$" in url]
    assert not interpolees, (
        f"le compose interpole {interpolees} : il prendrait alors la base logique du `.env` de la "
        "suite, et l'application se retrouverait sur la même que les tests. Garder un littéral, "
        "ou déplacer l'isolation ailleurs — mais pas assouplir ce garde"
    )

    du_compose = {base_logique(url) for url in urls}
    assert base_logique(Settings().valkey_url) not in du_compose, (
        "la suite vise la même base logique Valkey que l'application du compose : elle effacera "
        "les compteurs de l'application et lira les siens. Poser `VALKEY_URL` sur la base 1 dans "
        "le `.env` (et dans le step Tests de `ci.yml`)"
    )
