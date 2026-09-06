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
- les images des `services:` de `ci.yml`, qu'aucun écosystème ne suit : la CI doit tester sur la
  majeure que le compose fait tourner (§13.6), et seul un test peut tenir les deux à égalité.

Ce qui **n'est pas** tiré n'a pas d'empreinte à porter : un service qui construit son image
(`build:`) la nomme, il ne la tire pas. C'est la clé `build`, pas le nom, qui l'exclut — ainsi le
garde suit une image renommée sans qu'on y pense.
"""

import re
from typing import Any

import pytest
from conftest import CI, DOCKERFILE, PYTHON_VERSION, document_du_compose
from yaml import safe_load

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


def _etapes_du_dockerfile() -> list[tuple[str, str | None]]:
    """Chaque `FROM` du Dockerfile : la référence d'image, et le nom d'étape s'il y en a un."""
    texte = DOCKERFILE.read_text(encoding="utf-8")
    return [(m["image"], m["etape"]) for m in INSTRUCTION_FROM.finditer(texte)]


def _sources_des_copies() -> list[str]:
    """La source de chaque `COPY --from=…` du Dockerfile, dans l'ordre."""
    return COPIE_DEPUIS.findall(DOCKERFILE.read_text(encoding="utf-8"))


def _images_tirees_du_compose() -> dict[str, str]:
    """Les images du compose local que Docker **tire**, par nom de service."""
    services: dict[str, dict[str, Any]] = document_du_compose()["services"]
    return {nom: bloc["image"] for nom, bloc in services.items() if "build" not in bloc}


def _images_des_services_de_la_ci() -> dict[str, str]:
    """Les images `services:` du job de tests de la CI, par nom de service."""
    services: dict[str, dict[str, Any]] = safe_load(CI.read_text(encoding="utf-8"))["jobs"]["ci"][
        "services"
    ]
    return {nom: bloc["image"] for nom, bloc in services.items()}


def _sans_empreinte(image: str) -> str:
    """`image:tag`, l'empreinte ôtée — ce qu'un humain compare, ce que le bot fait glisser."""
    return image.split("@", 1)[0]


def test_le_dockerfile_declare_les_etapes_attendues() -> None:
    """Témoin positif : un paramétrage vide ne rougit jamais. Rougit à toute étape ajoutée ou ôtée.

    Par noms d'étapes et non par compte : l'échec dit laquelle manque ou apparaît.
    """
    assert [etape for _, etape in _etapes_du_dockerfile()] == ["uv", "build", None]


def test_le_compose_tire_les_images_attendues() -> None:
    """Témoin positif du compose — rougit à tout service tiré en plus, pour forcer la discussion."""
    assert set(_images_tirees_du_compose()) == {"postgres", "valkey"}


@pytest.mark.parametrize("image", [image for image, _ in _etapes_du_dockerfile()])
def test_chaque_image_de_base_du_dockerfile_porte_une_empreinte(image: str) -> None:
    assert EMPREINTE.match(image), f"le Dockerfile tire {image!r} sans empreinte"


@pytest.mark.parametrize(("service", "image"), sorted(_images_tirees_du_compose().items()))
def test_chaque_image_tiree_du_compose_porte_une_empreinte(service: str, image: str) -> None:
    assert EMPREINTE.match(image), f"{service} tire {image!r} sans empreinte"


@pytest.mark.parametrize("source", _sources_des_copies())
def test_tout_copy_from_nomme_une_etape_du_dockerfile(source: str) -> None:
    """Une image copiée sans passer par un `FROM` échappe à Dependabot : figée pour toujours."""
    etapes = {etape for _, etape in _etapes_du_dockerfile()}
    assert source in etapes, f"`COPY --from={source}` tire une image que Dependabot ne suivra pas"


@pytest.mark.parametrize(
    "image", [image for image, _ in _etapes_du_dockerfile() if image.startswith("python:")]
)
def test_l_image_python_est_celle_que_le_projet_epingle(image: str) -> None:
    """`api/.python-version` choisit l'interpréteur ; le Dockerfile ne peut pas en livrer un autre.

    Dependabot proposera `python:3.14-slim` comme il propose une empreinte : ce test rend cette PR
    rouge, pour qu'un humain la tranche en montant les deux fichiers ensemble.
    """
    tag = _sans_empreinte(image).split(":", 1)[1]
    assert tag.split("-", 1)[0] == PYTHON_VERSION, (
        f"le Dockerfile livre {image!r}, `api/.python-version` dit {PYTHON_VERSION} : "
        "les monter ensemble"
    )


@pytest.mark.parametrize(("service", "image_ci"), sorted(_images_des_services_de_la_ci().items()))
def test_la_ci_teste_sur_la_majeure_que_le_compose_fait_tourner(
    service: str, image_ci: str
) -> None:
    """Même `image:tag` des deux côtés ; seul le compose porte l'empreinte, seul lui est suivi."""
    image_compose = _images_tirees_du_compose()[service]
    assert _sans_empreinte(image_compose) == image_ci, (
        f"{service} : {image_compose!r} dans le compose, {image_ci!r} dans les services de la CI"
    )
