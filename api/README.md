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

Un `.env` qui date d'avant le délai d'arrêt fait échouer `just up` sur une variable manquante —
voir « Arrêter » plus bas.

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

## Arrêter

`docker compose stop` envoie un SIGTERM, puis tue au SIGKILL après un délai. Le défaut de Docker
est trop court pour fermer proprement des flux ouverts (cadrage §13.7, §13.9 règle 6) : `api` et
`worker` déclarent donc leur propre `stop_grace_period` dans `infra/docker-compose.yml`.

Ce délai seul ne suffirait pas, parce qu'**uvicorn attend les connexions ouvertes sans borne** :
une requête longue — une SSE, demain — tiendrait jusqu'au SIGKILL, et le délai n'aurait fait que
retarder la mort brutale. `UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN`, dans le `.env`, lui donne cette
borne.

**L'ordre est tout le sujet** : la borne d'uvicorn doit rester **sous** le `stop_grace_period`,
sinon c'est encore Docker qui tranche et la marge n'aura servi à rien. Les deux valeurs vivent dans
deux fichiers que rien ne relie — `api/tests/test_compose.py` les compare, et rougit si l'ordre
s'inverse ou si un maillon disparaît. Ne pas recopier ces chiffres ailleurs : les lire là.

Le worker n'a rien à borner : sa boucle s'arrête d'elle-même sur SIGTERM, il lui faut seulement le
temps de finir le tour en cours.

**Sur un `.env` plus ancien que ce réglage, toute commande `docker compose` échoue** — donc
`just up`, et par ricochet `just test`, qui exige la pile levée — avec un message qui nomme la
variable manquante. C'est délibéré : Compose n'aurait sinon transmis qu'une chaîne vide, qu'uvicorn
ignore, et la borne aurait disparu sans que rien ne le signale. Recopier la ligne depuis
`.env.example` suffit.

Ce qu'on doit observer : `docker compose stop api` rend la main **dans le délai déclaré** avec le
code de sortie **0**. Un `137` signifierait un SIGKILL — c'est-à-dire l'inverse de ce que cette
configuration existe pour obtenir.

La borne uvicorn est configurée, pas testée en exécution : aucune route de cette api ne tient assez
longtemps pour l'exercer. Elle le sera par ce qui l'exercera vraiment.

## L'image

`Dockerfile` construit une seule image pour les deux points d'entrée, en deux étapes : `uv` installe
les dépendances dans la première, sur l'interpréteur de l'image de base ; la seconde n'embarque que
le résultat et tourne sous l'utilisateur `arpendo`, jamais root (cadrage §13.10).

**Le code et le venv appartiennent à root** : l'utilisateur d'exécution les lit et les exécute, il
n'y écrit pas. Un processus compromis ne peut ni altérer une dépendance ni déposer un module. Rien
dans l'image n'a besoin d'écrire — le worker écrit son battement sous `/tmp`, et les `.pyc` sont
compilés au build. Le job `image` de la CI construit l'image et vérifie qu'un `touch` sous `/app`,
`/app/src` et `/app/.venv` échoue depuis le conteneur.

**Toute image tirée d'un registre est épinglée `tag@sha256:…`** — les `FROM` du Dockerfile comme
`postgres` et `valkey` du compose local. Le tag reste lisible et dit la version voulue ; l'empreinte
fige celle qu'on a réellement eue, et le commentaire au-dessus de chaque épinglage nomme la version
que le tag résolvait le jour où l'empreinte a été lue. `arpendo-api:dev`, construite ici et jamais
tirée, n'en porte pas.

