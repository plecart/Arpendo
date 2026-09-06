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
familles paramétrées ont un témoin séparé ; les trois autres tests sont écrits en une égalité
d'ensembles, où l'ensemble vide est un rouge.
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

CONTINUATION = re.compile(r"\\\r?\n\s*")
"""Un `\\` en fin de ligne : Docker lit la suite comme la même instruction, ces motifs aussi."""


def _dockerfile() -> str:
    """Le Dockerfile, continuations (`\\` en fin de ligne) jointes : une instruction par ligne."""
    return CONTINUATION.sub(" ", DOCKERFILE.read_text(encoding="utf-8"))


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


def _nom(image: str) -> str:
    """Le dernier segment du nom : `python`, qu'il soit écrit nu ou `docker.io/library/python`."""
    return _sans_empreinte(image).rsplit(":", 1)[0].rsplit("/", 1)[-1]


def _tag(image: str) -> str:
    """Le tag seul : `3.13-slim` pour `python:3.13-slim@sha256:…`."""
    return _sans_empreinte(image).rsplit(":", 1)[1]


def test_le_dockerfile_declare_les_etapes_attendues() -> None:
    """Témoin positif des paramétrages sur le Dockerfile — rougit à toute étape ajoutée ou ôtée.

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


def test_tout_copy_from_nomme_une_etape_du_dockerfile() -> None:
    """Les sources des `COPY --from` sont exactement les étapes nommées — dans les deux sens.

    Une source qui n'est pas une étape est une image tirée en douce, que Dependabot ne suivra
    jamais ; une étape nommée dont rien ne copie est morte. Et si le motif cessait de lire les
    `COPY`, l'ensemble vide rougirait : le témoin est dans l'égalité.
    """
    etapes_nommees = {etape for _, etape in _etapes_du_dockerfile() if etape}
    assert set(_sources_des_copies()) == etapes_nommees


def test_l_image_python_est_celle_que_le_projet_epingle() -> None:
    """`api/.python-version` choisit l'interpréteur ; le Dockerfile ne peut pas en livrer un autre.

    Dependabot proposera `python:3.14-slim` comme il propose une empreinte : ce test rend cette PR
    rouge, pour qu'un humain la tranche en montant les deux fichiers ensemble. L'ensemble vide —
    plus aucun `FROM python` reconnu — est un rouge, pas un vert par défaut.
    """
    version = PYTHON_VERSION.read_text(encoding="utf-8").strip()
    versions = {
        _tag(image).split("-", 1)[0]
        for image, _ in _etapes_du_dockerfile()
        if _nom(image) == "python"
    }
    assert versions == {version}, (
        f"le Dockerfile livre Python {sorted(versions)}, `api/.python-version` dit {version} : "
        "les monter ensemble"
    )


def test_la_ci_teste_sur_les_images_que_le_compose_fait_tourner() -> None:
    """Mêmes services, même `image:tag` dans les `services:` de la CI et dans le compose local.

    Seul le compose porte l'empreinte, seul lui est suivi par Dependabot ; la CI doit tester sur
    la même chose — sinon les migrations ne sont prouvées sur rien. L'égalité tient les deux
    sens : un service que la CI cesserait de lever, ou que le compose tirerait sans que la CI le
    connaisse, est une discussion à avoir, pas un vert.
    """
    jobs = document_yaml(CI)["jobs"]
    assert "ci" in jobs, f"le job de tests de ci.yml ne s'appelle plus `ci` : {sorted(jobs)}"
    services_de_la_ci = {nom: bloc["image"] for nom, bloc in jobs["ci"]["services"].items()}
    services_du_compose = {
        nom: _sans_empreinte(image) for nom, image in _images_tirees_du_compose().items()
    }
    assert services_de_la_ci == services_du_compose
