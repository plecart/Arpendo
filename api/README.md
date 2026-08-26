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

**`just test` exige `just up`.** Les tests parlent à un vrai PostgreSQL et à un vrai Valkey,
jamais à des doubles : une connexion simulée ne prouverait rien de ce que cette configuration
existe pour garantir. Ils lisent leurs coordonnées dans le `.env` de la racine, que le justfile
charge dans l'environnement des recettes. En CI, ce sont les conteneurs `services:` du workflow
et les variables du job qui jouent ce rôle — le même code, sans `.env`.

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
- `src/arpendo_api/core/` — le transversal : `settings.py` (la seule lecture de
  l'environnement du paquet), `valkey.py`, `health.py`.
- `src/arpendo_api/db/` — la persistance : `engine.py` aujourd'hui, le schéma et les sessions
  ensuite.
- `src/arpendo_api/domains/` — un paquet par domaine métier, créé avec le premier.

Le moteur et le client Valkey sont ouverts par le cycle de vie de l'application et rangés dans
`app.state` : leur durée de vie est exactement celle de l'application, et deux applications de
test n'en partagent jamais un.
