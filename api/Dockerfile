# Image de l'api. Multi-étapes : l'outillage de build (uv, cache de roues) reste dans la première
# étape et ne pèse pas sur l'image livrée. Utilisateur non privilégié — cadrage §13.10,
# « Jamais de conteneur applicatif en root ».
#
# Chaque image tirée est épinglée `tag@sha256:…` (§13.10, « Images épinglées par empreinte ») :
# le tag dit ce qu'on a voulu, l'empreinte fige ce qu'on a eu. Dependabot (écosystème `docker`
# sur `/api`) suit le tag et propose l'empreinte suivante quand il bouge — et son parseur ne lit
# que les lignes `FROM`, écrites en clair : chaque écart à cette forme est justifié sur place. Le
# commentaire de chaque épinglage nomme la version que le tag résolvait le jour où elle a été lue.
# `api/tests/test_images.py` refuse un `FROM` sans empreinte.

# uv installe les dépendances sur l'interpréteur de l'image de base ; sa propre image officielle
# évite une couche pip.
# Étape nommée, et non `COPY --from=<image>` : c'est ce qui met l'empreinte sur une ligne `FROM`,
# la seule que Dependabot lise. L'image ne contient que le binaire, l'étape ne construit rien.
# ghcr.io/astral-sh/uv:0.12 → uv 0.12.10 (lu le 6 septembre 2026).
FROM ghcr.io/astral-sh/uv:0.12@sha256:2bb3ebca0a796a155094a27773d290c4b074572e6107f171d88d086682fd2500 AS uv

# python:3.13-slim → Python 3.13.15 (lu le 6 septembre 2026).
FROM python:3.13-slim@sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285 AS build

COPY --from=uv /uv /usr/local/bin/uv

# `COMPILE_BYTECODE` paie le coût du .pyc une fois au build plutôt qu'au premier appel de chaque
# module. `LINK_MODE=copy` : le cache d'uv et /app ne sont pas sur le même montage, les liens durs
# échoueraient.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# Deux `sync` plutôt qu'un : le premier ne dépend que du manifeste et du verrou, donc sa couche
# — la plus lourde et la plus lente — est réutilisée tant qu'aucune dépendance ne bouge. Éditer
# `src/` ne réinstalle rien.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY src ./src
RUN uv sync --locked --no-dev

# Même image et même empreinte que l'étape `build`, écrites deux fois : un `ARG` les
# factoriserait, mais Dependabot ne résout pas les `ARG` et cesserait de les suivre. Le bot les
# monte ensemble, dans la même PR, puisque c'est la même dépendance.
# python:3.13-slim → Python 3.13.15 (lu le 6 septembre 2026).
FROM python:3.13-slim@sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285

# `--system` : pas de mot de passe, pas d'expiration. Le shell est refusé — ce compte sert à
# exécuter un processus, jamais à ouvrir une session.
RUN useradd --system --create-home --shell /usr/sbin/nologin arpendo

WORKDIR /app
# Sans `--chown` : code et venv appartiennent à root, l'utilisateur d'exécution les lit et les
# exécute, il n'y écrit pas — rien ici n'en a besoin, le worker écrit sous `/tmp`. Le job `image`
# de la CI le vérifie par un `touch` qui doit échouer.
COPY --from=build /app /app

# Met le venv en tête du PATH : `uvicorn` et `python` résolvent vers l'environnement du projet
# sans avoir à préfixer chaque commande.
ENV PATH="/app/.venv/bin:$PATH"

USER arpendo
EXPOSE 8000

# La sonde vit dans l'image, pas dans un fichier compose : elle vaut pour `api` dans tous les
# environnements. Seul le `worker`, qui n'écoute sur aucun port, la remplace dans chaque compose
# par la fraîcheur de son fichier de battement. Pas de `curl` à installer — la stdlib fait
# l'appel, et un `/health` en 503 lève une `HTTPError`, donc marque le conteneur `unhealthy`.
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "arpendo_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
