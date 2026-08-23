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

## Observation continue (`task-observer`)

Au début de **toute session orientée tâche** — toute interaction où des outils seront utilisés et
un livrable produit — invoquer le skill `task-observer` **avant de commencer le travail**, afin que
les occasions d'améliorer les skills soient captées tout au long de la session.

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
