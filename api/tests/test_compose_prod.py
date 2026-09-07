"""Le compose de production applique-t-il, service par service, la table de durcissement du §13.10 ?

Cadrage §13.10, « Durcissement des conteneurs » : une table de mesures dont l'issue #45 exige que
chacune soit **lisible dans le fichier**. Lisible, c'est bien ; tenue par un test, c'est mieux —
un `read_only: true` retiré « pour débloquer un déploiement » ne se remarque pas dans un diff de
soixante lignes, et personne ne lève cette pile sur le poste. Ce module lit le fichier comme YAML,
sans Docker ; ce que seul Docker peut dire (le `config` qui interpole, la validation du Caddyfile)
est joué par le job `image` de la CI.

Chaque ligne de la table est un test, ou une clause d'un test paramétré sur les services : la table
est la spécification, le fichier est l'implémentation, et ce module est ce qui les compare.

Deux mesures viennent de l'image plutôt que du compose pour les services bâtis sur l'image du
paquet : `USER` et `HEALTHCHECK` sont dans `api/Dockerfile`, une seule déclaration pour tous les
environnements. Le garde va les y lire plutôt que d'exiger une redite dans le compose.
"""

import re
from pathlib import Path
from typing import Any

import pytest
from conftest import COMPOSE_PROD, DOCKERFILE, document_yaml

UTILISATEURS_PRIVILEGIES = {"root", "0"}
"""Les écritures de `user:` (ou de `USER`) qui désignent root — interdites à chaque service."""

REAJOUTS_DE_CAPACITE = {"caddy": ["NET_BIND_SERVICE"]}
"""Le seul réajout que la table tolère (« réajout explicite si strictement nécessaire »).

`caddy`, et une seule capacité : le binaire de l'image officielle porte une capacité de fichier
(`getcap` → `cap_net_bind_service=ep`), et un `exec` échoue quand elle manque à l'ensemble
*bounding* — mesuré. Le port 443, lui, n'est pas privilégié dans un conteneur Docker. Tout autre
réajout, sur tout autre service, rougit ici : la liste est le contrat.
"""

PORTS_PUBLIES = {"caddy": ["443:443"]}
"""« Un seul port publié » : `caddy` sur 443, et rien d'autre nulle part."""


def _services() -> dict[str, dict[str, Any]]:
    """Les services du compose de production, par nom."""
    services: dict[str, dict[str, Any]] = document_yaml(COMPOSE_PROD)["services"]
    return services


def _par_service() -> list[Any]:
    return [pytest.param(nom, bloc, id=nom) for nom, bloc in sorted(_services().items())]


def _garanti_par_le_dockerfile(bloc: dict[str, Any], instruction: str) -> str | None:
    """L'argument de `instruction` dans `api/Dockerfile`, pour un service sur l'image du paquet.

    Une référence interpolée (`${ARPENDO_IMAGE:?…}`) est l'image du paquet : ce que son Dockerfile
    déclare vaut pour le service. Pour une image tirée, rien n'est garanti — `None`.
    """
    if not str(bloc.get("image", "")).startswith("${"):
        return None
    trouve = re.search(rf"^{instruction}\s+(.+)$", DOCKERFILE.read_text(encoding="utf-8"), re.M)
    return trouve[1].strip() if trouve else None


def _montages(bloc: dict[str, Any]) -> list[str]:
    """Les sources des volumes d'un service, syntaxe courte (`a:b`) ou longue (`source:`)."""
    sources = []
    for volume in bloc.get("volumes", []):
        if isinstance(volume, str):
            sources.append(volume.split(":", 1)[0])
        else:
            sources.append(str(volume.get("source", "")))
    return sources


def _tmpfs(bloc: dict[str, Any]) -> list[str]:
    """Les cibles `tmpfs` d'un service, clé courte `tmpfs:` ou volume long `type: tmpfs`."""
    cibles = [str(cible).split(":", 1)[0] for cible in bloc.get("tmpfs", [])]
    cibles += [
        str(volume["target"])
        for volume in bloc.get("volumes", [])
        if isinstance(volume, dict) and volume.get("type") == "tmpfs"
    ]
    return cibles


def test_le_compose_de_production_declare_les_services_attendus() -> None:
    """Témoin positif des paramétrages : les quatre services de la table (pas de `postgres`)."""
    assert set(_services()) == {"caddy", "api", "worker", "valkey"}, (
        "témoin : les services du compose de production ont changé"
    )


def test_seul_caddy_publie_un_port_et_c_est_443() -> None:
    """« Un seul port publié » — lu sur tous les services à la fois, pas seulement sur `caddy`."""
    publies = {nom: [str(p) for p in bloc.get("ports", [])] for nom, bloc in _services().items()}
    assert {nom: ports for nom, ports in publies.items() if ports} == PORTS_PUBLIES, (
        f"ports publiés : {publies} ; attendu {PORTS_PUBLIES}, et rien d'autre"
    )


@pytest.mark.parametrize(("nom", "bloc"), _par_service())
def test_chaque_service_tourne_sous_un_utilisateur_non_root(nom: str, bloc: dict[str, Any]) -> None:
    """« Jamais de conteneur applicatif en root » : `user:` ici, ou `USER` dans le Dockerfile."""
    utilisateur = str(bloc.get("user") or _garanti_par_le_dockerfile(bloc, "USER") or "")
    assert utilisateur, (
        f"`{nom}` n'a ni `user:` ni `USER` d'image : l'image tirée décide, et c'est root"
    )
    assert utilisateur.split(":")[0] not in UTILISATEURS_PRIVILEGIES, f"`{nom}` tourne en root"


