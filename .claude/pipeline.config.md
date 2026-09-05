# Configuration pipeline

## Dépôt GitHub
- repo : `plecart/Arpendo`
- branche trunk : `main`

## Sources de vérité
Ordre de normativité : **en cas de contradiction, le rang le plus haut l'emporte**. Lu par le skill
`contradiction` et par la règle `.claude/rules/decisions-vs-doc.md`.

| Rang | Fichier | Portée | Où s'inscrit un amendement |
|---|---|---|---|
| 1 | `documents/reference/01-cadrage.md` | produit, règles du jeu, étude technique, exploitation — **toutes sections closes** | le § concerné, **plus** une ligne dans le journal des changements (§18) — le §18 consigne les décisions **remplacées** : un § *ajouté* s'en passe, il est visible par lui-même |
| 2 | `documents/reference/02-specification-ux.md` | l'interface des décisions du cadrage ; n'en rouvre aucune | le § concerné seul — le document **ne porte que l'état courant**, jamais d'historique |
| 3 | `documents/reference/03-identite-visuelle.md` | direction « Relevé », close. Ses valeurs sont **intégrées** dans la spec UX §1.2, §1.5, §1.6, §3.4.1, §4 | le § concerné **et** son § miroir dans la spec UX — sinon les deux divergent |
| 4 | `documents/reference/04-chiffrage.md` | coûts d'hébergement et scénarios de montée en charge | le § concerné |
| 5 | issues GitHub ouvertes | découpage et planification, **dérivés** des rangs 1 à 4 | le corps de l'issue, jamais un commentaire — voir `repercussions` |

**Non normatif :** `documents/archive/` conserve le raisonnement et les options écartées. Rien ne
s'y décide ; on y **archive** le pourquoi d'un amendement. `documents/setup/` et
`documents/maquettes/` sont des supports, pas des sources.

Toute référence croisée cite un **§ ou un titre de section**, jamais un numéro de ligne : une
position périme à la première édition du document.

## Stack
- langages : Dart, Python
- cible mobile : **Android 8.0 (API 26) minimum** — `minSdk = 26` dans `app/android/app/build.gradle.kts`
  (cadrage §1) ; iOS en phase 2
- frameworks : Flutter + `mapbox_maps_flutter` v11.27, Tracelet (géoloc arrière-plan) ; FastAPI +
  Pydantic ; Caddy, Valkey, PostgreSQL, Docker Compose
- gestionnaire de paquets : `uv` (Python), `pub` (Dart)
- runtime + version :
  - **Python 3.13** — épinglée dans `api/.python-version` (`3.13`, mineure : `uv` installe le
    dernier patch, en local comme en CI ; le job CI ne déclare aucune version).
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
- textes app   : `just l10n`                 # dérive `fr-XA` puis génère `AppLocalizations`
- test         : `just test`                  # suite complète
- test ciblé api : `just test-one <chemin|motif>`     # une seule cible, pour la boucle TDD
- test ciblé app : `just test-one-app <chemin>`       # chemin relatif à `app/`
- lint         : `just lint`
- format       : `just fmt`                   # écrit
- format:check : `just fmt-check`             # vérifie sans écrire
- typecheck    : `just typecheck`
- build        : `just build`
- run local    : `just up`
- run app      : `just run`                   # app sur l'émulateur/appareil, `--dart-define` depuis le `.env`
- reprise worker : `just restart-worker`   # sources montées, mais pas de rechargement à chaud
- migrate      : `just migrate`               # `alembic upgrade head` sur la base du `.env`
- migration    : `just migration MSG`         # autogenerate — fichier à relire avant commit

> **`just test` exige `just up`** : les tests d'`api/` parlent à un vrai PostgreSQL et à un vrai
> Valkey. Ils lisent leurs coordonnées dans le `.env` de la racine (`set dotenv-load` du
> justfile) ; en CI, ce sont les conteneurs `services:` et les variables du job qui les
> fournissent. Copier `.env.example` en `.env` fait partie de l'installation d'un poste.

> Toutes exécutées et vertes depuis le scaffold `api/` + `app/` du 26 août 2026.

## Qualité
- seuil de couverture : 85 % côté `api/` (appliqué par `--cov-fail-under=85`) ; `n/a` côté `app/`
- gates bloquants en CI : lint, format:check, typecheck, build, test
- services requis en CI : `postgres:17`, `valkey:8`
  - **PostgreSQL 17** — disponible chez tous les hébergeurs managés UE (la 18 ne l'est pas
    partout), supporté jusqu'en novembre 2029, et aucune fonctionnalité postérieure n'est
    utilisée : H3 en BIGINT sans extension (cadrage §13.6). **Commander le service managé en 17.**
  - **Valkey 8** — ligne stable, compatible protocole Redis 7 ; usages du projet (pub/sub, cache,
    compteurs, verrous — cadrage §13.0) n'ont besoin de rien de plus récent. **Authentifié en
    CI comme ailleurs** (`VALKEY_EXTRA_FLAGS: --requirepass …`) : le §13.10 exige le mot de passe
    dans tous les environnements, et une CI qui tournerait sans lui validerait une configuration
    que personne ne déploie.

