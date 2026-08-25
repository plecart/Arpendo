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

Second serveur déclaré dans `.mcp.json` : **`mapbox-devkit`** (`@mapbox/mcp-devkit-server`, stdio
via `npx`), qui fournit les outils du skill `mapbox-style-quality` — `validate_expression_tool`,
`validate_geojson_tool`, `color_contrast_checker_tool`, `compare_styles_tool`,
`style_optimization_tool` — plus la gestion des styles et des jetons du compte. Il lit le jeton
dans la variable d'environnement **`MAPBOX_DEVKIT_TOKEN`**, posée dans le bloc `env` de
`.claude/settings.local.json` (fichier ignoré par git, lu par Claude Code au lancement — ni
variable système, ni `.env` de l'app, que Claude Code ne lit pas) : un
jeton **public `pk.`** dédié, portées `styles:read` `styles:list` `styles:download` pour la
validation ; ajouter `styles:write` seulement le jour où un style personnalisé existe, `tokens:*`
jamais. Distinct des deux jetons de l'app (`mapbox-token-security`).

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
| Relire une animation implémentée | `design-motion-principles` | **Mode audit uniquement**, contre les jetons `motion-*` de la spec, et en réponse écrite — pas son rapport HTML, pensé pour le web. Jamais en mode construction : il est pensé CSS/Framer (zéro Flutter) et choisirait des durées déjà fixées |
| Ergonomie tactile (`touch-psychology.md`), Material 3 Android (`platform-android.md`), perf/batterie (`mobile-performance.md`, section Flutter), push et sync hors-ligne (`mobile-backend.md`), checklist de sortie (§10) | `mobile-design` | Sur invocation explicite `/mobile-design`, en ignorant son « Mandatory Reference Reading » : lire **uniquement** le fichier utile. **Ne jamais ouvrir** `mobile-color-system.md` (impose `#000000` en fond) ni `mobile-typography.md` (impose une échelle) — la palette et la typo sont closes |

Sur une demande vague (« améliore cet écran »), **ne pas tirer un skill au hasard** : lire la
section correspondante de la spec, puis choisir dans la table.

## Carte (Mapbox) et navigation — skills gardés pour plus tard

Trois skills sont installés **pour une phase future** ; tant qu'elle n'a pas commencé, ils ne
s'invoquent que dans le cadre ci-dessous, jamais par matching de description :

- `mapbox-style-patterns` — recettes de **styles personnalisés**. La spec §3.2 a tranché **Mapbox
  Standard** (libellés désactivés par `show*Labels`, `lightPreset` pour le mode sombre) : aucun
  style à maintenir. Il ne sert que si cette décision est rouverte — et alors la contrainte
  ΔE ≥ 15 du fond de carte face aux dix couleurs joueur (cadrage §7.2) s'applique au nouveau style.
- `mapbox-data-visualization-patterns` — pour la **couche hexagones de la spec §3.3**
  (`GeoJsonSource` + `FillLayer` + expression sur une propriété) et rien d'autre : pas de
  choroplèthe, heat map ni 3D. Ses exemples sont en GL JS ; transposer vers `mapbox_maps_flutter`
  avec `mapbox-flutter-patterns`.
- `flutter-setup-declarative-routing` — son déclencheur (deep links, App Links, historique
  navigateur) est **post-MVP** (cadrage §7 : lien profond et QR code repoussés). Le MVP navigue
  au `Navigator` de base entre cinq écrans à racine pilotée par l'état (UX §2). Ne pas introduire
  `go_router` avant que le lien profond soit à l'ordre du jour.

`mapbox-style-quality` dépend du serveur MCP **DevKit** de Mapbox (`validate_expression_tool`,
`check_color_contrast_tool`…) déclaré dans `.mcp.json` ; sans lui, le skill n'a aucun outil.

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
