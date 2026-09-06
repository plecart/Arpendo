"""La suite partage-t-elle ses magasins avec quelqu'un — l'application, ou une suite voisine ?

Le pourquoi est dans le README d'`api/`, section « Tester et vérifier ». Ce module garde les deux
séparations, parce que ni l'une ni l'autre ne vit dans du code : celle d'avec l'application vit
dans des fichiers de configuration, celle d'avec les suites voisines dans une fixture de session
qu'un jour on croira facultative.

Les trois gardes portent sur la **configuration**, pas sur un comportement observé, et c'est
délibéré — voir la docstring du premier.
"""

import re

from conftest import COMPOSE
from magasins import (
    BASE_DE_LA_SUITE,
    DATABASE_URL,
    INDEX_CANDIDATS,
    base_logique,
    nom_de_base,
)

from arpendo_api.core.settings import Settings

VALKEY_URL_DU_COMPOSE = re.compile(r"VALKEY_URL:\s*(\S+)")
"""Chaque `VALKEY_URL` que le compose donne à un service.

Lue au **texte** et non au YAML, parce que la valeur est un littéral et le reste : l'ancre
`x-env` qui la factorise l'a déplacée sans la réécrire.

Toute autre forme fait **échouer bruyamment**, jamais silencieusement : l'interpolation a son
propre message, la disparition de la clé aussi, et `base_logique` lève sur le reste. Aucune ne
rend ce garde vert en ne mesurant plus rien.
"""


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


def test_la_suite_tourne_sur_sa_propre_base_postgresql() -> None:
    """La suite écrit dans une base créée pour elle, jamais dans celle que l'environnement nomme.

    Le garde est **exact** et non préfixé : le nom porte le pid de ce processus, la seule valeur
    qu'aucune suite concurrente ne peut porter en même temps que nous. `startswith` laisserait
    passer la base d'une voisine, qui est précisément ce dont on se sépare.

    La comparaison au DSN d'origine reste, et elle n'est pas redondante : elle est ce qui rougit si
    quelqu'un pointe l'environnement de la suite sur une base déjà nommée `arpendo_test_…`.
    """
    base = nom_de_base(Settings().database_url.get_secret_value())

    assert base == BASE_DE_LA_SUITE, (
        f"la suite tourne sur la base `{base}` et non sur la sienne : elle partage ses lignes de "
        "journal — et son schéma — avec l'application du compose et avec toute suite voisine. La "
        "fixture `magasins` de `conftest.py` n'a pas posé l'environnement"
    )
    assert base != nom_de_base(DATABASE_URL), (
        "la base de la suite est celle que l'environnement nomme : le test des migrations "
        "redescendra à `base` le schéma d'une voisine en plein test"
    )


def test_la_suite_tourne_sur_sa_propre_base_logique_valkey() -> None:
    """La suite compte ses requêtes sur une base logique qu'elle s'est réservée.

    L'index exact n'est pas prévisible — c'est le premier libre — donc le garde porte sur
    l'**appartenance au jeu des candidats**, ce qui exclut d'un coup la 0 de l'application et la
    base des verrous. C'est aussi ce qui rougit si la fixture `magasins` cessait de poser
    l'environnement : elle laisserait la suite sur celle des verrous, qu'elle viderait.
    """
    index = base_logique(Settings().valkey_url)

    assert index in INDEX_CANDIDATS, (
        f"la suite compte sur la base logique {index}, qu'elle ne s'est pas réservée : elle "
        f"partage ses compteurs — qu'elle observe et purge globalement — avec l'application du "
        f"compose ou avec une suite voisine. Attendu l'une de {INDEX_CANDIDATS}"
    )
