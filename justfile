# Commandes du projet — support unique tenu à jour (`.claude/rules/contraintes.md`).
# `.claude/pipeline.config.md` et `.github/workflows/ci.yml` n'appellent que ces recettes :
# quand une commande change, elle change ICI, à un seul endroit.
#
# Monorepo : `api/` + `worker/` en Python (uv), `app/` en Flutter.

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

# ─── api/ + worker/ (Python) ───────────────────────────────────────────────────

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

[working-directory('api')]
fmt-api:
    uv run ruff format .

[working-directory('api')]
fmt-check-api:
    uv run ruff format --check .

[working-directory('api')]
typecheck:
    uv run mypy --strict src

# ─── app/ (Flutter) ────────────────────────────────────────────────────────────

[working-directory('app')]
install-app:
    "{{flutter}}" pub get

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

[working-directory('app')]
fmt-check-app:
    "{{dart}}" format --set-exit-if-changed .

[working-directory('app')]
build:
    "{{flutter}}" build appbundle

# ─── infra/ ────────────────────────────────────────────────────────────────────

# `--env-file` est indispensable : avec `-f infra/…`, le répertoire de projet de Compose est
# `infra/`, et c'est `infra/.env` qu'il chercherait. On lui désigne celui de la racine, le seul
# du dépôt. Les chemins relatifs du fichier compose, eux, restent résolus depuis `infra/`.
up:
    docker compose -f infra/docker-compose.yml --env-file .env up -d
