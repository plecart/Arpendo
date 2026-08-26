# Contribuer

Le développement suit une pipeline pilotée par les issues. **La source de vérité du process n'est
pas ce fichier** : c'est le skill `cycle-pr` (déroulé pas à pas) et les règles permanentes dans
[.claude/rules/](.claude/rules/). Ce document n'en donne que la carte.

Chaque étape ci-dessous a une commande dédiée (`/triage`, `/cycle-pr`…) — voir
[.claude/commands/](.claude/commands/).

## Le flux en une page

0. **Configurer** — `init-projet` écrit `.claude/pipeline.config.md` (dépôt, labels, stack,
   commandes, domaines, surfaces). À relancer dès qu'une de ces valeurs change.
1. **Planifier** — `vers-prd` (conversation → PRD) → `vers-issues` (PRD → petites issues) →
   `triage` (machine à états, rattachement au thème, « agent brief »).
2. **Interroger** — `interroge-moi`, **obligatoire** : `ready-for-agent` et `ready-for-human` ne
   s'atteignent que via l'état `needs-interrogation`. Les décisions tranchées sont écrites dans
   l'issue, pas laissées dans une conversation.
3. **Implémenter** — `cycle-pr` : briefing pré-PR → **PR draft ouverte avant tout code** → TDD
   red-green-refactor → cycle `modif → test → cleanup → test → commit` → auto-review → `gh pr ready`
   → review → vérif de fumée → merge. Plusieurs PR en parallèle : `pr-paralleles` (worktrees).
3bis. **Amender** — `contradiction` dès qu'une décision de conversation contredit une source de
   vérité (`documents/reference/`, issues ouvertes) : le document est amendé dans la session, ou la
   décision est abandonnée. Déclenché par la règle `decisions-vs-doc`, à n'importe quel moment.
4. **Répercuter** — `repercussions` après chaque merge : corrige le corps des issues dont la
   planification est devenue fausse. Lancé automatiquement en fin de `cycle-pr`.
5. **Valider** — `plan-qa` → `execution-qa` → `bug-vers-issue`, proposé quand un **thème se vide**
   de ses issues ouvertes. La QA ne re-teste jamais ce que la CI couvre déjà.

## Les règles qui ne se négocient pas

Voir [.claude/rules/](.claude/rules/) (chargées automatiquement via `CLAUDE.md`) :

- **Aucun commit cassé**, jamais d'auto-merge, jamais de force-push — `contraintes.md`
- **Cleanup pass verbatim** à chaque relecture (DRY / KISS / YAGNI) — `cleanup-verbatim.md`
- **Format des commits** : `type(scope): description`, préfixe EN + description FR ; PR ≤ ~10
  fichiers / ~500 lignes — `taille-pr.md`
- **Aucune décision ne contredit la doc en silence** : deux citations, arrêt, puis amendement ou
  abandon — `decisions-vs-doc.md`

## Deux choses qui surprennent au début

- **La PR existe avant le code.** Elle est ouverte en draft dès le départ, avec `Closes #N`. C'est
  ce qui signale qu'une issue est en cours de développement — sans quoi une autre session pourrait
  réécrire sa spec en croyant que personne n'y travaille.
- **La CI ne tourne pas sur une draft.** Aucun check n'apparaît tant que la PR n'est pas passée en
  ready. Ce n'est pas une CI cassée : les tests tournent en local à chaque commit.
