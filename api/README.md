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
journaux jusqu'à #42, mais `/health` le dit en répondant 503. Assumé : rejeter chaque requête sur une erreur de
configuration ferait une panne totale là où l'on a un service dégradé et bruyamment signalé.
Attraper `Exception`, en revanche, désarmerait la limitation au premier bug du limiteur au lieu de
le faire sortir en 500.

### L'adresse comptée, et à qui l'on croit

Le limiteur ne lit **jamais** `X-Forwarded-For`. Il compte `request.client.host`, que le
`ProxyHeadersMiddleware` d'uvicorn — actif par défaut — a déjà remplacé par l'adresse annoncée par
le proxy **si et seulement si** le pair figure dans `FORWARDED_ALLOW_IPS`. Une seule décision, un
seul endroit. Trois nuances qui se paient cher :

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
  l'environnement du paquet), `valkey.py`, `health.py`.
- `src/arpendo_api/db/` — la persistance : `engine.py` (le moteur), `base.py` (la base
  déclarative et les conventions de schéma — sa docstring en est la référence), `session.py` (la
  session par requête), `migrations/` (Alembic).
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
