# Configuration pipeline

## Dépôt GitHub
- repo : `plecart/Arpendo`
- branche trunk : `main`

## Stack
- langages : Dart, Python
- frameworks : Flutter + `mapbox_maps_flutter` v11.27, Tracelet (géoloc arrière-plan) ; FastAPI +
  Pydantic ; Caddy, Valkey, PostgreSQL, Docker Compose
- gestionnaire de paquets : `uv` (Python), `pub` (Dart)
- runtime + version : python 3.13, Flutter stable (version épinglée par FVM au scaffold)

## Commandes du projet
Lues par `cycle-pr`, `execution-qa` et la génération de CI. `n/a` = étape absente du projet.
Toutes délèguent au `justfile` de la racine — **modifier une commande, c'est modifier le justfile**.
- install      : `just install`
- test         : `just test`                  # suite complète
- test ciblé   : `just test-one <chemin|motif>`  # une seule cible, pour la boucle TDD
- lint         : `just lint`
- format       : `just fmt`                   # écrit
- format:check : `just fmt-check`             # vérifie sans écrire
- typecheck    : `just typecheck`
- build        : `just build`
- run local    : `just up`

> ⚠️ **Non vérifiées au 23 août 2026** — le monorepo n'a encore ni `api/` ni `app/`. L'étape 11
> d'`init-projet` n'a pas pu passer. Les relancer au premier scaffold, et corriger ici si l'une
> échoue autrement que par absence de code.

## Qualité
- seuil de couverture : 85 % côté `api/` (appliqué par `--cov-fail-under=85`) ; `n/a` côté `app/`
- gates bloquants en CI : lint, format:check, typecheck, test
- services requis en CI : postgres, valkey

## Périmètre
- domaines (nom métier → chemin) — servent aussi de thèmes/milestones à `triage` :
  - Socle technique : `infra/`, `.github/`, `api/src/arpendo_api/core/`, `api/src/arpendo_api/db/`
  - Compte & identité : `api/src/arpendo_api/domains/compte/`, `app/lib/ui/features/compte/`
  - Partie : `api/src/arpendo_api/domains/partie/`, `app/lib/ui/features/partie/`
  - Territoire : `api/src/arpendo_api/domains/territoire/`, `worker/`, `app/lib/data/`
  - Carte & rendu : `app/lib/ui/features/carte/`, `app/lib/ui/core/`
  - Flux & notifications : `api/src/arpendo_api/domains/flux/`, `app/lib/ui/features/flux/`
- zones sensibles (arrêt humain avant commit) : migrations de schéma · écrans à valider
  visuellement · `infra/` (déploiement, Caddy, compose) · authentification
- hors périmètre : monétisation · analytics produit · iOS (phase 2) · modale « Mes hexagones »
  (post-MVP, cadrage §7.6) · animations de squelette via couches Three.js custom (cadrage §13.1) ·
  exclusion géographique de zones (cadrage §16)
- surfaces exposées — ce que la QA a le droit de vérifier ; ne lister que ce qui existe :
  API HTTP REST + SSE · persistance PostgreSQL · cache et pub/sub Valkey · traitements
  asynchrones (conteneur `worker`) · application mobile Android · comptes utilisateurs /
  isolation entre parties
- surfaces visibles par un utilisateur :
  Connexion + choix du pseudo (UX §4) · Accueil — créer / rejoindre / choix de couleur (UX §5) ·
  avertissement de sécurité à l'entrée en partie (UX §6) · écran Jeu — header, contrôles
  flottants, bandeau d'explication, feuille « Partie » (UX §7) · modale Paramètres — permissions,
  historique, suppression de compte (UX §8) · fin de partie et tableau des scores (UX §9) ·
  notification permanente Android (UX §10) · notifications push et mise à jour forcée (UX §11) ·
  parcours de permissions et état « carte masquée » (UX §12) · états vides / chargement / erreur
  (UX §13)

## Langue
- skills / issues / PRD / descriptions : français
- préfixe conventional commit : anglais (feat/fix/chore/docs/refactor)

## Mapping labels (rôle canonique → label GitHub)
- bug → `bug`
- enhancement → `enhancement`
- needs-triage → `needs-triage`
- needs-info → `needs-info`
- needs-interrogation → `needs-interrogation`
- ready-for-agent → `ready-for-agent`
- ready-for-human → `ready-for-human`
- wontfix → `wontfix`
- qa-plan → `qa-plan`
- qa-finding → `qa-finding`

## Skills du projet
- Pipeline maison (11) : `init-projet`, `vers-prd`, `vers-issues`, `triage`, `interroge-moi`,
  `cycle-pr`, `repercussions`, `pr-paralleles`, `plan-qa`, `execution-qa`, `bug-vers-issue`
- Qualité de code : `ponytail` (+ `-review`, `-audit`, `-debt`, `-gain`, `-help`) — exigé par
  cadrage §13.10
- Flutter (5) : `flutter-apply-architecture-best-practices`, `flutter-setup-declarative-routing`,
  `flutter-setup-localization`, `flutter-build-responsive-layout`, `flutter-fix-layout-issues`
- Mapbox (7) : `mapbox-flutter-patterns`, `mapbox-android-patterns`, `mapbox-cartography`,
  `mapbox-data-visualization-patterns`, `mapbox-style-patterns`, `mapbox-style-quality`,
  `mapbox-token-security`
- Design / UI (5) : `design-system`, `ui-ux-pro-max`, `mobile-app-ui-design`, `mobile-design`,
  `game-ui-ux`, plus `design-motion-principles`
- Transverses : `task-observer` (activé par `CLAUDE.md`), `find-skills`, `i-have-adhd`
- Fourni par le runtime, **non épinglé** : `dataviz` — son `scripts/validate_palette.py` est le
  validateur normatif de la palette (identité visuelle §145, §577). Absent de `skills-lock.json`.
- Écartés :
  - `0xGF/boneyard` — incompatible Flutter par construction : mesure la géométrie du DOM réel
  - `leonxlnx/taste-skill` — borné aux landing pages / portfolios en Tailwind
  - `Graphify-Labs/graphify` — compatible `.dart`, **reporté** faute de code ; CLI déjà présente
  - `obra/superpowers` — chevauche `cycle-pr` / `pr-paralleles` / `triage` / `interroge-moi`
  - `thedotmack/claude-mem` — doublonne la mémoire native de Claude Code
  - Strix (cadrage §13.10) — agent de pentest, pas un skill ; préproduction, plus tard