Ces empreintes ne se mettent pas à jour à la main : **Dependabot** les suit, écosystème `docker` sur
`/api` pour le Dockerfile et `docker-compose` sur `/infra` pour le compose, et propose la suivante
quand le tag bouge. Dans un Dockerfile, il ne lit que les lignes `FROM` — d'où une étape nommée
pour l'image `uv` plutôt qu'un `COPY --from=<image>`, et deux `FROM python` identiques plutôt qu'un
`ARG`. Pour relire une empreinte à la source : `docker buildx imagetools inspect <image:tag>`
(l'empreinte de l'index multi-architectures, pas celle d'une plateforme).

Le bot propose aussi les **tags voisins** — `python:3.14-slim`, `postgres:18` — et un tel build
passerait en vert. `tests/test_images.py` tient ce que le bot ne voit pas : toute image tirée porte
une empreinte, tout `COPY --from` nomme une étape, le `FROM python` est la version d'`.python-version`,
et `postgres` comme `valkey` sont la même majeure dans le compose et dans les `services:` de la CI
(qu'aucun écosystème ne suit). Une PR Dependabot qui monte une majeure est rouge : c'est à un humain
de monter les deux côtés ensemble.

**Le même job scanne l'image avec Trivy**, en deux passes : un rapport de toutes les gravités, qui
ne bloque jamais, puis une porte qui rougit sur une vulnérabilité **critique et corrigeable** —
jamais sur une critique sans correctif amont, qui laisserait la PR rouge sans geste possible. Une
porte rouge se lève en reconstruisant l'image sur une empreinte plus récente (Dependabot la
propose) ou en montant la dépendance Python fautive. Pour rejouer la porte sur le poste, sur
l'image que `just up` a construite — `//var/run/…` et non `/var/run/…` : sous Git Bash, MSYS
réécrirait le chemin simple en `C:\Program Files\Git\var\…`, et Linux lit les deux formes :

```
docker run --rm -v //var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.70.0 \
  image --severity CRITICAL --ignore-unfixed --exit-code 1 arpendo-api:dev
```

## Tester et vérifier

**`just test` exige `just up`.** Les tests parlent à un vrai PostgreSQL et à un vrai Valkey,
jamais à des doubles : une connexion simulée ne prouverait rien de ce que cette configuration
existe pour garantir. Ils lisent leurs coordonnées dans le `.env` de la racine, que le justfile
charge dans l'environnement des recettes. En CI, ce sont les conteneurs `services:` du workflow
et les variables du job qui jouent ce rôle — le même code, sans `.env`.

> **L'application tourne sur la base Valkey 0, et aucune suite n'y touche.** L'application tourne
> *toujours* pendant la suite, et celle-ci efface toutes les clés `ratelimit:*` avant et après
> chaque test : sur une base partagée, elle effaçait les compteurs de l'application et lisait les
> siens. Le healthcheck du conteneur `api`, qui interroge `/health` toutes les dix secondes,
> suffisait à faire échouer un test de fenêtre, rarement et de façon illisible. `VALKEY_URL`
> pointe la 1, qui est la base des **verrous** ; chaque suite travaille sur un index qu'elle s'y
> réserve — voir plus bas.
>
> **La séparation ne vaut que pour les commandes du keyspace** — celles du limiteur : `INCR`,
> `EXPIRE`, `TTL`, `SCAN`. Aucune ne traverse les bases logiques, et le recouvrement y devient
> donc impossible plutôt qu'improbable. **Le pub/sub du bus, lui, les traverse** : un abonné d'une
> base reçoit ce qu'on publie depuis une autre (mesuré). Ce qui isole le bus est le **nom de
> canal** — `game:{uuid4}`, un par partie et un par test — et rien d'autre ; c'est écrit au point
> d'usage, dans `tests/conftest.py`. Le jour où un canal à **nom fixe** apparaîtra — canal système,
> verrou, annonce du worker — la suite et l'application se parleront de nouveau, et il faudra le
> traiter là où le canal se compose. **La séparation par magasin décrite plus bas n'y change
> rien** : elle vaut pour le keyspace, jamais pour le pub/sub, et deux suites voisines s'entendent
> donc l'une l'autre exactement comme l'application les entend.
>
> `tests/test_isolation.py` garde la séparation des bases, qui ne vit sinon que dans `.env`,
> `ci.yml` et le compose. Il la garde sur **l'ensemble des bases qu'une suite peut atteindre** —
> les verrous, et les quatorze index réservables — et non sur l'index tiré au lancement : celui-là
> vient du jeu des candidates par construction, donc le comparer ne mesurerait rien (mesuré :
> `VALKEY_URL` sur la 0 laissait passer).

> **Chaque suite crée sa propre base PostgreSQL**, `arpendo_test_<jeton>`, sur le serveur et avec les
> identifiants de `DATABASE_URL` — la fixture de session `magasins` la crée avant que quoi que ce
> soit ne lise la configuration, et la détruit à la fin. Deux suites lancées **en parallèle** depuis
> deux worktrees visaient sinon la même base (#94) : la purge du journal, qui porte sur le préfixe
> de type, effaçait les lignes de la voisine en plein test, et le test des migrations redescendait
> à `base` le schéma sous ses pieds. On ne partitionne pas une table par une clé de ligne quand
> c'est la table qu'on supprime — d'où une base par suite, et non une clé de suite.
>
> Le nom porte un **jeton aléatoire** tiré au lancement, et non le pid. Un pid n'est unique que
> parmi les processus vivants d'un même espace de nommage, et le système le **réattribue** : il
> faudrait alors détruire avant de créer pour survivre à la collision, et cette destruction ne
> saurait pas distinguer le résidu d'une suite morte de la base d'une voisine vivante — deux espaces
> de pid qui joignent le même serveur (WSL, un conteneur, un runner) peuvent porter le même. Un nom
> qui n'est jamais réattribué supprime la collision, donc la destruction, donc le risque.
>
> Écarté pour la même raison, à l'interrogatoire : un nom **stable par worktree**, recréé à chaque
> lancement — deux terminaux du même worktree se détruiraient, c'est-à-dire le cas même qu'on
> cherche à rendre vert. Et le **balayage** de toutes les bases `arpendo_test_*` au démarrage : une
> suite entre deux tests peut n'avoir aucune connexion ouverte, le balayage la tuerait.
>
> Conséquence : un `kill -9` ne passe pas par la fin de session et laisse une base derrière lui, mais
> elle est **inoffensive** — aucune suite ne reprendra jamais son nom. En contrepartie rien ne force
> la main : elles s'accumulent en silence. Pour les balayer, de temps en temps :
>
> ```sql
> SELECT 'DROP DATABASE ' || quote_ident(datname) || ' WITH (FORCE);'
> FROM pg_database WHERE datname LIKE 'arpendo_test_%';
> ```
>
> **Chaque suite se réserve aussi une base logique Valkey**, parmi les index 2 à 15. La réservation
> est un verrou `SET arpendo:tests:base:<index> <jeton> NX EX 3600` posé sur la base que
> `VALKEY_URL` nomme — la 1 sur le poste comme en CI, qui **devient donc la base des verrous** et
> cesse d'être candidate. Un verrou ici, un simple jeton là-bas, et c'est le nombre de noms
> disponibles qui l'explique : quatorze places qu'il faut se répartir, contre un espace assez vaste
> pour qu'on s'y ignore. `NX` rend la prise atomique — deux suites qui démarrent au même instant ne
> peuvent pas obtenir le même index, là où un tirage au sort entrerait en collision une fois sur
> quatorze. L'index obtenu est vidé (`FLUSHDB`) à la prise : ce qu'il contenait appartenait à une
> suite tuée.
>
> La libération compare le jeton avant de supprimer, en un seul pas (`EVAL`) : une suite dont le
> bail aurait expiré pendant qu'elle tournait ne peut pas emporter la réservation de celle qui a
> repris son index. Le bail d'une heure ne sert donc qu'au verrou orphelin d'un `kill -9` — sans
> lui, un index sortirait du jeu jusqu'au prochain `FLUSHALL`. Pour les regarder — le Valkey du
> compose est authentifié, y compris en local (cadrage §13.10) :
>
> ```sh
> docker exec infra-valkey-1 sh -c \
>   'valkey-cli --no-auth-warning -a "$VALKEY_PASSWORD" -n 1 KEYS "arpendo:tests:base:*"'
> ```
>
> Le `sh -c` n'est pas décoratif : sans lui, `$VALKEY_PASSWORD` est développé par le shell de
> l'hôte, où la variable n'existe que si le `.env` a été chargé. Là, elle est développée dans le
> conteneur, qui la porte toujours.

| Commande | Rôle |
|---|---|
| `just test-api` | suite complète avec couverture, seuil 85 % |
| `just test-one tests/test_health.py` | une seule cible, pour la boucle TDD |
| `just lint-api` | `ruff check` |
| `just fmt-api` / `just fmt-check-api` | `ruff format` |
| `just typecheck` | `mypy --strict` sur `src/` et `tests/` |

Les tests HTTP passent par la fixture `client` de `tests/conftest.py` : un `httpx.AsyncClient`
branché sur l'application sans réseau. La chaîne est `settings` → `app` → `client`, et c'est
`app` qui **entre réellement dans le cycle de vie** : `ASGITransport` ne le déclenche pas, donc
sans ce contexte les tests parleraient à une application sans moteur ni client Valkey — en
silence. Un test qui veut un environnement dégradé surcharge `settings` par paramétrisation
indirecte et hérite du reste de la chaîne, comme le fait le test « Valkey injoignable ».
Les tests asynchrones n'ont besoin d'aucun marqueur (`asyncio_mode = "auto"`).

## Journaux

**Un objet JSON par ligne, sur la sortie standard, pour tous les loggers du processus** — le nôtre,
celui d'uvicorn, celui d'Alembic, ceux des bibliothèques. Docker collecte la sortie standard : il
n'y a ni fichier, ni rotation, ni second flux à déclarer ailleurs.

```json
{"event": "Running upgrade -> ada3c4690df8", "logger": "alembic.runtime.migration",
 "level": "info", "timestamp": "2026-09-03T08:41:35.751365Z"}
```

Les clés sont **stables** : `timestamp` (ISO, UTC, suffixé `Z`), `level`, `logger`, `event`, plus
ce que l'appelant a lié. Elles le sont parce qu'une **seule liste de processeurs** sert aux deux
origines — la chaîne structlog et la `foreign_pre_chain` du formateur. Deux listes divergeraient au
premier ajout, et la divergence ne se verrait que dans l'agrégateur.

Un seul processeur échappe à cette liste, et c'est instructif : **le rendu de la pile**.
`stack_info=True` doit produire la clé `stack` des deux côtés, mais `StackInfoRenderer` ne
transporte pas la pile — il la **recalcule depuis sa propre frame**. Juste au moment de l'appel,
faux au moment du formatage, où il capturerait la plomberie du handler à la place du point d'appel.
La stdlib garde donc la sienne, qu'on renomme (`_rename_stack_info`) plutôt que de la recalculer.
Un test couvre les deux origines.

Les valeurs sont **échappées en ASCII**, défaut de `json.dumps` que le rendu conserve : tout
caractère non ASCII part sous sa forme `\uXXXX`, donc l'événement « partie créée » sort avec ses
deux `é` remplacés chacun par une séquence de six caractères. Sans conséquence pour un agrégateur,
moins lisible pour un œil humain devant `docker logs`.

**`configure_logging()` est appelée par les trois points d'entrée** : `create_app`, le worker et
`env.py`. Deux propriétés en découlent, toutes deux éprouvées par `tests/test_logs.py` :

- **idempotente** — le second appel ne fait rien. Sans quoi chaque ligne serait doublée, ce qui ne
  casse rien de visible et se paie en volume d'agrégation ;
- **elle n'enlève le handler de personne** — un `basicConfig(force=True)` vide le handler de
  capture de pytest (mesuré). Elle ajoute le sien, elle ne fait pas le ménage. Les loggers
  d'uvicorn font seule exception : lui les configure **avant** d'appeler la fabrique, et les
  laisser en place mettrait deux formats sur la même sortie.

**Journaliser depuis le code du paquet** — un logger de la stdlib suffit, il passe par le même
rendu :

```python
import structlog

_journal = structlog.get_logger(__name__)
_journal.info("partie créée", hexagones=3)
```

**Ajouter un contexte à toutes les lignes d'une unité de travail** — un `bind_contextvars` dans le
domaine qui le connaît ; `merge_contextvars` est en tête de la chaîne et le verse dans chaque
ligne. Rien à changer dans `core/logs.py`.

Aucun `--log-config` n'est passé à uvicorn : ce serait une troisième déclaration à tenir à jour
dans le Dockerfile, dans le compose et sur le poste.

**Une exception, et une seule : le refus de démarrage.** Les trois points d'entrée lisent leur
configuration **avant** d'ouvrir les journaux, donc une `ConfigurationError` sort en traceback
Python sur stderr, pas en objet JSON sur stdout. L'ordre est délibéré : à ce moment-là la chaîne de
rendu n'existe pas, et c'est ce qui garantit que la valeur fautive ne la traverse pas — ni elle, ni
Sentry, qui s'y branchera. Le traceback ne porte que le nom du champ et la nature du défaut, jamais
la valeur (`from None`, voir « Structure »). Un agrégateur qui n'indexe que du JSON ne verra donc
pas cette ligne-là : c'est dans `docker logs` qu'on lit pourquoi un conteneur a refusé de démarrer.

### L'identifiant de requête

Chaque requête HTTP reçoit un **`uuid4` généré par le serveur**. Il est lié au contexte pour toute
la durée de la requête — donc présent sous la clé `request_id` dans chaque ligne qu'elle produit —
et annoncé sur la réponse par l'en-tête `X-Request-ID`. C'est ce qui permet de partir d'une erreur
signalée par un joueur et de retrouver dans l'agrégateur exactement les lignes de *sa* requête,
plutôt que tout ce que les autres faisaient à la même seconde.

**L'en-tête entrant n'est jamais repris.** C'est une entrée non fiable, et le journal est un lieu
de confiance : la reprendre laisserait un appelant choisir la clé sur laquelle ses requêtes sont
regroupées — se confondre avec un autre, ou déposer une chaîne de son choix, où un saut de ligne
suffit à fabriquer une fausse entrée. Le jour où un identifiant de corrélation venu d'un client
légitime aura un sens, il aura son propre en-tête et sa propre validation.

**`RequestIdMiddleware` est empilé au-dessus du limiteur de débit** (donc déclaré après lui dans
`create_app` : Starlette enveloppe, le dernier déclaré est traversé le premier). Un 429 est produit
par le limiteur sans que la requête atteigne l'application ; dans l'ordre inverse, exactement les
réponses qu'on cherche à diagnostiquer seraient les seules sans identifiant. Un test l'éprouve.

Le contexte est **restauré** à la sortie, et non supprimé (`bound_contextvars`) : il appartient au
fil d'exécution, pas à la requête. Une requête qui lève laisserait sa clé derrière elle, et une
tâche de fond se verrait rattachée à un travail qui ne l'a pas demandée ; et le jour où un contexte
englobant liera `request_id`, la valeur d'avant sera rendue plutôt qu'effacée.

**Une limite mesurée : une 500 non rattrapée ne porte pas l'en-tête.** Starlette monte son
`ServerErrorMiddleware` **au-dessus** de la pile de middlewares de l'application ; la réponse
d'erreur qu'il fabrique ne repasse donc pas par le nôtre. Les lignes de journal émises *pendant*
la requête portent bien l'identifiant — c'est le plus utile — mais la réponse que le client voit
n'en porte aucun. Structurel, non contournable par `add_middleware` : à savoir avant de chercher
un identifiant sur un rapport d'erreur 500.

## Sentry

**Rien n'est envoyé tant que `SENTRY_DSN` est vide** — et c'est le défaut du poste comme de la CI.
« Désactivé » veut dire *aucun appel* à `sentry_sdk.init`, et non un `init` avec un DSN vide : ce
dernier installerait quand même les intégrations, les handlers de journalisation et le hook
d'exceptions non rattrapées.

| Réglage | Rôle |
|---|---|
| `SENTRY_DSN` | le point de collecte. **Vide = désactivé.** Masqué : l'URL porte la clé du projet |
| `SENTRY_SAMPLE_RATE` | part des événements envoyés, dans `]0, 1]`. `1.0` sur le poste ; la valeur de production est tranchée par #47 |

⚠️ **Un `SENTRY_DSN` posé dans le `.env` d'un poste fait aussi partir les événements de `just
test`** : la suite construit de vraies applications, qui appellent `configure_sentry`. Et comme
`SENTRY_ENVIRONMENT` n'est pas encore posée (elle est portée par #47), le SDK les étiquette
`production` — son défaut. La CI est protégée, elle pose `SENTRY_DSN` vide explicitement ; un poste
ne l'est pas. Laisser le DSN vide localement est le défaut, et le bon.

`configure_sentry(settings)` est appelée par les **deux hôtes qui servent du trafic** — la fabrique
d'application et le worker — après `configure_logging()`. Cet ordre est une **convention, pas une
contrainte** : mesuré, le SDK n'installe aucun handler sur la racine, il remplace
`logging.Logger.callHandlers`, ce qui le rend insensible à l'ordre. On va du moins effectif au plus
effectif — les réglages, les journaux, puis le seul des trois qui ouvre une porte vers le réseau.
L'environnement des migrations ne l'appelle pas : un processus court, sans requête, dont l'échec se
lit dans le code de retour.

**Les lignes de journal atteignent Sentry**, et pas seulement stdout : l'intégration de
journalisation du SDK en fait des breadcrumbs à partir de `INFO` et des événements à partir de
`ERROR`. Elles passent donc par `scrub`, **message rendu comme paramètres bruts** : un
`logger.error("echec a %s, %s", lat, lon)` expédie le message formaté *et* la liste `params`, et
c'est la règle de la paire sur les nombres qui couvre la seconde — le rendu seul aurait masqué une
donnée voyageant à côté de lui.

### Deux filets d'assainissement, parce qu'aucun ne suffit seul

Le cadrage §13.10 est explicite : « le scrubbing PII doit être configuré explicitement, sinon on
reconstruit exactement l'historique de localisation que §12.3 interdit ».

- **`EventScrubber`** (fourni par le SDK) travaille **par clé** : `password`, `token`,
  `authorization`, `cookie`… plus les clés de position que ce projet ajoute — `latitude`,
  `longitude`, `lat`, `lon`, `email`. Attention, **il remplace son denylist par défaut quand on lui
  en passe un** : `DENYLIST` reprend donc les 33 du SDK avant d'ajouter les cinq nôtres. Un test
  l'épingle, parce que l'erreur inverse — croire ajouter et en fait retirer — ne se voit nulle
  part. (Les quatre clés d'adresse IP font exception : le SDK les ajoute de lui-même dès que
  `send_default_pii` est faux.)
- **`scrub`**, en `before_send`, travaille **par forme** sur le corps entier de l'événement :
  paires de coordonnées, `Bearer …`, adresses e-mail. C'est lui qui attrape ce que l'autre ne peut
  pas voir — une coordonnée noyée dans un message, ou le secret qu'une `ValidationError` de
  pydantic recopie en clair dans son texte.

**Une position se reconnaît à la paire, jamais à un nombre seul** — et la règle vaut pour les deux
natures que prend une coordonnée dans un événement :

| | reconnu | ignoré |
|---|---|---|
| **chaînes** | deux décimales séparées par n'importe quoi de court et non numérique : `48.858370, 2.294481`, `lat=…&lon=…`, `POINT(… …)`, un JSON sérialisé, un saut de ligne | un horodatage ISO — il n'a **qu'une** décimale longue |
| **nombres** | deux flottants de forme géographique dans le **même conteneur** : les paramètres d'un log, un `extra`, un `contexts`, la `data` d'un breadcrumb | un flottant isolé, des entiers, des nombres ronds |

Le faux positif assumé est un conteneur de deux mesures fines (`{"p50": 12.345678, "p99":
98.765432}`), assaini pour rien. L'asymétrie est voulue : perdre un centile se voit et se répare,
laisser fuir une position ne se voit pas et ne se répare pas. `FORMES_DE_POSITION`, dans
`tests/test_sentry.py`, épingle la **population** des formes connues — sept d'entre elles fuyaient
pendant qu'une huitième servait de preuve que « c'était couvert ».

`scrub` est une **fonction pure** : elle rend une structure neuve et ne touche pas l'événement
reçu, ce qui permet de l'éprouver sur un dictionnaire écrit à la main, sans réseau, sans `init`,
sans projet Sentry.

**Le motif de coordonnée exige une paire**, jamais un nombre isolé : un horodatage ISO
(`…:35.751365Z`) a exactement la même forme décimale, et un motif à un seul nombre les emporterait
tous — on assainirait la seule chose qui permet de dater une erreur. Un test épingle un horodatage,
un index H3 et un numéro de build comme devant **survivre**.

**Ce que ces deux filets ne couvrent pas** : les lignes de journal. `scrub` est un `before_send`
Sentry, il ne traverse jamais la sortie standard. L'assainissement des coordonnées dans les
journaux est porté par #92, à traiter avant que le domaine Territoire journalise sa première
position.

**L'identifiant de requête est posé en tag Sentry** par `RequestIdMiddleware` — c'est lui qui relie
une erreur remontée dans Sentry aux lignes de journal qu'elle a produites.

Pas de `traces_sample_rate` (pas de performance), pas de `set_user` (ce qu'un identifiant de compte
vaut au RGPD sera tranché par le domaine Compte), pas de table `ignore_errors` vide. Le Data
Scrubbing configuré côté serveur Sentry est un **troisième** filet, indépendant de ce code (#30).

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
`AuthenticationError` : un mot de passe Valkey erroné désarme la limitation. La branche est muette
par construction — aucune trace, pas même en JSON — mais `/health` le dit en répondant 503.
Assumé : rejeter chaque requête sur une erreur de configuration ferait une panne totale là où
l'on a un service dégradé et signalé.
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
le journal de la stdlib — donc en JSON, comme le reste — en nommant la tâche fautive, et le suivant
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

**`just migrate` dit ce qu'il fait** : `env.py` appelle `configure_logging()` comme les deux autres
points d'entrée, donc les messages « Running upgrade … » du logger d'Alembic sortent en JSON, sur la
même sortie et avec les mêmes clés que le reste. C'est la raison pour laquelle le troisième appel
existe — sans lui, la commande resterait muette et seul son code de retour parlerait. Pour l'état
courant sans rien appliquer : `cd api && uv run alembic current`.

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
  domaines s'y ajoutent sous `/v1` ; **deux** restent à la racine, parce que leurs lecteurs ne
  connaissent pas `/v1` : `/health`, qui s'adresse aux sondes, et `/version`, qui s'adresse à un
  client trop vieux pour parler à `/v1`.
- `src/arpendo_api/core/` — le transversal : `settings.py` (la seule lecture de
  l'environnement du paquet), `logs.py` (le rendu JSON, une fois pour tous les loggers),
  `request_id.py` (l'identifiant de requête et son en-tête), `valkey.py`, `health.py`,
  `version.py` (les deux seuils de version du client),
  `journal.py` (la ligne, le type, le registre), `bus.py` (`publish` / `subscribe`),
  `resources.py` (les ressources partagées et leur cycle de vie).
- `src/arpendo_api/db/` — la persistance : `engine.py` (le moteur), `base.py` (la base
  déclarative et les conventions de schéma — sa docstring en est la référence), `session.py` (la
  session par requête), `migrations/` (Alembic).
- `src/arpendo_api/worker/` — le **second point d'entrée** : la boucle de tâches périodiques et
  son point d'entrée `python -m arpendo_api.worker`.
- `src/arpendo_api/domains/` — un paquet par domaine métier, créé avec le premier.

**Les réglages sensibles sont des `Secret`** — le mot de passe Valkey et l'URL de base, qui porte
celui de PostgreSQL. Les afficher, les journaliser ou les sérialiser rend `SecretStr('**********')`
et rien d'autre ; la valeur ne sort que par un `.get_secret_value()` explicite, dans la seule
fabrique qui la consomme. Un futur secret — clé de session, jeton FCM — se déclare avec le même
alias.

**Le DSN Sentry est la seule exception, et elle est instructive** : il se déclare `OptionalSecret`,
pas `Secret`. `Secret` refuse le blanc, parce que partout ailleurs une variable posée mais vide est
une configuration trouée qu'il vaut mieux découvrir au démarrage. Pour le DSN, « vide » est au
contraire une **décision de l'exploitant** — Sentry désactivé — et le poste comme la CI tournent
ainsi. `OptionalSecret` ramène donc le blanc à `None` par un validateur `before`, sans jamais
rejeter. Sans lui, `SENTRY_DSN=` donnerait `SecretStr('')` : une valeur présente et fausse, et une
branche « désactivé » qui ne se déclencherait jamais.

**Les trois hôtes du paquet lisent leur configuration par `load_settings()`**, jamais par
`Settings()` — l'api, le worker et l'environnement des migrations. La différence n'est visible que
le jour où la configuration est fausse : `Settings()` lève une `ValidationError` qui recopie
l'entrée **brute** dans l'`input_value` de chacune de ses erreurs, avant l'emballage `SecretStr`.
Son *message* n'en porte plus rien — `hide_input_in_errors` du `model_config` l'en retire, donc la
trace du démarrage refusé ne la montre pas — mais `errors()` et `json(include_input=True)` la
portent toujours, et rien n'empêche un appelant futur de les lire. `load_settings()` traduit
l'erreur en
`ConfigurationError` qui nomme le champ et la nature du défaut, jamais la valeur — et coupe le
chaînage (`from None`), sans quoi la trace d'origine s'imprimerait juste au-dessus. C'est le seul
chemin du démarrage qu'aucun assainissement d'événement ne couvre : Sentry lit son propre DSN dans
ces réglages, il n'existe donc pas encore. Un test balaie `src/` et échoue sur tout `Settings()`
qui reparaîtrait hors de `settings.py`.

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
