# Arpendo — api

Paquet Python `arpendo_api` : la **couche de services** du jeu, indépendante du transport
(cadrage §12.6), servie aujourd'hui par un hôte HTTP FastAPI et demain, à l'identique, par le
worker — un seul paquet, deux points d'entrée, deux conteneurs (cadrage §13.0).

## Lancer

Prérequis : `uv` (il installe seul le Python épinglé dans `.python-version`).

```
just install-api
cd api && uv run uvicorn arpendo_api.main:create_app --factory --reload
```

`GET http://localhost:8000/health` répond `{"status": "ok"}`.

## Tester et vérifier

| Commande | Rôle |
|---|---|
| `just test-api` | suite complète avec couverture, seuil 85 % |
| `just test-one tests/test_health.py` | une seule cible, pour la boucle TDD |
| `just lint-api` | `ruff check` |
| `just fmt-api` / `just fmt-check-api` | `ruff format` |
| `just typecheck` | `mypy --strict` sur `src/` |

Les tests HTTP passent par la fixture `client` de `tests/conftest.py` : un `httpx.AsyncClient`
branché sur `create_app()` sans réseau. Les tests asynchrones n'ont besoin d'aucun marqueur
(`asyncio_mode = "auto"`).

## Structure

- `src/arpendo_api/main.py` — `create_app()`, la fabrique de l'hôte HTTP. Les routeurs des
  domaines s'y ajoutent sous `/v1` ; `/health` et `/version` restent à la racine.
- `src/arpendo_api/core/` — le transversal (santé, puis réglages, garde-fous…).
- `src/arpendo_api/domains/` — un paquet par domaine métier, créé avec le premier.
