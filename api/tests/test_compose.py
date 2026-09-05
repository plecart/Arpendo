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
from conftest import COMPOSE, ENV_EXAMPLE, variables_des_reglages

IMAGE_DU_PAQUET = "arpendo-api:dev"
"""L'image que partagent les points d'entrée du paquet (cadrage §13.0 : un paquet, deux entrées).

C'est **elle** qui désigne les services concernés, et non une liste de noms écrite ici : un
troisième point d'entrée bâti sur la même image sera couvert le jour où il naîtra, sans que
personne ait à penser à l'ajouter. Une liste de noms, elle, aurait vieilli en silence.

**Une seule chose ne se dérive pas** : le témoin positif ci-dessous énumère les points d'entrée
attendus, et c'est sa raison d'être — il rougit à l'arrivée du troisième pour forcer la
conversation, plutôt que de l'absorber en silence. Tout le reste suit, y compris l'exception
``SERVICE_D_UVICORN``, qui nomme un service et non une liste.
"""

SERVICE_D_UVICORN = "api"
"""Le seul point d'entrée que le serveur uvicorn héberge — donc le seul à lire `UVICORN_*`.

Nommé une fois, ici : c'est l'**exception** à la partition, et une exception se déclare. Tout ce qui
n'est pas cette exception se dérive de ``IMAGE_DU_PAQUET``, sans liste à tenir.
"""

BORNE_UVICORN = "UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN"
"""La variable qui borne l'attente d'uvicorn sur les connexions déjà ouvertes.

Elle traverse **trois** artefacts avant d'agir : `.env.example` la pose, le compose la relaie au
service qui exécute uvicorn, et uvicorn la lit sous ce nom (`auto_envvar_prefix` de click). C'est
une chaîne, et une chaîne cède à son maillon le moins tenu — d'où un garde par maillon plutôt qu'un
seul sur le résultat.
"""

BORNE_POSEE = re.compile(rf"^{BORNE_UVICORN}=(\d+)$", re.MULTILINE)
"""Les secondes que `.env.example` propose au poste."""

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


def test_le_compose_declare_les_points_d_entree_attendus() -> None:
    """Garde-fou du garde : sans lui, une image renommée viderait la paramétrisation ci-dessous.

    Un test paramétré sur une collection vide ne s'exécute pas — et ne rougit donc jamais. C'est
    le témoin positif qui distingue « la règle est respectée » de « la mesure ne mesure rien ».
    """
    assert set(_services_du_paquet()) == {"api", "worker"}


def _declare(fragment: dict[str, Any], cle: str, dans: str) -> dict[str, Any]:
    """La valeur d'une clé du compose, ou un échec qui nomme ce qui manque.

    Un accès direct lèverait un ``KeyError``. pytest le compte parmi les **échecs** et non parmi les
    erreurs — qu'il réserve au montage —, si bien qu'aucun compteur ne le distingue d'une
    assertion ; mais il ne dit rien de ce qu'on cherchait, et une exception nue se lit comme une
    panne de l'outil plutôt que comme un défaut du fichier lu. On la remplace donc par une
    assertion, qui nomme la clé et le fragment.

    **Jamais depuis une aide appelée à l'import.** ``_document`` et ``_services_du_paquet`` le
    sont, par les décorateurs de paramétrisation : une assertion qui remonterait jusqu'à elles
    tomberait à la **collecte** et avorterait le module entier — pire que le ``KeyError`` qu'on
    remplace. Le caveat vaut par transitivité pour toute aide qui appelle celle-ci.

    Deux formes valides du compose échouent ici plutôt que plus loin, et c'est le point :

    - la clé **présente mais vide** — YAML rend ``environment:`` sans contenu par ``None``, qu'une
      garde de simple présence laisse passer avant d'exploser sur un ``TypeError`` (mesuré). Un
      bloc vidé est la forme que prend la suppression d'une ligne de fusion ;
    - le bloc écrit **en liste** (``- CLE=valeur``), que Compose accepte : les clés deviendraient
      des chaînes ``"CLE=valeur"``, et la comparaison rougirait sur un écart illisible.

    Args:
        fragment: le fragment de compose interrogé.
        cle: la clé attendue.
        dans: comment nommer ce fragment dans le message d'échec.

    Returns:
        Le bloc de clés associé à ``cle``.
    """
    valeur = fragment.get(cle)

    assert valeur is not None, f"le compose ne déclare plus `{cle}` dans {dans}"
    assert isinstance(valeur, dict), (
        f"`{cle}` dans {dans} n'est pas un bloc de clés mais un {type(valeur).__name__} : la forme "
        "en liste est un compose valide, mais ses clés sont alors des chaînes `CLE=valeur`"
    )

    return valeur


