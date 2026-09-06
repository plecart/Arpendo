# Commandes du projet — support unique tenu à jour (`.claude/rules/contraintes.md`).
# `.claude/pipeline.config.md` et `.github/workflows/ci.yml` n'appellent que ces recettes :
# quand une commande change, elle change ICI, à un seul endroit.
#
# Monorepo : `api/` en Python (uv) — dont le worker, second point d'entrée du même paquet —
# et `app/` en Flutter.

# Version du SDK Flutter : `.fvmrc` à la racine en est la source unique, dans TOUS les
# environnements. Seul le *fournisseur* diffère, parce que le besoin diffère : en local, FVM isole
# cette version des autres projets de la machine ; en CI, le runner est jetable et dédié, donc
# `subosito/flutter-action` lit le même `.fvmrc` et met `flutter` sur le PATH sans couche FVM.
#
# On vise le lien `.fvm/flutter_sdk` que FVM pose dans le projet, PAS la commande `fvm` : sous
# Windows elle s'installe en `fvm.bat`, que Git Bash ne sait pas résoudre, et son dossier n'est
# pas dans le PATH par défaut. Le lien, lui, marche dans tous les shells sans rien configurer.
# `.fvm/` est ignoré par git : sur un clone neuf, `fvm install` le recrée depuis `.fvmrc`.
# La CI n'a pas de lien — elle surcharge via FLUTTER_CMD / DART_CMD.
#
# Ne jamais écrire `flutter` ou `dart` nus dans une recette : ce serait le SDK global du PATH,
# dont la version n'a aucune raison de correspondre, et l'épinglage deviendrait décoratif.
# `justfile_directory()` rend un chemin Windows à antislashs, que `sh` interprète comme des
# échappements et avale (`E:\Projets` devient `E:Projets`). On normalise en slashs : Windows les
# accepte partout, et le chemin traverse alors n'importe quel shell intact.
# Le `.env` de la racine alimente l'environnement des recettes — `just test` en a besoin, puisque
# `Settings` ne lit que l'environnement (cadrage §13.9 règle 5) et n'ouvre aucun fichier. Sans
# effet en CI : une variable déjà posée dans l'environnement l'emporte sur le `.env`, et le runner
# n'en a de toute façon aucun. Absent du poste, le fichier est ignoré sans erreur.
set dotenv-load := true

