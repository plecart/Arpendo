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
    INDEX_CANDIDATS,
    INDEX_DES_VERROUS,
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


def test_aucune_base_valkey_de_la_suite_ne_touche_celle_de_l_application() -> None:
    """Le garde porte sur la **configuration**, pas sur un comportement observé, et c'est délibéré.

    La séparation des bases rend le recouvrement *impossible* pour les commandes du keyspace ; un
    test qui compterait des échecs devrait tourner longtemps pour dire quelque chose, et ne dirait
    jamais « jamais ». Mesuré : sans ce garde et sur une base partagée, **30 exécutions de la suite
    sur 30 sont vertes** — le défaut y est entièrement invisible, et c'est ce qui l'avait laissé
    passer.

    Il porte sur **l'ensemble des bases qu'une suite peut atteindre**, et non sur celle qu'elle a
    tirée cette fois-ci : les verrous, et les quatorze index réservables. Comparer l'index obtenu
    ne mesurerait rien — il est tiré du jeu des candidats par construction, donc l'assertion serait
    vraie quel que soit ce jeu. Mesuré : avec la comparaison sur l'index obtenu, `VALKEY_URL` posée
    sur la base 0 — la configuration que `.env.example` interdit — laissait les trois gardes verts.
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
    assert INDEX_DES_VERROUS not in du_compose, (
        "les verrous des suites se posent sur la base logique de l'application du compose, et "
        "chaque suite y écrit une clé. Poser `VALKEY_URL` sur la base 1 dans le `.env` (et dans "
        "le step Tests de `ci.yml`)"
    )
    reservables_du_compose = du_compose & set(INDEX_CANDIDATS)
    assert not reservables_du_compose, (
        f"une suite peut se réserver {reservables_du_compose}, que l'application du compose "
        "utilise : elle la viderait à la réservation, puis effacerait ses compteurs et lirait les "
        "siens"
    )
    # Verte par construction tant que `VALKEY_URL` nomme un index hors de la plage réservable :
    # `INDEX_CANDIDATS` en exclut alors `INDEX_DES_VERROUS` sans avoir à filtrer. Ce qui la met à
    # l'épreuve est la combinaison — filtre retiré **et** verrous sur un index de 2 à 15 — et non
    # l'une de ses deux moitiés. Ne pas lire son vert comme une couverture du jeu de candidats.
    assert INDEX_DES_VERROUS not in INDEX_CANDIDATS, (
        f"une suite peut se réserver la base des verrous {INDEX_DES_VERROUS} : elle la viderait, "
        "et toutes les suites voisines se croiraient alors seules sur leur index"
    )


def test_la_suite_tourne_sur_sa_propre_base_postgresql() -> None:
    """La suite écrit dans une base créée pour elle, jamais dans celle que l'environnement nomme.

    Le garde est **exact** et non préfixé, et une seule assertion suffit donc à couvrir les deux
    moitiés du critère : le nom porte le jeton tiré au chargement de `magasins`, que rien d'autre
    ne porte — il commence donc par `arpendo_test_`, et il diffère de celui qu'un environnement
    peut nommer. `startswith` laisserait passer la base d'une voisine, qui est précisément ce dont
    on se sépare ; une comparaison au DSN d'origine en plus de celle-ci ne pourrait rougir que si
    l'environnement nommait `arpendo_test_<notre jeton>`, un nom tiré au sort à chaque lancement —
    mesuré : elle reste verte quand on la retire.
    """
    base = nom_de_base(Settings().database_url.get_secret_value())

    assert base == BASE_DE_LA_SUITE, (
        f"la suite tourne sur la base `{base}` et non sur la sienne : elle partage ses lignes de "
        "journal — et son schéma — avec l'application du compose et avec toute suite voisine. La "
        "fixture `magasins` de `conftest.py` n'a pas posé l'environnement"
    )


def test_la_suite_tourne_sur_sa_propre_base_logique_valkey() -> None:
    """La suite compte ses requêtes sur une base logique qu'elle s'est réservée.

    L'index exact n'est pas prévisible — c'est le premier libre — donc le garde porte sur
    l'appartenance au jeu des candidats. **Ce qu'il mesure, et lui seul : que la fixture `magasins`
    a bien posé l'environnement.** Que ce jeu soit lui-même sain — disjoint de l'application et des
    verrous — est mesuré par le garde de configuration au-dessus, et pas ici : c'est la
    décomposition qui rend celui-ci autre chose qu'une tautologie.
    """
    index = base_logique(Settings().valkey_url)

    assert index in INDEX_CANDIDATS, (
        f"la suite compte sur la base logique {index}, qu'elle ne s'est pas réservée : elle "
        f"partage ses compteurs — qu'elle observe et purge globalement — avec l'application du "
        f"compose ou avec une suite voisine. Attendu l'une de {INDEX_CANDIDATS}"
    )
