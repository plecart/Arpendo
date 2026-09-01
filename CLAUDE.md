# Pipeline de développement

Ce projet suit une pipeline de dev pilotée par les issues. Le cycle de réalisation d'une PR est
décrit dans [CONTRIBUTING.md](CONTRIBUTING.md) et exécutable via le skill `cycle-pr`.

## Règles permanentes (toujours actives)

@.claude/rules/contraintes.md
@.claude/rules/taille-pr.md
@.claude/rules/cleanup-verbatim.md
@.claude/rules/decisions-vs-doc.md

## Configuration du projet

`.claude/pipeline.config.md` est la **source unique** pour : le dépôt GitHub, le mapping de labels,
la stack, les **commandes du projet** (test / lint / format / typecheck / build), les seuils de
qualité, les **sources de vérité**, les **domaines**, les **zones sensibles** et les **surfaces
exposées**. Ne jamais deviner une commande ni un label — les lire là. Pour créer ou modifier ce
fichier : skill `init-projet`.

Les **sources de vérité** (`documents/reference/`, puis les issues ouvertes) y sont classées par
**rang de normativité**. C'est cette table que lisent la règle `decisions-vs-doc` et le skill
`contradiction` : une décision qui contredit un rang s'arrête, et soit elle est abandonnée, soit
le document est amendé dans la même session.

Les **domaines** servent aussi de thèmes (milestones GitHub). Les **surfaces visibles par un
utilisateur** déclenchent la vérif de fumée avant merge et la proposition de campagne QA en fin de
thème — si ce champ est vide, ces deux propositions ne se déclenchent jamais.

## Vocabulaire

Le glossaire de domaine du projet est [`UBIQUITOUS_LANGUAGE.md`](UBIQUITOUS_LANGUAGE.md), à la
racine : employer ses termes et éviter les synonymes qu'il déclare interdits, dans la portée et
selon les règles d'emploi que son préambule fixe. Les **identifiants techniques** — tables,
colonnes, champs — n'en relèvent pas : ils restent ceux que fixe le cadrage, en anglais.
Respecter les ADR de la zone touchée.

## Documentation des bibliothèques

Pour toute question sur une lib/framework de la stack (API, config, migration de version),
**utiliser en priorité le serveur MCP `context7`** plutôt que la mémoire ou une recherche web :
il renvoie la doc à jour de la lib demandée, ce qui économise des tokens et évite les réponses
périmées. Déclaré dans `.mcp.json` à la racine (scope projet), **sans clé API** : les quotas
de l'offre gratuite s'appliquent. Vérifier avec `claude mcp list`.