def _ancre() -> dict[str, Any]:
    """L'environnement partagé, lu **avant** sa fusion — la seule vue de la partition.

    Returns:
        Le contenu de l'ancre.
    """
    return _declare(_document(), ANCRE_PARTAGEE, "son en-tête")


def _environnement_de(service: str) -> dict[str, Any]:
    """Le bloc ``environment`` d'un service du paquet, ancres développées.

    Le trajet « service → bloc → environnement » se faisait sur trois sites, étiquette de message
    recopiée à chaque fois. Une seule formulation, donc une seule à corriger.

    Les **deux** pas passent par ``_declare`` : un service absent de la collection est aussi
    lisible qu'un bloc absent du service, et l'aide bâtie pour supprimer les accès directs n'en
    garde pas un pour elle-même.

    Args:
        service: le nom d'un service du paquet.

    Returns:
        Le bloc ``environment``, tel que le conteneur le recevra.
    """
    bloc = _declare(_services_du_paquet(), service, "les points d'entrée du paquet")

    return _declare(bloc, "environment", f"le service `{service}`")


@pytest.mark.parametrize("service", sorted(_services_du_paquet()))
def test_chaque_point_d_entree_recoit_tout_ce_que_lisent_les_reglages(service: str) -> None:
    """Toute variable que lit ``Settings`` est présente dans l'environnement de chaque service.

    ``Settings`` valide la configuration **entière** au démarrage, quel que soit le point d'entrée :
    un `worker` à qui manque un seuil du limiteur — qu'il n'utilise pourtant jamais — refuse de
    démarrer et redémarre en boucle. La règle est donc « tout ou rien », pas « ce dont le service
    se sert ».

    **Toutes**, et pas seulement les requises : ``SENTRY_DSN`` est le seul réglage facultatif, donc
    le seul qu'un service puisse perdre sans que rien ne casse — Sentry se désactiverait en
    silence, alors que le worker en a autant besoin que l'api (un tour de tâche qui échoue est
    exactement ce qu'on veut voir remonter). Un garde qui ne regarde que les requises laisse
    passer précisément le cas qui ne se remarque pas.

    L'inclusion est à sens unique : un service peut porter davantage. `api` déclare
    ``FORWARDED_ALLOW_IPS``, que lit uvicorn et non ``Settings`` ; ce que le `worker` a le droit de
    porter en plus est borné plus bas.
    """
    declarees = set(_environnement_de(service))

    assert variables_des_reglages() <= declarees