@pytest.mark.parametrize(("nom", "bloc"), _par_service())
def test_chaque_service_a_un_systeme_de_fichiers_en_lecture_seule(
    nom: str, bloc: dict[str, Any]
) -> None:
    """`read_only: true` + au moins un `tmpfs` : rien d'écrit ailleurs que là où on l'a décidé."""
    assert bloc.get("read_only") is True, f"`{nom}` n'est pas en `read_only: true`"
    assert _tmpfs(bloc), f"`{nom}` est en lecture seule sans aucun `tmpfs` : où écrit-il ?"


@pytest.mark.parametrize(("nom", "bloc"), _par_service())
def test_chaque_service_abandonne_toutes_les_capacites(nom: str, bloc: dict[str, Any]) -> None:
    """`cap_drop: ALL`, puis les seuls réajouts du contrat ; `no-new-privileges` partout."""
    assert bloc.get("cap_drop") == ["ALL"], f"`{nom}` ne fait pas `cap_drop: [ALL]`"
    assert bloc.get("cap_add", []) == REAJOUTS_DE_CAPACITE.get(nom, []), (
        f"`{nom}` réajoute {bloc.get('cap_add')} : seul {REAJOUTS_DE_CAPACITE} est toléré"
    )
    assert "no-new-privileges:true" in bloc.get("security_opt", []), (
        f"`{nom}` n'active pas `no-new-privileges`"
    )


@pytest.mark.parametrize(("nom", "bloc"), _par_service())
def test_chaque_service_est_borne_redemarre_et_sonde(nom: str, bloc: dict[str, Any]) -> None:
    """Limites de ressources, `restart: unless-stopped`, `healthcheck` : le bas de la table."""
    assert bloc.get("mem_limit"), (
        f"`{nom}` n'a pas de `mem_limit` : un emballement emporte la machine"
    )
    assert bloc.get("cpus"), f"`{nom}` n'a pas de `cpus`"
    assert bloc.get("restart") == "unless-stopped", f"`{nom}` n'a pas `restart: unless-stopped`"
    assert bloc.get("healthcheck") or _garanti_par_le_dockerfile(bloc, "HEALTHCHECK"), (
        f"`{nom}` n'a pas de `healthcheck`, ni ici ni dans le Dockerfile du paquet"
    )


@pytest.mark.parametrize(("nom", "bloc"), _par_service())
def test_aucun_service_ne_monte_le_socket_docker(nom: str, bloc: dict[str, Any]) -> None:
    """« Socket Docker jamais monté » : ce serait une évasion triviale vers root sur l'hôte."""
    fautifs = [source for source in _montages(bloc) if "docker.sock" in source]
    assert not fautifs, f"`{nom}` monte {fautifs}"


def test_valkey_exige_un_mot_de_passe() -> None:
    """« Valkey authentifié, même sans port publié » — par le même drapeau qu'en local et en CI."""
    drapeaux = str(_services()["valkey"].get("environment", {}).get("VALKEY_EXTRA_FLAGS", ""))
    assert "--requirepass" in drapeaux, f"`valkey` démarre sans `--requirepass` : {drapeaux!r}"


def test_l_api_ne_croit_que_le_reseau_du_compose() -> None:
    """`FORWARDED_ALLOW_IPS` est le CIDR du sous-réseau déclaré, littéral — jamais `*`.

    Uvicorn ne réécrit `request.client` que pour un pair de cette liste (cadrage §13.7) ; le
    sous-réseau est **fixé** par `ipam`, sinon Docker en choisit un à chaque création du réseau et
    la valeur littérale cesserait de correspondre sans qu'aucune erreur ne le dise.
    """
    reseaux: dict[str, Any] = document_yaml(COMPOSE_PROD)["networks"]
    sous_reseaux = [
        str(config.get("subnet", ""))
        for reseau in reseaux.values()
        for config in (reseau.get("ipam", {}).get("config") or [])
    ]
    assert len(sous_reseaux) == 1, f"un seul sous-réseau fixé attendu, lu {sous_reseaux}"
    confiance = str(_services()["api"]["environment"].get("FORWARDED_ALLOW_IPS", ""))
    assert confiance == sous_reseaux[0], (
        f"`api` croit {confiance!r}, le sous-réseau déclaré est {sous_reseaux[0]!r}"
    )
    assert "*" not in confiance


def test_le_caddyfile_vide_le_flux_sans_attendre() -> None:
    """§13.7 : « le vidage immédiat doit être configuré explicitement » — `flush_interval -1`.

    Sur tout le `reverse_proxy`, sans matcher : la route SSE n'a pas encore de chemin, et le défaut
    de Caddy (vidage sur `text/event-stream` seulement) est une heuristique qu'on ne veut pas
    devoir connaître. Lu tel quel, le Caddyfile n'étant pas du YAML.
    """
    caddyfile = (Path(COMPOSE_PROD).parent / "Caddyfile").read_text(encoding="utf-8")
    assert re.search(r"^\s*flush_interval\s+-1\s*$", caddyfile, re.M), (
        "le Caddyfile ne pose pas `flush_interval -1` : la SSE arriverait par paquets en production"
    )
