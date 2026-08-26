# Arpendo — api

Paquet Python `arpendo_api` : la **couche de services** du jeu, indépendante du transport
(cadrage §12.6), servie aujourd'hui par un hôte HTTP FastAPI et demain, à l'identique, par le
worker — un seul paquet, deux points d'entrée, deux conteneurs (cadrage §13.0).

## Lancer

Deux façons, pour deux besoins.

**La pile complète, en conteneurs** — PostgreSQL 17, Valkey 8 et l'api, décrits par
`infra/docker-compose.yml`. C'est le mode de référence : c'est cette pile que la production
reproduit, à deux écarts près documentés en tête du fichier compose.

```
cp .env.example .env    # une fois, à la racine ; y mettre un VALKEY_PASSWORD
just up
```

Les sources sont montées dans le conteneur `api` et uvicorn tourne en `--reload` : éditer
`src/` recharge le serveur, sans reconstruire l'image. Rebâtir n'est nécessaire qu'après un
changement de dépendance (`docker compose -f infra/docker-compose.yml --env-file .env build api`).

**L'api seule, sur le poste** — pour attacher un débogueur ou un profileur au processus.

```
just install-api
cd api && uv run uvicorn arpendo_api.main:create_app --factory --reload
```

Dans les deux cas, `GET http://localhost:8000/health` répond `{"status": "ok"}`.

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
