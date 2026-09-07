"""Toute image tirée est-elle épinglée par empreinte — et suivie par qui la rafraîchit ?

Cadrage §13.10, « Images épinglées par empreinte ». L'invariant est réparti sur deux fichiers que
deux écosystèmes Dependabot différents rafraîchissent — `docker` sur `api/Dockerfile`,
`docker-compose` sur `infra/` — et le bot conserve la forme `tag@sha256:…` ; ce garde vise la main
qui ajoute une image par tag seul, ou qui retire une empreinte pour « débloquer » un build. Aucun
test de code ne peut le voir : les tests parlent aux services, jamais à l'image qui les porte.

Trois choses que le bot ne voit pas, gardées ici parce que rien d'autre ne les garde :

- une image tirée **hors d'une ligne `FROM`** (`COPY --from=<image>`) : son parseur ne lit que
  ces lignes, l'empreinte ne serait jamais rafraîchie — d'où « tout `COPY --from` nomme une
  étape » ;
- le bot propose aussi les **tags voisins** (`python:3.14-slim`, `postgres:18`), pas seulement
  l'empreinte suivante : un tel build passerait en vert et livrerait un interpréteur que
  `api/.python-version` n'a pas choisi ;
- les images des `services:` de `ci.yml`, qu'aucun écosystème ne suit : la CI doit tester sur les
  images que le compose fait tourner (§13.6), et seul un test peut tenir les deux à égalité.

Ce qui **n'est pas** tiré n'a pas d'empreinte à porter : un service qui construit son image
(`build:`) la nomme, il ne la tire pas. C'est la clé `build`, pas le nom, qui l'exclut — ainsi le
garde suit une image renommée sans qu'on y pense.

**Chaque famille porte son témoin** : un paramétrage vide ne rougit jamais, et une population qui
rétrécit parce qu'un motif ne lit plus le fichier est un garde qui disparaît en silence. Les deux
familles paramétrées et l'inclusion des `COPY --from` ont un témoin séparé ; les deux autres tests
sont écrits en une égalité d'ensembles, où l'ensemble vide est un rouge.
"""

import re
from typing import Any

import pytest
from conftest import CI, COMPOSE, DOCKERFILE, PYTHON_VERSION, document_yaml

EMPREINTE = re.compile(r"^\S+:[\w][\w.-]*@sha256:[0-9a-f]{64}$")
"""La forme `image:tag@sha256:<64 hexadécimaux>` : le tag reste, lisible, l'empreinte fige.

Le tag seul est refusé, l'empreinte seule aussi — sans tag, personne ne sait plus ce qu'elle fige,
et Dependabot ne sait plus la suivre.
"""

INSTRUCTION_FROM = re.compile(
    r"^FROM\s+(?:--platform=\S+\s+)?(?P<image>\S+)(?:\s+AS\s+(?P<etape>\S+))?", re.I | re.M
)
"""Une ligne `FROM`, telle que Docker et Dependabot la lisent : `--platform` toléré, casse libre."""

COPIE_DEPUIS = re.compile(r"^COPY\s.*?--from=(?P<source>\S+)", re.I | re.M)
"""La source d'un `COPY --from=…` — une étape de ce Dockerfile, ou une image tirée en douce."""

COMMENTAIRE = re.compile(r"^[ \t]*#.*\r?\n", re.M)
"""Une ligne de commentaire — retirée d'abord : un `\\` qui la termine ne continue rien."""

CONTINUATION = re.compile(r"\\\r?\n\s*")
"""Un `\\` en fin de ligne d'instruction : Docker lit la suite comme la même instruction."""


def _dockerfile() -> str:
    """Le Dockerfile sans ses commentaires, continuations jointes : une instruction par ligne.

    Dans cet ordre — mesuré : Docker exécute normalement l'instruction qui suit un commentaire
    terminé par `\\`. Joindre avant de retirer aurait avalé cette instruction.
    """
    return CONTINUATION.sub(" ", COMMENTAIRE.sub("", DOCKERFILE.read_text(encoding="utf-8")))


def _etapes_du_dockerfile() -> list[tuple[str, str | None]]:
    """Chaque `FROM` du Dockerfile : la référence d'image, et le nom d'étape s'il y en a un."""
    return [(m["image"], m["etape"]) for m in INSTRUCTION_FROM.finditer(_dockerfile())]


def _sources_des_copies() -> list[str]:
    """La source de chaque `COPY --from=…` du Dockerfile, dans l'ordre."""
    return COPIE_DEPUIS.findall(_dockerfile())


def _images_tirees_du_compose() -> dict[str, str]:
    """Les images du compose local que Docker **tire**, par nom de service."""
    services: dict[str, dict[str, Any]] = document_yaml(COMPOSE)["services"]
    return {nom: bloc["image"] for nom, bloc in services.items() if "build" not in bloc}


def _sans_empreinte(image: str) -> str:
    """`image:tag`, l'empreinte ôtée — ce qu'un humain compare, ce que le bot fait glisser."""
    return image.split("@", 1)[0]