## Périmètre
- domaines (nom métier → chemin) — servent aussi de thèmes/milestones à `triage` :
  - Socle technique : `infra/`, `.github/`, `api/src/arpendo_api/core/`, `api/src/arpendo_api/db/`
    — et tout ce qui n'est pas un domaine métier : la pipeline (`.claude/`, `CLAUDE.md`,
    `CONTRIBUTING.md`, `justfile`, `.env.example`) et les documents de référence (`documents/`).
    C'est ce qui donne un thème aux PR de doc et d'outillage, qui n'en avaient pas
  - Compte & identité : `api/src/arpendo_api/domains/compte/`, `app/lib/ui/features/compte/`
  - Partie : `api/src/arpendo_api/domains/partie/`, `app/lib/ui/features/partie/`
  - Territoire : `api/src/arpendo_api/domains/territoire/`, `api/src/arpendo_api/worker/`, `app/lib/data/`
  - Carte & rendu : `app/lib/ui/features/carte/`, `app/lib/ui/core/`
  - Flux & notifications : `api/src/arpendo_api/domains/flux/`, `app/lib/ui/features/flux/`
- zones sensibles (arrêt humain — **la cadence est fixée par `.claude/rules/contraintes.md`**, et
  elle n'est pas la même pour les deux) : écrans à valider visuellement · authentification
  — l'arrêt sur les migrations de schéma est levé tant qu'aucun environnement ne porte de données
  réelles ; à réintroduire au premier déploiement
- hors périmètre : monétisation · analytics produit · iOS (phase 2) · modale « Mes hexagones »
  (post-MVP, cadrage §7.6) · animations de squelette via couches Three.js custom (cadrage §13.1) ·
  exclusion géographique de zones (cadrage §16) · animation du logo pendant le chargement et
  animation de transition entre les écrans (**cadrage §20**, registre des reports)
- **`triage` lit le cadrage §20 avant de créer une issue** : un sujet qui y figure est un report
  décidé, pas un manque à ticketer
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
- identifiants d'`api/src/` (types, fonctions, modules) et identifiants techniques fixés par le
  cadrage (tables, colonnes, champs) : anglais. **`src/` et non `api/` entier** : le body de la PR
  #88, qui a posé cette ligne, cite la décision de la vague 3 comme bornant l'anglais aux
  « identifiants publics d'`api/src` » — la ligne écrite sur-étendait la décision qu'elle
  enregistrait. Les fonctions d'`api/tests/` relèvent de la ligne suivante, avec les noms de tests
  et les docstrings qu'elles côtoient
- code Dart d'`app/` : français (`Bandeau`, `resoudre`, `enLigne`…), hors identifiants techniques
  ci-dessus — convention établie par les composants mergés et le glossaire (préambule)
- commentaires / docstrings / noms de tests : français
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
- prd → `prd`   # label de nature (document parent) — hors machine à états, ni rôle d'état ni thème
- documentation → `documentation`   # label de nature (PR `docs(…)` sans issue liée, PRD) — hors
  machine à états

**Métadonnées d'une PR** — posées à l'Étape 2 de `cycle-pr`, vérifiées à l'Étape 5. Toute PR qui
n'est pas l'œuvre d'un bot porte, sans exception ni « plus tard » :
- **assignee** : son auteur ;
- **un** label de catégorie : celui de l'issue qu'elle ferme ; sans issue, dérivé du type
  conventional commit — `feat` / `chore` / `refactor` → `enhancement`, `fix` → `bug`,
  `docs` → `documentation` ;
- **le milestone** du domaine de ses fichiers (ci-dessous) — le socle couvre la pipeline et les
  documents, aucune PR n'en est orpheline.
Les PR Dependabot gardent leurs labels `dependencies` / écosystème et n'entrent pas dans la règle.
Normalisées en une passe le 5 septembre 2026 ; à partir de là, une PR qui dévie se corrige avant
`gh pr ready`, pas dans une passe de rattrapage.

## Skills du projet
- Pipeline maison (12) : `init-projet`, `vers-prd`, `vers-issues`, `triage`, `interroge-moi`,
  `cycle-pr`, `contradiction`, `repercussions`, `pr-paralleles`, `plan-qa`, `execution-qa`,
  `bug-vers-issue`
- Audit maison (1) : `audit-spec-ui` — audit mécanique d'une spec d'interface, issu du journal
  d'observations (obs 1, 3, 5, 14) ; commande homonyme `/audit-spec-ui`
- Qualité de code (6) : `ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`,
  `ponytail-gain`, `ponytail-help` — exigé par cadrage §13.10, `ponytail` activé par `CLAUDE.md`
- Flutter (5) : `flutter-apply-architecture-best-practices`, `flutter-setup-declarative-routing`,
  `flutter-setup-localization`, `flutter-build-responsive-layout`, `flutter-fix-layout-issues`
- Mapbox (6) : `mapbox-flutter-patterns`, `mapbox-cartography`, `mapbox-token-security`,
  `mapbox-data-visualization-patterns`, `mapbox-style-patterns`, `mapbox-style-quality` — les
  trois derniers sous conditions, voir `CLAUDE.md` (« Carte (Mapbox) et navigation »)
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
