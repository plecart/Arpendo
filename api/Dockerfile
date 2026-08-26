# Image de l'api. Multi-étapes : l'outillage de build (uv, cache de roues) reste dans la première
# étape et ne pèse pas sur l'image livrée. Utilisateur non privilégié — cadrage §13.10,
# « Jamais de conteneur applicatif en root ».
#
# Épinglage par TAG de version, pas par empreinte : le §13.10 vise l'empreinte, #45 la posera en
# même temps que `read_only`, `cap_drop`, les limites de ressources et le scan d'images. Un digest
# isolé ici, sans le reste du durcissement, donnerait l'illusion que le sujet est traité.

FROM python:3.13-slim AS build

# uv installe l'interpréteur et les dépendances ; sa propre image officielle évite une couche pip.
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv

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

FROM python:3.13-slim

# `--system` : pas de mot de passe, pas d'expiration. Le shell est refusé — ce compte sert à
# exécuter un processus, jamais à ouvrir une session.
RUN useradd --system --create-home --shell /usr/sbin/nologin arpendo

WORKDIR /app
COPY --from=build --chown=arpendo:arpendo /app /app

# Met le venv en tête du PATH : `uvicorn` et `python` résolvent vers l'environnement du projet
# sans avoir à préfixer chaque commande.
ENV PATH="/app/.venv/bin:$PATH"

USER arpendo
EXPOSE 8000

# La sonde vit dans l'image, pas dans un fichier compose : elle vaut pour tous les environnements
# et #45 n'aura pas à la redéclarer. Pas de `curl` à installer — la stdlib fait l'appel, et un
# `/health` en 503 lève une `HTTPError`, donc marque le conteneur `unhealthy`.
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "arpendo_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