def test_l_ancre_partagee_porte_exactement_ce_que_lisent_les_reglages() -> None:
    """La partition entre l'ancre et les services est une **règle**, pas une liste à tenir.

    Ce que ``Settings`` lit est commun aux deux points d'entrée et vit dans l'ancre ; ce que lit le
    serveur qui héberge l'api — ``UVICORN_*``, ``FORWARDED_ALLOW_IPS`` — reste sur `api` seule.
    L'égalité se lit donc dans les deux sens : une variable de réglages laissée hors de l'ancre s'y
    recopierait à nouveau service par service, et une variable d'uvicorn glissée dedans serait
    donnée à un `worker` qui n'exécute pas uvicorn.

    L'attendu est **dérivé du modèle** (``variables_des_reglages``) : ajouter un champ à
    ``Settings`` fait rougir ici tant que l'ancre ne le porte pas.
    """
    assert set(_ancre()) == variables_des_reglages()


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

    Elle couvre du même geste la présence du délai : sans lui, Docker s'en tient à son défaut.
    """
    proposee = BORNE_POSEE.search(ENV_EXAMPLE.read_text(encoding="utf-8"))
    assert proposee, (
        "`.env.example` ne propose plus de borne à uvicorn : il attendrait les connexions ouvertes "
        "sans limite, et Docker le tuerait au SIGKILL"
    )
    borne = int(proposee[1])

    for nom, bloc in sorted(_services_du_paquet().items()):
        delai = bloc.get("stop_grace_period")
        assert delai, (
            f"`{nom}` n'a pas de `stop_grace_period` : Docker s'en tient à son défaut, trop court "
            "pour fermer proprement des flux ouverts"
        )
        assert borne < _secondes(delai), (
            f"uvicorn attend jusqu'à {borne} s là où Docker tue `{nom}` à {delai} : le SIGKILL "
            "arrive le premier et l'arrêt n'est plus gracieux"
        )


def test_le_compose_relaie_la_borne_a_uvicorn_sous_un_garde() -> None:
    """Le maillon du milieu : la borne posée dans le `.env` doit atteindre le conteneur.

    L'ordre gardé plus haut ne vaut que si la variable arrive jusqu'à uvicorn. La retirer du
    service laisserait tout le reste vrai — `.env.example` la propose toujours, elle est toujours
    sous le délai de Docker — et l'attente redeviendrait pourtant infinie.

    Le garde `:?` fait partie du maillon, il n'est pas un ornement : **mesuré**, une valeur vide est
    ignorée en silence par click, qui retombe sur « sans borne ». Un `${…}` nu laisse Compose
    injecter la chaîne vide avec un simple avertissement sur stderr, et la borne disparaît sans que
    rien n'échoue. La forme brute est lisible ici parce que ``yaml.safe_load`` n'interpole pas.

    Le **type** fait partie de la forme : une borne écrite en entier non quoté (``: 25``) est un
    compose valide — Compose la normalise en chaîne, mesuré — que YAML rend en ``int``. Sans le
    contrôle de type, la vérification de forme lèverait un ``AttributeError`` nu au lieu de dire
    laquelle des formes fautives a été employée.
    """
    assert SERVICE_D_UVICORN in _services_du_paquet(), (
        f"aucun service `{SERVICE_D_UVICORN}` **parmi les points d'entrée du paquet** : soit il a "
        f"été renommé, soit il n'est plus bâti sur `{IMAGE_DU_PAQUET}`. C'est `SERVICE_D_UVICORN` "
        "qui désigne le service exécutant uvicorn, et toute la partition s'y adosse"
    )
    relais = _environnement_de(SERVICE_D_UVICORN).get(BORNE_UVICORN)

    assert relais, (
        f"le service `{SERVICE_D_UVICORN}` ne reçoit plus {BORNE_UVICORN} : uvicorn attendrait "
        "les connexions ouvertes sans limite, et Docker le tuerait au SIGKILL"
    )
    assert isinstance(relais, str) and relais.startswith(f"${{{BORNE_UVICORN}:?"), (
        f"{BORNE_UVICORN} est relayée par {relais!r}, hors de la seule forme sûre. La valeur se "
        "déclare une fois, dans le `.env` : ni littéral ici, ni défaut d'interpolation. Et seul "
        "le `:?` refuse aussi la valeur **vide** — une interpolation nue `${…}` comme un "
        "`${…?…}` sans les deux-points la laissent passer, et click l'ignore en silence. "
        "La borne se perdrait sans un mot"
    )


@pytest.mark.parametrize("service", sorted(set(_services_du_paquet()) - {SERVICE_D_UVICORN}))
def test_un_point_d_entree_sans_uvicorn_ne_recoit_rien_de_plus_que_l_ancre(service: str) -> None:
    """L'autre moitié de la partition : ce qu'uvicorn lit ne descend pas aux autres points d'entrée.

    L'égalité gardée plus haut porte sur le **contenu de l'ancre** ; elle laisserait passer une
    variable d'uvicorn recopiée en plus sur ce service. Elle y serait sans effet — ce point d'entrée
    n'exécute pas uvicorn — mais elle ferait mentir la règle que le compose énonce, et la prochaine
    variable ajoutée « par symétrie » n'aurait plus rien pour l'arrêter.

    Avec le garde d'inclusion plus haut, ce sens ferme l'égalité : un point d'entrée qui n'exécute
    pas uvicorn reçoit **exactement** l'ancre. Le service qui l'exécute est le seul à porter
    davantage, et l'asymétrie est le sujet — l'exception est nommée par ``SERVICE_D_UVICORN``, tout
    le reste est dérivé de l'image.
    """
    surplus = set(_environnement_de(service)) - set(_ancre())

    assert not surplus, (
        f"`{service}` reçoit {sorted(surplus)} en plus de l'ancre. Ce que lit ``Settings`` va dans "
        f"`x-env` ; ce que lit le serveur qui héberge l'api reste sur `{SERVICE_D_UVICORN}`, seul "
        "service à l'exécuter. Si l'une de ces variables est légitimement propre à ce point "
        "d'entrée, c'est la règle de partition qu'il faut amender — dans le compose et ici —, "
        "pas ce garde qu'il faut retirer"
    )