racine := replace(justfile_directory(), '\', '/')
flutter := env('FLUTTER_CMD', racine / '.fvm/flutter_sdk/bin/flutter')
dart := env('DART_CMD', racine / '.fvm/flutter_sdk/bin/dart')

default:
    @just --list

# ─── Agrégats — ce que la CI et `cycle-pr` appellent ───────────────────────────

install: install-api install-app
test: test-api test-app
lint: lint-api lint-app
fmt: fmt-api fmt-app
fmt-check: fmt-check-api fmt-check-app

# ─── api/ (Python) — api HTTP et worker, un seul paquet ───────────────────────

# `working-directory` plutôt que `cd X && …` : l'attribut ne dépend d'aucun shell, là où `&&`
# n'existe pas en PowerShell 5.1 — la seule version présente sous Windows 11.

[working-directory('api')]
install-api:
    uv sync

[working-directory('api')]
test-api:
    uv run pytest --cov=src --cov-fail-under=85

# Une seule cible côté `api/`, pour la boucle TDD de `cycle-pr` ; pendant Flutter : `test-one-app`
[working-directory('api')]
test-one CIBLE:
    uv run pytest {{CIBLE}}

[working-directory('api')]
lint-api:
    uv run ruff check .

# `ruff format` ne s'arrête pas aux `.py` : il découvre aussi les **fichiers Markdown** et
# reformate les blocs ```` ```python ```` qu'ils contiennent (également `py`, `py3`, `pyi`,
# `pycon`). Un exemple de code ajouté à un README passe donc par le formateur, et `fmt-check-api`
# échoue dessus comme sur n'importe quel module — piège d'autant plus surprenant que la recette
# ne nomme que `api/`.
[working-directory('api')]
fmt-api:
    uv run ruff format .

[working-directory('api')]
fmt-check-api:
    uv run ruff format --check .

[working-directory('api')]
typecheck:
    uv run mypy --strict src tests

# ─── migrations (Alembic, jamais au démarrage — cadrage §13.9 règle 3) ────────

# Applique les migrations sur la base du `.env`. Dans un conteneur éphémère, même commande :
# `docker compose -f infra/docker-compose.yml --env-file .env run --rm api alembic upgrade head`.
[working-directory('api')]
migrate:
    uv run alembic upgrade head

# Génère une migration par comparaison des modèles au schéma réel. Le fichier produit est à
# RELIRE avant commit : zone sensible « migrations de schéma » (`.claude/pipeline.config.md`).
[working-directory('api')]
migration MSG:
    uv run alembic revision --autogenerate -m "{{MSG}}"

# ─── app/ (Flutter) ────────────────────────────────────────────────────────────

# `&&` place `l10n` APRÈS le corps, jamais avant : `gen-l10n` a besoin de
# `flutter_localizations`, que seul `pub get` met dans l'arbre.
[working-directory('app')]
install-app: && l10n
    "{{flutter}}" pub get

# Textes de l'app. `app_fr.arb` est la seule source versionnée : le script en dérive la locale de
# test `fr-XA` (+30 % de longueur, marqueurs), puis `gen-l10n` écrit la classe. Les deux sorties
# sont ignorées par git, donc régénérées à chaque `just install` — en CI comme sur un clone neuf.
[working-directory('app')]
l10n:
    "{{dart}}" run tool/allonger_arb.dart
    "{{flutter}}" gen-l10n

[working-directory('app')]
test-app:
    "{{flutter}}" test

# Une seule cible côté `app/` (chemin relatif à `app/`), pendant de `test-one`
[working-directory('app')]
test-one-app CIBLE:
    "{{flutter}}" test {{CIBLE}}

[working-directory('app')]
lint-app:
    "{{flutter}}" analyze

[working-directory('app')]
fmt-app:
    "{{dart}}" format .

# `--output none` est indispensable : `dart format` ÉCRIT par défaut, et `--set-exit-if-changed`
# ne règle que le code de sortie. Sans lui, la vérification reformate les fichiers qu'elle contrôle.
[working-directory('app')]
fmt-check-app:
    "{{dart}}" format --output none --set-exit-if-changed .

# Lance l'app sur l'émulateur ou l'appareil branché, configurée depuis le `.env` de la racine
# (chargé par `set dotenv-load`). `env_var` échoue avec un message clair si la variable manque —
# le pendant, côté recette, du refus de démarrer de l'app.
#
# Les deux réglages Sentry prennent `env` et son défaut vide, PAS `env_var` : absente et vide y
# veulent dire la même chose — Sentry désactivé pour le DSN, tout envoyer pour le taux —, là où
# `API_BASE_URL` manquante est un trou qui doit faire échouer la recette. Côté api, `Settings`
# exige au contraire `SENTRY_SAMPLE_RATE` : la dissymétrie est voulue et documentée dans
# `.env.example`, l'application ne pouvant pas refuser de démarrer pour un garde-fou de coût.
#
# Toutes les valeurs sont entre guillemets : elles viennent d'un `.env` que personne ne valide, et
# une valeur portant une espace se découperait sinon en deux arguments — le SDK recevrait un
# réglage tronqué au lieu d'échouer lisiblement.
[working-directory('app')]
run:
    "{{flutter}}" run --dart-define=API_BASE_URL="{{env_var("API_BASE_URL")}}" --dart-define=SENTRY_DSN="{{env("SENTRY_DSN", "")}}" --dart-define=SENTRY_SAMPLE_RATE="{{env("SENTRY_SAMPLE_RATE", "")}}"

[working-directory('app')]
build:
    "{{flutter}}" build appbundle --dart-define=API_BASE_URL="{{env_var("API_BASE_URL")}}" --dart-define=SENTRY_DSN="{{env("SENTRY_DSN", "")}}" --dart-define=SENTRY_SAMPLE_RATE="{{env("SENTRY_SAMPLE_RATE", "")}}"

# ─── infra/ ────────────────────────────────────────────────────────────────────

# `--env-file` est indispensable : avec `-f infra/…`, le répertoire de projet de Compose est
# `infra/`, et c'est `infra/.env` qu'il chercherait. On lui désigne celui de la racine, le seul
# du dépôt. Les chemins relatifs du fichier compose, eux, restent résolus depuis `infra/`.
#
# `--build` : sans lui, `just up` relance l'image telle qu'elle était au dernier build, et une
# dépendance ajoutée entre-temps manque à l'exécution — une panne dont la cause n'est nulle part
# dans le code qu'on vient d'écrire. Le coût est nul quand rien n'a bougé : les couches du
# Dockerfile ne se reconstruisent que si `pyproject.toml` ou `uv.lock` changent.
up:
    docker compose -f infra/docker-compose.yml --env-file .env up -d --build

# Reprend les sources du worker. Elles sont montées comme celles de l'api, mais lui ne recharge pas
# à chaud : il n'y a pas d'équivalent de `--reload` pour une boucle asyncio. `--env-file` est
# indispensable ici pour la même raison que ci-dessus — sans lui, Compose cherche son `.env` dans
# `infra/` et refuse de démarrer sur `VALKEY_PASSWORD` manquant.
restart-worker:
    docker compose -f infra/docker-compose.yml --env-file .env restart worker
