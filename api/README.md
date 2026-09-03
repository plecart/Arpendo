# Arpendo — api

Paquet Python `arpendo_api` : la **couche de services** du jeu, indépendante du transport
(cadrage §12.6), servie aujourd'hui par un hôte HTTP FastAPI et demain, à l'identique, par le
worker — un seul paquet, deux points d'entrée, deux conteneurs (cadrage §13.0).

## Lancer

Deux façons, pour deux besoins.

**La pile complète, en conteneurs** — PostgreSQL 17, Valkey 8, l'api et le worker, décrits par
`infra/docker-compose.yml`. C'est le mode de référence : c'est cette pile que la production
reproduit, à deux écarts près documentés en tête du fichier compose.

```
cp .env.example .env    # une fois, à la racine ; y mettre un VALKEY_PASSWORD
just up
```

Les sources sont montées dans le conteneur `api` et uvicorn tourne en `--reload` : éditer
`src/` recharge le serveur sans rien reconstruire. Un changement de dépendance, lui, demande une
image neuve — `just up` la rebâtit, et ne coûte rien quand rien n'a bougé.

**Le conteneur `worker` monte les mêmes sources mais ne recharge pas** : il n'y a pas d'équivalent
de `--reload` pour une boucle asyncio, et en inventer un serait du code de production qui ne sert
qu'au poste. Après avoir édité une tâche : `just restart-worker`.

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

## Limitation de débit

Chaque requête est comptée dans Valkey, par **dimension** et par clé, en fenêtre fixe. Au-delà du
quota, l'api répond **429** avec un `Retry-After` valant ce qu'il reste de la fenêtre. Aucune route
n'est exemptée : `/health` compte comme les autres, ses quelques sondes par minute étant
négligeables devant le quota — et c'est ce qui en fait l'endpoint réel des tests.

**Ajouter un axe de limitation, c'est ajouter une entrée à `DIMENSIONS`** (`core/rate_limit.py`),
sur le modèle de `PROBES` : un nom, une fonction qui tire la clé de la requête, et deux fonctions
qui lisent le quota et la fenêtre dans les réglages. Le middleware ne les connaît pas et ne change
pas. Une clé `None` veut dire « cet axe ne s'applique pas à cette requête » : elle passe alors sans
être comptée. Seul axe aujourd'hui : `ip`, sous la clé `ratelimit:ip:<adresse>`.

| Réglage | Rôle |
|---|---|
| `RATE_LIMIT_IP_REQUESTS` | requêtes autorisées par adresse et par fenêtre |
| `RATE_LIMIT_IP_WINDOW_SECONDS` | durée de la fenêtre, en secondes |
| `FORWARDED_ALLOW_IPS` | lue par **uvicorn**, pas par `Settings` — voir plus bas |

**Échec ouvert** : Valkey injoignable, la requête passe sans être comptée (cadrage §13.8 — la perte
de Valkey est indolore par conception, et des compteurs remis à zéro sont sans conséquence). Sont
attrapées `ConnectionError` et `TimeoutError` de redis-py — sœurs, l'une n'hérite pas de l'autre,
il faut donc nommer les deux — **et tout ce qui hérite de la première**, dont
`AuthenticationError` : un mot de passe Valkey erroné désarme la limitation. Aucune trace dans les
journaux jusqu'à #42, mais `/health` le dit en répondant 503. Assumé : rejeter chaque requête sur
une erreur de configuration ferait une panne totale là où l'on a un service dégradé et signalé.
Attraper `Exception`, en revanche, désarmerait la limitation au premier bug du limiteur au lieu de
le faire sortir en 500.

### L'adresse comptée, et à qui l'on croit

Le limiteur ne lit **jamais** `X-Forwarded-For`. Il compte `request.client.host`, que le
`ProxyHeadersMiddleware` d'uvicorn — actif par défaut — a déjà remplacé par l'adresse annoncée par
le proxy **si et seulement si** le pair figure dans `FORWARDED_ALLOW_IPS`. Une seule décision, un
seul endroit. Les nuances qui se paient cher :

