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
`src/` recharge le serveur sans rien reconstruire. Un changement de dépendance, lui, demande une
image neuve — `just up` la rebâtit, et ne coûte rien quand rien n'a bougé.

**L'api seule, sur le poste** — pour attacher un débogueur ou un profileur au processus.

```
just install-api
cd api && uv run --env-file ../.env uvicorn arpendo_api.main:create_app --factory --reload
```

`--env-file` n'est pas décoratif : `Settings` ne lit que l'environnement (cadrage §13.9 règle 5) et
n'ouvre aucun fichier. Partout ailleurs c'est le justfile qui charge le `.env` de la racine — ici on
est hors justfile, donc sans ce drapeau l'api s'arrête sur `database_url Field required`.

Dans les deux cas, `GET http://localhost:8000/health` répond **200**
`{"status": "ok", "postgres": "ok", "valkey": "ok"}`, ou **503** avec `"status": "degraded"` et
la dépendance fautive marquée `"unreachable"` — le verdict pour un moniteur d'uptime, le détail
pour la personne qui diagnostique. Un service absent se constate en quelques millisecondes : les
clients échouent vite plutôt que d'épuiser le budget de la sonde.

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
branché sur l'application sans réseau. La chaîne est `settings` → `app` → `client`, et c'est
`app` qui **entre réellement dans le cycle de vie** : `ASGITransport` ne le déclenche pas, donc
sans ce contexte les tests parleraient à une application sans moteur ni client Valkey — en
silence. Un test qui veut un environnement dégradé surcharge `settings` par paramétrisation
indirecte et hérite du reste de la chaîne, comme le fait le test « Valkey injoignable ».
Les tests asynchrones n'ont besoin d'aucun marqueur (`asyncio_mode = "auto"`).

## Structure

- `src/arpendo_api/main.py` — `create_app()`, la fabrique de l'hôte HTTP. Les routeurs des
  domaines s'y ajoutent sous `/v1` ; `/health` reste à la racine, parce qu'il s'adresse aux
  sondes et non aux clients.
- `src/arpendo_api/core/` — le transversal : `settings.py` (la seule lecture de
  l'environnement du paquet), `valkey.py`, `health.py`.
- `src/arpendo_api/db/` — la persistance : `engine.py` aujourd'hui, le schéma et les sessions
  ensuite.
- `src/arpendo_api/domains/` — un paquet par domaine métier, créé avec le premier.

**Les réglages sensibles sont des `Secret`** — le mot de passe Valkey et l'URL de base, qui porte
celui de PostgreSQL. Les afficher, les journaliser ou les sérialiser rend `SecretStr('**********')`
et rien d'autre ; la valeur ne sort que par un `.get_secret_value()` explicite, dans la seule
fabrique qui la consomme. Un futur secret — clé de session, DSN Sentry, jeton FCM — se déclare
avec le même alias.

**Les ressources partagées sont ouvertes par le cycle de vie et rangées dans `app.state`** : leur
durée de vie est exactement celle de l'application, et deux applications de test n'en partagent
jamais une. Chacune est empilée sur un `AsyncExitStack` dès sa naissance, donc libérée même si la
suivante échoue à naître ou si une fermeture lève. Ajouter une ressource, c'est deux lignes dans
le cycle de vie — la créer, l'empiler.

**Ajouter une dépendance à `/health`, c'est ajouter une entrée à `PROBES`** — la table de module
qui associe un nom de réponse à un aller-retour vers la dépendance. La route ne nomme aucune
dépendance : elle parcourt la table. Ni le verdict, ni le code de statut, ni le format de réponse
ne bougent, et un test le vérifie en ajoutant une sonde de son cru.
