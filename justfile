# Commandes du projet — support unique tenu à jour (`.claude/rules/contraintes.md`).
# `.claude/pipeline.config.md` et `.github/workflows/ci.yml` n'appellent que ces recettes :
# quand une commande change, elle change ICI, à un seul endroit.
#
# Monorepo : `api/` + `worker/` en Python (uv), `app/` en Flutter.

default:
    @just --list

install:
    cd api && uv sync
    cd app && flutter pub get

test: test-api test-app

test-api:
    cd api && uv run pytest --cov=src --cov-fail-under=85

test-app:
    cd app && flutter test

# Une seule cible, pour la boucle TDD de `cycle-pr`
test-one CIBLE:
    cd api && uv run pytest {{CIBLE}}

lint:
    cd api && uv run ruff check .
    cd app && flutter analyze

fmt:
    cd api && uv run ruff format .
    cd app && dart format .

fmt-check:
    cd api && uv run ruff format --check .
    cd app && dart format --set-exit-if-changed .

typecheck:
    cd api && uv run mypy --strict src

build:
    cd app && flutter build appbundle

up:
    docker compose -f infra/docker-compose.yml up -d
