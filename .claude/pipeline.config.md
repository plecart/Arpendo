# Configuration pipeline

## Dépôt GitHub
- repo : `plecart/Arpendo`
- branche trunk : `main`

## Stack
- langages : Dart, Python
- frameworks : Flutter + `mapbox_maps_flutter` v11.27, Tracelet (géoloc arrière-plan) ; FastAPI +
  Pydantic ; Caddy, Valkey, PostgreSQL, Docker Compose
- gestionnaire de paquets : `uv` (Python), `pub` (Dart)
- runtime + version :
  - **Python 3.13** — fournie par `uv` ; à épingler dans `api/.python-version` au scaffold.
  - **Flutter 3.47.1** (Dart 3.13.1, révision `6655482ec0`) — épinglée
    dans `.fvmrc` à la racine, **source unique en local comme en CI**. Seul le fournisseur
    diffère : FVM sur le poste de dev, `subosito/flutter-action` sur le runner (qui lit le
    même `.fvmrc`). Les recettes `app/` du justfile passent par les variables `{{flutter}}` /
    `{{dart}}`, valant `fvm flutter` / `fvm dart` par défaut et surchargées en CI via
    `FLUTTER_CMD` / `DART_CMD`. Changer de version = éditer `.fvmrc`, puis `fvm install`.

## Commandes du projet
Lues par `cycle-pr`, `execution-qa` et la génération de CI. `n/a` = étape absente du projet.
Toutes délèguent au `justfile` de la racine — **modifier une commande, c'est modifier le justfile**.
- install      : `just install`
- test         : `just test`                  # suite complète
- test ciblé api : `just test-one <chemin|motif>`     # une seule cible, pour la boucle TDD
- test ciblé app : `just test-one-app <chemin>`       # chemin relatif à `app/`
- lint         : `just lint`
- format       : `just fmt`                   # écrit
- format:check : `just fmt-check`             # vérifie sans écrire
- typecheck    : `just typecheck`
- build        : `just build`
- run local    : `just up`

> ⚠️ **Non vérifiées tant que `api/` et `app/` n'existent pas** — les recettes pointent vers des
> répertoires absents. À exécuter réellement dès le premier scaffold, et à corriger ici si l'une
> échoue pour une autre raison que l'absence de code. **Les agrégats (`install`, `test`, `lint`,
> `fmt*`) traversent les deux répertoires : le premier scaffold doit créer `api/` et `app/`
> ensemble** — même réduits au squelette —, sinon chaque commande échoue sur le répertoire manquant
> et la CI reste rouge.

## Qualité
- seuil de couverture : 85 % côté `api/` (appliqué par `--cov-fail-under=85`) ; `n/a` côté `app/`
- gates bloquants en CI : lint, format:check, typecheck, build, test
- services requis en CI : `postgres:17`, `valkey:8`
  - **PostgreSQL 17** — disponible chez tous les hébergeurs managés UE (la 18 ne l'est pas
    partout), supporté jusqu'en novembre 2029, et aucune fonctionnalité postérieure n'est
    utilisée : H3 en BIGINT sans extension (cadrage §13.6). **Commander le service managé en 17.**
  - **Valkey 8** — ligne stable, compatible protocole Redis 7 ; usages du projet (pub/sub, cache,
    compteurs, verrous — cadrage §13.0) n'ont besoin de rien de plus récent.

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
- Qualité de code (6) : `ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`,
  `ponytail-gain`, `ponytail-help` — exigé par cadrage §13.10, `ponytail` activé par `CLAUDE.md`
- Flutter (5) : `flutter-apply-architecture-best-practices`, `flutter-setup-declarative-routing`,
  `flutter-setup-localization`, `flutter-build-responsive-layout`, `flutter-fix-layout-issues`
- Mapbox (7) : `mapbox-flutter-patterns`, `mapbox-android-patterns`, `mapbox-cartography`,
  `mapbox-data-visualization-patterns`, `mapbox-style-patterns`, `mapbox-style-quality`,
  `mapbox-token-security`
- Design / UI (4) : `design-system`, `mobile-design`, `game-ui-ux`, `design-motion-principles` —
  un seul par situation, table d'arbitrage dans `CLAUDE.md` (« Design et UI »)
- Transverses : `task-observer` (activé par `CLAUDE.md`), `find-skills`, `i-have-adhd`
- Fourni par le runtime, **non épinglé** : `dataviz` — son `scripts/validate_palette.py` est le
  validateur normatif de la palette (identité visuelle §1.2, §4.3). Absent de `skills-lock.json`.
- Écartés :
  - `0xGF/boneyard` — incompatible Flutter par construction : mesure la géométrie du DOM réel
  - `leonxlnx/taste-skill` — borné aux landing pages / portfolios en Tailwind
  - `Graphify-Labs/graphify` — compatible `.dart`, **reporté** faute de code ; CLI déjà présente
  - `obra/superpowers` — chevauche `cycle-pr` / `pr-paralleles` / `triage` / `interroge-moi`
  - `thedotmack/claude-mem` — doublonne la mémoire native de Claude Code
  - Strix (cadrage §13.10) — agent de pentest, pas un skill ; préproduction, plus tard