def _nom_et_tag(image: str) -> tuple[str, str]:
    """(`python`, `3.13-slim`) pour `python:3.13-slim@sha256:…` — et pour ses autres écritures.

    Le nom est le dernier segment (`docker.io/library/python` compris) ; le tag est ce qui suit le
    dernier `:`, sauf si c'est le port d'un registre (`localhost:5000/python`) — alors il n'y a
    pas de tag, et la chaîne vide le dit, plutôt qu'une exception nue.
    """
    reference = _sans_empreinte(image)
    nom, deux_points, tag = reference.rpartition(":")
    if not deux_points or "/" in tag:
        nom, tag = reference, ""
    return nom.rsplit("/", 1)[-1], tag


def test_le_dockerfile_declare_les_etapes_attendues() -> None:
    """Témoin positif des paramétrages sur le Dockerfile — rougit à toute étape ajoutée ou ôtée.

    Par noms d'étapes et non par compte : l'échec dit laquelle manque ou apparaît.
    """
    assert [etape for _, etape in _etapes_du_dockerfile()] == ["uv", "build", None], (
        "témoin : les étapes du Dockerfile ont changé"
    )


def test_le_compose_tire_les_images_attendues() -> None:
    """Témoin positif du compose — rougit à tout service tiré en plus, pour forcer la discussion."""
    assert set(_images_tirees_du_compose()) == {"postgres", "valkey"}, (
        "témoin : les services tirés du compose ont changé"
    )


@pytest.mark.parametrize("image", [image for image, _ in _etapes_du_dockerfile()])
def test_chaque_image_de_base_du_dockerfile_porte_une_empreinte(image: str) -> None:
    assert EMPREINTE.match(image), f"le Dockerfile tire {image!r} sans empreinte"


@pytest.mark.parametrize(("service", "image"), sorted(_images_tirees_du_compose().items()))
def test_chaque_image_tiree_du_compose_porte_une_empreinte(service: str, image: str) -> None:
    assert EMPREINTE.match(image), f"{service} tire {image!r} sans empreinte"


def test_tout_copy_from_nomme_une_etape_du_dockerfile() -> None:
    """Toute source d'un `COPY --from` est une étape nommée de ce Dockerfile — jamais une image.

    Une source qui n'est pas une étape est une image tirée en douce, que Dependabot ne suivra
    jamais. L'inclusion seule : la réciproque (« toute étape nommée est copiée ») interdirait
    l'idiome `AS runtime` sur l'étape finale, dont rien ne copie. Le témoin est le test suivant.
    """
    etapes_nommees = {etape for _, etape in _etapes_du_dockerfile() if etape}
    sources = set(_sources_des_copies())
    assert sources <= etapes_nommees, (
        f"`COPY --from` depuis {sorted(sources - etapes_nommees)} : Dependabot ne les suivra pas"
    )


def test_le_dockerfile_copie_depuis_les_etapes_attendues() -> None:
    """Témoin positif du test précédent — rougit si le motif cesse de lire un `COPY --from`."""
    assert set(_sources_des_copies()) == {"uv", "build"}, (
        "témoin : les sources de `COPY --from` attendues ont changé"
    )


def test_l_image_python_est_celle_que_le_projet_epingle() -> None:
    """`api/.python-version` choisit l'interpréteur ; le Dockerfile ne peut pas en livrer un autre.

    Dependabot proposera `python:3.14-slim` comme il propose une empreinte : ce test rend cette PR
    rouge, pour qu'un humain la tranche en montant les deux fichiers ensemble. L'ensemble vide —
    plus aucun `FROM python` reconnu — est un rouge, pas un vert par défaut.
    """
    assert PYTHON_VERSION.exists(), f"{PYTHON_VERSION.name} manque sous api/ : qui choisit Python ?"
    version = PYTHON_VERSION.read_text(encoding="utf-8").strip()
    versions = {
        tag.split("-", 1)[0]
        for nom, tag in map(_nom_et_tag, (image for image, _ in _etapes_du_dockerfile()))
        if nom == "python"
    }
    assert versions == {version}, (
        f"le Dockerfile livre Python {sorted(versions)}, `api/.python-version` dit {version} : "
        "les monter ensemble"
    )


def test_la_ci_teste_sur_les_images_que_le_compose_fait_tourner() -> None:
    """Mêmes services, même `image:tag` dans les `services:` de la CI et dans le compose local.

    Seul le compose porte l'empreinte, seul lui est suivi par Dependabot ; la CI doit tester sur
    la même chose — sinon les migrations ne sont prouvées sur rien. **Le contrat est une
    égalité**, dans les deux sens : la CI ne cesse pas de lever un service en silence, et le
    compose local ne tire rien que la suite ne teste. Un outil de confort du poste (`adminer`,
    `mailpit`) n'a donc pas sa place ici tel quel : le jour où l'un arrive, Compose a le mot pour
    « pas levé par défaut » — `profiles:` — et c'est cette clé qui l'exclura, comme `build:`
    exclut l'image du paquet. Pas avant.
    """
    jobs = document_yaml(CI)["jobs"]
    assert "ci" in jobs, f"le job de tests de ci.yml ne s'appelle plus `ci` : {sorted(jobs)}"
    assert "services" in jobs["ci"], "le job `ci` ne lève plus aucun service"
    services_de_la_ci = {nom: bloc["image"] for nom, bloc in jobs["ci"]["services"].items()}
    services_du_compose = {
        nom: _sans_empreinte(image) for nom, image in _images_tirees_du_compose().items()
    }
    assert services_de_la_ci == services_du_compose, (
        f"CI {services_de_la_ci} ≠ compose {services_du_compose} : monter les deux ensemble"
    )