Second serveur déclaré dans `.mcp.json` : **`mapbox-devkit`** (`@mapbox/mcp-devkit-server`, stdio),
qui fournit **23 outils**, dont ceux du skill `mapbox-style-quality` : `validate_expression_tool`,
`validate_geojson_tool`, `check_color_contrast_tool`, `compare_styles_tool`, `optimize_style_tool`,
`validate_style_tool` — plus la gestion des styles et des jetons du compte. Il lit le jeton
dans la variable d'environnement **`MAPBOX_DEVKIT_TOKEN`**, posée dans le bloc `env` de
`.claude/settings.local.json` (fichier ignoré par git, lu par Claude Code au lancement — ni
variable système, ni `.env` de l'app, que Claude Code ne lit pas) : un
jeton **public `pk.`** aux quatre portées de lecture `styles:read`, `styles:tiles`, `fonts:read`
et `datasets:read` — la console en coche davantage à la création (`vision:read`), à décocher.
**Ne demander ni `styles:list` ni `styles:write`** : ce sont des portées *secrètes*, Mapbox
émettrait alors un jeton `sk.` — inutilement puissant ici. Les outils
de validation du skill sont du **traitement local** : ils n'appellent
aucune API et fonctionnent même avec un jeton factice. Le jeton ne sert qu'à laisser le serveur
démarrer. Distinct des deux jetons de l'app (`mapbox-token-security`).

**Deux réglages spécifiques à Windows, tous deux nécessaires** — sur un poste Unix, remettre
`"command": "npx"` et supprimer la clé `PATH` :

1. **`cmd /c npx` et non `npx`.** Claude Code lance le serveur par un `spawn` sans shell. Sous
   Windows, `npx` sans extension est un script POSIX que le système ne sait pas exécuter —
   `spawn npx ENOENT`, le serveur remonte en `failed` / `Connection closed`. `cmd /c` résout
   `npx.cmd`.
2. **`PATH` épinglé sur `C:/Program Files/nodejs`.** Le poste porte **deux liens Node
   concurrents** : `C:\Program Files
odejs` → v24.3.0, et `%NVM_SYMLINK%` = `C:
vm4w
odejs`
   → v18.17.1. L'hôte d'extension VS Code résout `npx` par le second et démarre le serveur en
   Node 18, qui ne connaît pas `import … with { type: 'json' }` → `SyntaxError: Unexpected token
   'with'`. Le paquet exige Node ≥ 22. Épingler le `PATH` du serveur le rend indépendant de nvm.

**Diagnostic d'un serveur MCP en `failed` :** ne pas deviner — lire la `stderr` réelle dans
`~/AppData/Roaming/Code/logs/<horodatage>/window1/exthost/Anthropic.claude-code/Claude VSCode.log`.
`node -v` dans un terminal ne dit **rien** de la version que l'hôte d'extension utilisera.

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
| Étendre le thème Dart des jetons (`app/lib/ui/core/theme/`) | `design-system` | Architecture primitif → sémantique → composant, **valeurs recopiées de la spec §1**. Il n'y a **pas** de `tokens.json` : le module Dart est le fichier de jetons machine. Ni CSS, ni Tailwind, ni diapositives |
| Relire une animation implémentée | `design-motion-principles` | **Mode audit uniquement**, contre les jetons `motion-*` de la spec, et en réponse écrite — pas son rapport HTML, pensé pour le web. Jamais en mode construction : il est pensé CSS/Framer (zéro Flutter) et choisirait des durées déjà fixées |
| Ergonomie tactile (`touch-psychology.md`), Material 3 Android (`platform-android.md`), perf/batterie (`mobile-performance.md`, section Flutter), push et sync hors-ligne (`mobile-backend.md`), checklist de sortie (§10) | `mobile-design` | Sur invocation explicite `/mobile-design`, en ignorant son « Mandatory Reference Reading » : lire **uniquement** le fichier utile. **Ne jamais ouvrir** `mobile-color-system.md` (impose `#000000` en fond) ni `mobile-typography.md` (impose une échelle) — la palette et la typo sont closes |

Sur une demande vague (« améliore cet écran »), **ne pas tirer un skill au hasard** : lire la
section correspondante de la spec, puis choisir dans la table.

**Relire ou auditer une spec d'interface** (« relis la description de l'interface », « qu'est-ce
qui cloche dans cette spec ») → skill `audit-spec-ui`, jamais un skill de design : on audite le
document, on ne produit pas d'interface.

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

## Orchestration — Agent Teams à trois étages

La session principale est le **lead** (Fable). Elle garde ce qui demande le plus de jugement :
briefing, planification, arbitrages `decisions-vs-doc`, cleanup pass, review avant merge, dialogue
avec l'utilisateur. Le reste se délègue à des équipiers définis dans `.claude/agents/` — **le
modèle n'est pas choisi par tâche, il est choisi par rôle** au moment de créer l'équipier :

| Rôle | Modèle | Confier |
|---|---|---|
| `developpeur` | Opus | l'implémentation TDD d'un brief borné, la correction de tests rouges, la relecture d'un diff |
| `executant` | Sonnet | tests / lint / format, exploration et cartographie du code, edits entièrement spécifiés |

Invoquer par le nom du rôle : « spawn a teammate using the `executant` agent type to … ». Un
équipier créé sans rôle ni modèle tombe sur Opus (`CLAUDE_CODE_SUBAGENT_MODEL`, réglage
utilisateur) — jamais sur Fable.

**Une commande ponctuelle se lance soi-même.** Un équipier démarre avec un contexte complet ; le
déléguer coûte plus qu'un `git status` ou un `flutter test` isolé. La délégation ne paie que pour
un **bloc de travail** : une tranche d'issue, une suite à faire passer au vert, une cartographie.

Limites connues : une équipe par session, pas d'équipes imbriquées, `/resume` ne restaure pas les
équipiers, mode `in-process` seulement sous Windows / VS Code, et **un rôle ajouté ou modifié dans
`.claude/agents/` n'est visible qu'à la session suivante** (la liste des types est figée au
démarrage — repli : `general-purpose` avec le modèle du rôle).

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
| `/contradiction` | Une décision contredit la doc → amende le document, puis propage |
| `/repercussions` | Impact d'un merge sur les sources de vérité (→ `contradiction`), puis sur les issues ouvertes |
| `/pr-paralleles` | Plusieurs PR en parallèle (worktrees) |
| `/plan-qa` | Écrire un plan de QA |
| `/execution-qa` | Dérouler le plan de QA |
| `/bug-vers-issue` | Consigner un bug en issue |
