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

## Sessions

Une route qui a besoin de la base annote son paramètre — l'injection fait le reste :

```python
from arpendo_api.db.session import Session


@router.post("/v1/quelque-chose")
async def creer(session: Session) -> Reponse:
    session.add(objet)
    await session.commit()  # explicite, par l'appelant
    return Reponse(...)
```

**La dépendance ne commet jamais à la sortie.** Committer là persisterait la moitié d'une unité de
travail quand une erreur survient à mi-chemin : l'appelant recevrait une erreur *et* la base
garderait un état partiel. C'est donc la route qui commet, au moment où elle sait son travail
complet ; ce qui n'a pas été commis est annulé à la fermeture de la session. Deux tests le
prouvent — l'un en vérifiant qu'une requête sans `commit` ne laisse rien, l'autre qu'un `commit`
explicite persiste.

**Une session par requête**, tirée du `async_sessionmaker` que le cycle de vie range dans
`app.state` — jamais un second moteur. `expire_on_commit=False` : sinon le premier attribut lu
après un `commit` déclencherait un rechargement, impossible à attendre en async, et une réponse
HTTP est sérialisée *après* le commit.

## Événements et bus

Le journal d'événements de domaine (§12.6) a deux faces. `DomainEvent` est **la ligne** — ce que
PostgreSQL garde, source de l'audit, du débogage et du flux d'activité. `Event` est **le type** —
une base Pydantic dont chaque sous-classe déclare son identifiant :

```python
from typing import ClassVar

from arpendo_api.core.journal import Event


class TileCaptured(Event):
    type: ClassVar[str] = "tile.captured"

    tile: int
```

Déclarer la sous-classe suffit : elle s'inscrit au registre `EVENTS` sous son identifiant, et c'est
ce registre qui permet de rendre à un message reçu la classe qui l'a produit. Deux classes sous le
même identifiant lèvent à la déclaration — sinon la seconde remplacerait la première en silence et
les abonnés décoderaient dans la mauvaise classe. Les identifiants sont **en anglais, pointés**,
`entité.participe` : ils sont stockés en colonne, donc soumis à la règle des identifiants
techniques. Le MVP n'en livre encore aucun ; le premier vient avec le domaine Partie.

**`publish` journalise, commet, puis diffuse — dans cet ordre.**

```python
from arpendo_api.core.bus import publish

await publish(session, valkey, TileCaptured(game_id=partie, tile=42))
```

C'est `publish` qui **clôt l'unité de travail** : la garantie « rien n'est diffusé qui ne soit
journalisé » est la séquence de ses awaits, et non une discipline laissée à l'appelant. Il est
variadique — un fait de domaine en produit parfois plusieurs, et un lot, c'est un commit et N
messages, dans l'ordre de l'appel. Un objet qui n'est pas l'instance d'une sous-classe inscrite est
refusé **avant la première écriture**. Un événement **sans partie** est journalisé et jamais
publié : il n'a pas de canal. En retour, chaque instance reçoit l'`id` et l'`occurred_at` de sa
ligne commise — le premier deviendra le `Last-Event-ID` de la SSE.

**`subscribe` est un gestionnaire de contexte**, et pas une simple fabrique d'itérateur :

```python
from arpendo_api.core.bus import subscribe

async with subscribe(valkey, partie) as flux:
    async for evenement in flux:
        ...
```

À l'entrée, il attend la **confirmation d'abonnement du serveur** : `PubSub.subscribe()` n'écrit
que sur la socket sans lire la réponse, et publier aussitôt après risque de partir avant que le
serveur n'ait enregistré l'abonné — mesuré, sans l'attente il ne l'avait enregistré que 12 fois sur
30 — sans que rien ne le signale. À la sortie, il ferme le `PubSub` et rend sa connexion. Un
canal par partie (`game:<uuid>`), composé à un seul endroit. Un message d'un type que ce processus
ne connaît pas est **sauté** — un producteur plus récent ne doit pas faire perdre à l'abonné les
messages qu'il sait lire — tandis qu'une clé inattendue dans la charge utile fait lever : le fil
reste une frontière.

**Aucune reconnexion écrite ici, aucune lecture rejouée** : une coupure remonte à l'appelant. Le
cadrage §13.8 la pose comme indolore par conception — l'appelant se réabonne, le journal a tout
gardé. Un serveur injoignable se constate dès l'entrée du contexte, pas à la première lecture.

## Migrations

Le schéma est versionné par Alembic, configuré dans le `[tool.alembic]` de `pyproject.toml` — pas
d'`alembic.ini` : l'URL vient de `Settings`, comme pour l'application. Les scripts vivent sous
`src/arpendo_api/db/migrations/`, donc entrent dans l'image par le `COPY src` du Dockerfile.

