"""Toute image tirée d'un registre est-elle épinglée par empreinte ?

Cadrage §13.10, « Images épinglées par empreinte ». L'invariant est réparti sur deux fichiers que
deux écosystèmes Dependabot différents rafraîchissent — `docker` sur `api/Dockerfile`,
`docker-compose` sur `infra/` — et le bot conserve la forme `tag@sha256:…` ; ce garde vise la main
qui ajoute une image par tag seul, ou qui retire une empreinte pour « débloquer » un build. Aucun
test de code ne peut le voir : les tests parlent aux services, jamais à l'image qui les porte.

Ce qui **n'est pas** tiré n'a pas d'empreinte à porter : un service qui construit son image
(`build:`) la nomme, il ne la tire pas. C'est la clé `build`, pas le nom, qui l'exclut — ainsi le
garde suit une image renommée sans qu'on y pense.
"""

import re
from typing import Any

import pytest
from conftest import COMPOSE, DOCKERFILE
from yaml import safe_load

EMPREINTE = re.compile(r"^\S+:[\w][\w.-]*@sha256:[0-9a-f]{64}$")
"""La forme `image:tag@sha256:<64 hexadécimaux>` : le tag reste, lisible, l'empreinte fige.

Le tag seul est refusé, l'empreinte seule aussi — sans tag, personne ne sait plus ce qu'elle fige,
et Dependabot ne sait plus la suivre.
"""


def _images_tirees_du_compose() -> dict[str, str]:
    """Les images du compose local que Docker **tire**, par nom de service."""
    services: dict[str, dict[str, Any]] = safe_load(COMPOSE.read_text(encoding="utf-8"))["services"]
    return {nom: bloc["image"] for nom, bloc in services.items() if "build" not in bloc}


def _images_de_base_du_dockerfile() -> list[str]:
    """Les références de chaque `FROM` du Dockerfile — toutes tirées, par construction."""
    return re.findall(r"^FROM\s+(\S+)", DOCKERFILE.read_text(encoding="utf-8"), re.MULTILINE)


def test_le_compose_tire_les_images_attendues() -> None:
    """Témoin positif : un paramétrage vide ne rougit jamais. Rougit si un service tiré apparaît."""
    assert set(_images_tirees_du_compose()) == {"postgres", "valkey"}


def test_le_dockerfile_declare_les_etapes_attendues() -> None:
    """Témoin positif : build et exécution sur Python, plus l'étape qui porte `uv`."""
    assert len(_images_de_base_du_dockerfile()) == 3


@pytest.mark.parametrize(("service", "image"), sorted(_images_tirees_du_compose().items()))
def test_chaque_image_tiree_du_compose_porte_une_empreinte(service: str, image: str) -> None:
    assert EMPREINTE.match(image), f"{service} tire {image!r} sans empreinte"


@pytest.mark.parametrize("image", _images_de_base_du_dockerfile())
def test_chaque_image_de_base_du_dockerfile_porte_une_empreinte(image: str) -> None:
    assert EMPREINTE.match(image), f"le Dockerfile tire {image!r} sans empreinte"