- **Ne jamais poser `*`.** Il ne se contente pas de faire confiance à tout le monde : il
  **change d'algorithme**. Sous `*`, uvicorn retient le **premier** hôte de la liste — celui de
  gauche, entièrement écrit par le client — et ne le valide même pas comme adresse : un
  `X-Forwarded-For: pas-une-ip` devient tel quel la clé de comptage. Le limiteur est alors à la
  fois contournable (une valeur différente à chaque requête) et une fabrique de clés arbitraires
  qui vivent une fenêtre entière. Le raccourci est tentant quand l'adresse de la passerelle est
  imprévisible ; il désarme la limitation.
- **`*` accompagné n'est pas `*`.** `FORWARDED_ALLOW_IPS=*,10.0.0.1` ne vaut pas « tout le
  monde » : le `*` y devient un nom d'hôte littéral que personne ne porte, et la liste se comporte
  exactement comme `10.0.0.1`. Le raccourci total n'existe que pour `*` **seul**. Une valeur vide,
  elle, ne fait confiance à personne.
- **Hors `*`, l'adresse retenue est le premier hôte non fiable en partant de la droite**, pas le
  premier de la liste. Chaque proxy ajoute à la fin : la droite est le seul bout qu'un client ne
  contrôle pas.
- **La liste accepte les IP, les CIDR et les littéraux.** Une IP mal écrite ne lève rien : elle
  devient un littéral, qui ne correspondra jamais à personne.

**En production**, y poser le réseau de Caddy — périmètre de #45 — et **ne pas s'en remettre au
défaut**. Derrière un reverse proxy dont l'adresse n'est pas déclarée, aucun en-tête n'est cru et
le limiteur compte l'adresse interne de Caddy pour *tous* les joueurs : le quota par adresse
devient un plafond global, « et le premier joueur actif bloquerait les autres » (cadrage §13.7).
Sûr du côté de l'usurpation, dégradé du côté de la disponibilité — pas un état où l'on s'installe.

Dans la pile locale, les requêtes venues de l'hôte atteignent le conteneur avec pour pair la
passerelle du bridge Docker : tout le trafic de la machine partage donc un seul compteur tant
qu'aucun reverse proxy n'est devant. Sans conséquence au quota par défaut.
## Contrôle de version du client

`GET /version` publie les deux seuils que l'application mobile interroge **avant tout autre appel**
(spec UX §2.1, étape 1). Route **publique**, à la racine et non sous `/v1` : elle précède la
session, et un client qui doit apprendre qu'il est trop vieux pour parler à `/v1` ne peut pas être
obligé de connaître `/v1` pour le demander — la même raison qui garde `/health` à la racine.

```
GET /version  →  200  {"min_build": 1, "recommended_build": 1}
```

| Réglage | Rôle |
|---|---|
| `CLIENT_BUILD_MIN` | `build < min` → l'app affiche un écran bloquant vers le magasin, sans retour ni fermeture (cadrage §14.1, spec UX §11.2) |
| `CLIENT_BUILD_RECOMMENDED` | `build < recommended` → bandeau fermable, priorité 12 (spec UX §2.4) |

Les deux comparaisons sont **strictes** : un build égal à un seuil l'atteint. Les deux réglages
sont des **numéros de build** — l'entier monotone de `version: x.y.z+N` du manifeste de l'app,
jamais du semver : c'est le seul champ dont l'ordre est total et déjà garanti par le magasin.

**Le serveur ne rend aucun verdict.** Il annonce ses seuils ; c'est l'app qui compare. Lui faire
lire `X-Client-Version` pour répondre « à jour / obsolète » couplerait la route à l'en-tête et
priverait l'app de la connaissance de sa cible — elle ne saurait plus quoi afficher. Un test le
garde, et il rougit si la comparaison est rapatriée ici.

**`CLIENT_BUILD_MIN <= CLIENT_BUILD_RECOMMENDED` est vérifié au démarrage**, par un validateur de
modèle de `Settings` : chaque seuil est valide pris seul, c'est leur ordre qui ne l'est pas. Un
`.env` inversé refuse de démarrer, comme un secret manquant — sans quoi l'incident serait invisible
côté serveur, la route répondant 200.