| Faire | Commande |
|---|---|
| Écrire une migration | `just migration "ce qu'elle change"` — autogénérée par comparaison des modèles au schéma réel |
| La relire | **obligatoire avant commit** : l'autogénération ne voit ni les renommages ni les données. Écrire la docstring, retirer les balises « auto generated ». Zone sensible « migrations de schéma » |
| L'appliquer sur le poste | `just migrate` |
| L'appliquer dans un conteneur éphémère | `docker compose -f infra/docker-compose.yml --env-file .env run --rm api alembic upgrade head` — c'est ce que la CI de déploiement déclenchera (cadrage §13.9 règle 3) |

**`just migrate` ne dit rien quand il travaille** : les messages « Running upgrade … » passent par
le logger d'Alembic, qu'aucun handler ne configure — le logging est le sujet de #42, et un
`alembic.ini` n'existe pas ici. **Le code de retour est le signal** ; pour voir l'état,
`just migrate && cd api && uv run alembic current`.

**Jamais au démarrage** : rien dans `main.py` n'appelle Alembic. Une migration se joue une fois,
hors du cycle de vie des conteneurs.

**Chaque migration est prouvée réversible** : `tests/test_migrations.py` joue
`upgrade head → downgrade base → upgrade head` sur le PostgreSQL de l'environnement, dans la suite
ordinaire — en CI comme sur le poste. La fixture `schema` de `conftest.py` monte le schéma à
`head` avant la suite : `just test` après `just up` ne demande aucune étape manuelle. Elle est
synchrone parce que `env.py` appelle `asyncio.run()`, qui refuse une boucle déjà en cours.

**Ajouter un domaine, c'est ajouter son module de modèles aux imports de `env.py`** : une table
qu'aucun import n'a enregistrée dans `Base.metadata` passe pour supprimée.

## Structure

- `src/arpendo_api/main.py` — `create_app()`, la fabrique de l'hôte HTTP. Les routeurs des
  domaines s'y ajoutent sous `/v1` ; `/health` reste à la racine, parce qu'il s'adresse aux
  sondes et non aux clients.
- `src/arpendo_api/core/` — le transversal : `settings.py` (la seule lecture de
  l'environnement du paquet), `valkey.py`, `health.py`, `journal.py` (la ligne, le type, le
  registre), `bus.py` (`publish` / `subscribe`), `resources.py` (les ressources partagées et leur
  cycle de vie).
- `src/arpendo_api/db/` — la persistance : `engine.py` (le moteur), `base.py` (la base
  déclarative et les conventions de schéma — sa docstring en est la référence), `session.py` (la
  session par requête), `migrations/` (Alembic).
- `src/arpendo_api/domains/` — un paquet par domaine métier, créé avec le premier.

**Les réglages sensibles sont des `Secret`** — le mot de passe Valkey et l'URL de base, qui porte
celui de PostgreSQL. Les afficher, les journaliser ou les sérialiser rend `SecretStr('**********')`
et rien d'autre ; la valeur ne sort que par un `.get_secret_value()` explicite, dans la seule
fabrique qui la consomme. Un futur secret — clé de session, DSN Sentry, jeton FCM — se déclare
avec le même alias.

**Les ressources partagées — moteur, fabrique de sessions, client Valkey — sont ouvertes par
`core/resources.py`**, et par personne d'autre. `open_resources(settings)` les empile sur un
`AsyncExitStack` dès leur naissance, donc chacune est libérée même si la suivante échoue à naître
ou si une fermeture lève. **Ajouter une ressource, c'est deux lignes là-bas** — la créer, l'empiler
— au bon rang : l'ordre de création est celui des dépendances, l'ordre de libération s'en déduit.

Le module ignore FastAPI, et c'est ce qui compte : les **deux points d'entrée du paquet** (§13.0)
l'appelleront, l'hôte HTTP depuis son cycle de vie et le worker, quand il naîtra, depuis sa boucle.
Le cycle de vie HTTP ne fait que consommer le résultat et le ranger dans `app.state`, dont la durée
de vie est exactement celle de l'application — deux applications de test n'y partagent jamais une
ressource. C'est là que les sondes de `/health` et la session par requête vont les chercher.

**Ajouter une dépendance à `/health`, c'est ajouter une entrée à `PROBES`** — la table de module
qui associe un nom de réponse à un aller-retour vers la dépendance. La route ne nomme aucune
dépendance : elle parcourt la table. Ni le verdict, ni le code de statut, ni le format de réponse
ne bougent, et un test le vérifie en ajoutant une sonde de son cru.
