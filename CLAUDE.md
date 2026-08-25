# Pipeline de développement

Ce projet suit une pipeline de dev pilotée par les issues. Le cycle de réalisation d'une PR est
décrit dans [CONTRIBUTING.md](CONTRIBUTING.md) et exécutable via le skill `cycle-pr`.

## Règles permanentes (toujours actives)

@.claude/rules/contraintes.md
@.claude/rules/taille-pr.md
@.claude/rules/cleanup-verbatim.md

## Configuration du projet

`.claude/pipeline.config.md` est la **source unique** pour : le dépôt GitHub, le mapping de labels,
la stack, les **commandes du projet** (test / lint / format / typecheck / build), les seuils de
qualité, les **domaines**, les **zones sensibles** et les **surfaces exposées**. Ne jamais deviner
une commande ni un label — les lire là. Pour créer ou modifier ce fichier : skill `init-projet`.

Les **domaines** servent aussi de thèmes (milestones GitHub). Les **surfaces visibles par un
utilisateur** déclenchent la vérif de fumée avant merge et la proposition de campagne QA en fin de
thème — si ce champ est vide, ces deux propositions ne se déclenchent jamais.

## Vocabulaire

Utiliser le glossaire de domaine du projet (`UBIQUITOUS_LANGUAGE.md` s'il existe) dans les
noms de tests, les titres d'issues et de PR. Respecter les ADR de la zone touchée.

## Documentation des bibliothèques

Pour toute question sur une lib/framework de la stack (API, config, migration de version),
**utiliser en priorité le serveur MCP `context7`** plutôt que la mémoire ou une recherche web :
il renvoie la doc à jour de la lib demandée, ce qui économise des tokens et évite les réponses
périmées. Déclaré dans `.mcp.json` à la racine (scope projet), **sans clé API** : les quotas
de l'offre gratuite s'appliquent. Vérifier avec `claude mcp list`.

## Minimalisme (`ponytail`)

Invoquer le skill `ponytail` **avant d'écrire du code** — écriture, ajout, refactor, correctif,
choix d'une dépendance ou d'une lib. Sa description seule ne suffit pas à le déclencher de façon
fiable : c'est cette ligne qui l'active. Exigé par le cadrage §13.10, aligné sur la doctrine
KISS/DRY/YAGNI de `.claude/rules/contraintes.md`.

Niveau par défaut : `full`. Se change par `/ponytail lite|full|ultra` et persiste jusqu'à la fin
de la session. Ponctuellement : `/ponytail-review` (relecture anti-sur-ingénierie d'un diff),
`/ponytail-audit` (dépôt entier), `/ponytail-debt` (raccourcis marqués `ponytail:` à reprendre).

**Ce qu'il ne simplifie jamais** : validation aux frontières de confiance, gestion d'erreurs qui
évite une perte de données, sécurité, accessibilité, et tout ce qui est explicitement demandé.
Il raccourcit la solution, jamais la lecture : tracer le flux complet avant de choisir un barreau.

`ponytail` gouverne **ce qu'on construit** ; `.claude/rules/cleanup-verbatim.md` gouverne **la
relecture de ce qui a été construit**. Les deux s'appliquent, à des moments différents — ponytail
en amont de l'écriture, le prompt de relecture après. L'un ne dispense pas de l'autre.

## Design et UI — arbitrage des skills

**La spécification décide, les skills exécutent.** Les jetons (`02-specification-ux.md` §1 :
espacements, typo, couleurs, mouvement), l'architecture d'écran (§2), la palette joueur (§3) et
l'identité « Relevé » (`03-identite-visuelle.md`) sont **clos**. Aucun skill ne choisit une
palette, une police, un style, une durée d'animation ni un rayon d'angle : il les **lit** dans la
spec. Ne jamais re-dériver la contrainte ΔE (§16) — elle a déjà été calculée.

Quatre skills design sont installés et se chevauchent. Un seul par situation :

| Situation | Skill | Ce qu'il fait ici — et pas plus |
|---|---|---|
| Structure de l'écran Jeu : contrôles flottants, pile d'activité, feuille, empilement Connexion → Accueil → Avertissement → Jeu → Paramètres | `game-ui-ux` | Ancrage aux safe areas (§2.3), pile d'écrans, **HUD piloté par événements SSE, jamais par sondage**. Les widgets concrets viennent des skills `flutter-*` |
| Écrire `tokens.json` et son pendant Flutter (`ThemeData` / `ThemeExtension`) | `design-system` | Architecture primitif → sémantique → composant, **valeurs recopiées de la spec §1**. Ni CSS, ni Tailwind, ni diapositives |
| Relire une animation implémentée | `design-motion-principles` | **Mode audit uniquement**, contre les jetons `motion-*` de la spec. Jamais en mode construction : il est pensé CSS/Framer et choisirait des durées déjà fixées |
| Performance mobile (60 fps, batterie, géoloc arrière-plan) et checklist de sortie | `mobile-design` | Sur invocation explicite `/mobile-design`. Lourd (six lectures obligatoires), orienté React Native : ne pas le déclencher pour dessiner un écran |

Sur une demande vague (« améliore cet écran »), **ne pas tirer un skill au hasard** : lire la
section correspondante de la spec, puis choisir dans la table.

## Observation continue (`task-observer`)

Invoquer le skill `task-observer` au début d'une session **longue ou structurée** — un cycle de PR,
un audit, une passe de spec. Pas pour une question, une commande isolée ou un correctif court.

**Seuil de consignation — haut.** Ne consigner que ce qui changerait le comportement d'un skill :
une règle violée de façon répétée, une correction de l'utilisateur qui se généralise, un manque
rencontré sur plusieurs sessions. Une friction isolée ne se consigne pas. **Maximum 3 entrées par
session** ; au-delà, ne garder que les plus fortes.

**Ne jamais interrompre pour le journal.** Pas de proposition de revue spontanée, pas de résumé
d'observations en fin de session, pas de relance sur le retard de revue. Le journal ne se surface
que si l'utilisateur le demande explicitement.

Au chargement de **n'importe quel skill**, consulter le journal d'observations pour les entrées
OPEN rattachées à ce skill et en appliquer les enseignements au travail en cours — même si le
fichier du skill n'a pas encore été mis à jour.

**Emplacement du journal, à ne pas laisser deviner :**
`C:\Users\pacom\.claude\projects\E--Projets-Arpendo\skill-observations\log.md`. C'est un chemin
**stable**, hors du dépôt. Ne jamais l'ancrer sur le répertoire courant : `pr-paralleles` travaille
dans des **git worktrees** éphémères, et un journal écrit là disparaît avec le worktree.

## Skills de la pipeline

Chaque skill s'invoque par sa **commande homonyme** (`/triage`, `/cycle-pr`, `/plan-qa`…) ou se
déclenche automatiquement sur sa description.

| Commande | Rôle |
|---|---|
| `/init-projet` | Setup et reconfiguration de la pipeline |
| `/vers-prd` | Conversation → PRD |
| `/vers-issues` | PRD/plan → issues |
| `/triage` | Machine à états + thèmes + brief d'agent |
| `/interroge-moi` | Lever les ambiguïtés d'un plan |
| `/cycle-pr` | Cycle complet d'une PR (TDD → merge) |
| `/repercussions` | Impact d'un merge sur les issues ouvertes |
| `/pr-paralleles` | Plusieurs PR en parallèle (worktrees) |
| `/plan-qa` | Écrire un plan de QA |
| `/execution-qa` | Dérouler le plan de QA |
| `/bug-vers-issue` | Consigner un bug en issue |