## Le worker

**Un seul paquet, deux points d'entrée** (cadrage §13.0) : l'api HTTP et le worker sont deux hôtes
de la même couche de services. Même image, commande différente, **conteneur distinct** — ils ne
fusionnent jamais, parce qu'une tâche planifiée ne doit s'exécuter qu'une fois quel que soit le
nombre d'instances HTTP (§13.9 règle 2).

```
python -m arpendo_api.worker
```

Il ouvre les ressources partagées par le même `open_resources` que l'api, déroule sa table de
tâches, et s'arrête sur SIGTERM en libérant tout.

**Contrairement à l'api, il ne se lance pas sur un poste Windows** : son fichier de battement est
un chemin POSIX absolu (`/tmp/…`). C'est voulu — ce chemin est le seul qui restera inscriptible
quand #45 posera un système de fichiers en lecture seule.

**Un tour de tâche qui échoue ne fait pas tomber le worker** : le tour est perdu, l'erreur part sur
le journal de la stdlib (que #42 configurera) en nommant la tâche fautive, et le tour suivant
repart. Plusieurs joueurs dépendent de ce processus — l'échec d'une purge sur un hoquet de la base
est un incident local, pas une raison de priver tout le monde des autres tâches.

**Le prix de cette règle, à connaître** : une tâche définitivement cassée boucle et journalise sans
fin, et le conteneur **reste `healthy`** — le battement est une entrée distincte de la table, il
continue de battre. Un healthcheck vert dit que le worker tourne, pas que ses tâches réussissent ;
c'est le journal qui le dit.

**Ajouter une tâche planifiée, c'est ajouter une entrée à `TASKS`** — un nom, un intervalle, une
coroutine qui reçoit les ressources :

```python
TASKS: Mapping[str, tuple[float, Task]] = {"battement": (HEARTBEAT_INTERVAL, _heartbeat)}
```

Ni la boucle, ni l'ouverture des ressources, ni l'arrêt n'ont à changer. Chaque entrée tourne dans
sa **propre tâche asyncio**, réunies par un `TaskGroup` : une tâche lente n'en retarde aucune
autre, et si l'une venait à lever malgré la garde ci-dessus, les autres sont annulées plutôt que
laissées à tourner sur des ressources déjà fermées. L'attente entre deux tours porte sur
l'**événement d'arrêt** et non sur le temps — sans quoi un `docker compose stop` devrait patienter
jusqu'au prochain réveil, ce qui deviendra insupportable à la première tâche horaire.

Une seule tâche à la naissance : le **battement**, qui repose toutes les 10 secondes la date de
`/tmp/arpendo-worker-battement`. Le fichier n'a pas de contenu — c'est sa date que lit la sonde
du conteneur. Les tâches réelles (fin de partie, purges de rétention, bilans du flux, envoi des push)
arrivent avec les domaines Territoire et Flux.

**L'arrêt passe par `signal.signal`, jamais par `loop.add_signal_handler`** : le second lève
`NotImplementedError` sous Windows, où ce projet se développe. Le gestionnaire s'exécute hors du
contrôle de la boucle, donc il ne touche pas l'événement directement — `call_soon_threadsafe` est
le seul pont sûr.

## Migrations

Le schéma est versionné par Alembic, configuré dans le `[tool.alembic]` de `pyproject.toml` — pas
d'`alembic.ini` : l'URL vient de `Settings`, comme pour l'application. Les scripts vivent sous
`src/arpendo_api/db/migrations/`, donc entrent dans l'image par le `COPY src` du Dockerfile.

| Faire | Commande |
|---|---|
| Écrire une migration | `just migration "ce qu'elle change"` — autogénérée par comparaison des modèles au schéma réel |
| La relire | **obligatoire avant commit** : l'autogénération ne voit ni les renommages ni les données. Écrire la docstring, retirer les balises « auto generated ». |
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
- `src/arpendo_api/worker/` — le **second point d'entrée** : la boucle de tâches périodiques et
  son point d'entrée `python -m arpendo_api.worker`.
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
