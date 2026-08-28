---
name: pr-paralleles
description: Orchestre plusieurs PR en parallèle via des git worktrees — sélectionne des issues ready-for-agent non bloquées et à faible recouvrement de fichiers, crée un worktree + une branche par issue, prépare une session par worktree, tient un tableau de bord, et nettoie après merge. Utiliser pour développer plusieurs issues en même temps, paralléliser la réalisation de PR, ou lancer une vague de travail AFK.
---

# PR parallèles

Permet de travailler sur **plusieurs PR en même temps** sans qu'elles se marchent dessus, en
isolant chaque unité de travail dans son propre **git worktree** (un dossier de travail + une
branche distincts, partageant le même dépôt `.git`). Chaque worktree se développe dans **sa propre
session Claude Code**, en suivant `cycle-pr`.

Prérequis : `.claude/pipeline.config.md` existe (sinon lancer `init-projet`).

## Quand l'utiliser

- Plusieurs issues `ready-for-agent` sont prêtes et indépendantes.
- L'utilisateur veut « faire plusieurs PR en même temps ».

## Process

### 1. Rassembler les issues candidates

Lister les issues prêtes :

```
gh issue list --label ready-for-agent --state open --json number,title,labels
```

Lire l'« agent brief » de chacune (commentaire posé par `triage`). En extraire la **liste des
fichiers/zones probablement touchés** (les briefs décrivent des interfaces et des comportements,
pas des chemins — déduire les zones du code à partir de là).

### 2. Sélectionner un lot sûr

Ne retenir que des issues :

- **sans bloqueur en attente** — vérifier le champ « Bloquée par » de l'issue / du brief ; tout
  bloqueur doit être déjà mergé.
- **à faible recouvrement de fichiers/zones** entre elles — deux issues qui touchent le même
  module sont des candidates au conflit de merge ; les exécuter en série, pas en parallèle.

Présenter le lot proposé à l'utilisateur sous forme de tableau (issue, titre, zones touchées,
risque de recouvrement) et **demander confirmation** avant de créer quoi que ce soit. Recommander
un degré de parallélisme raisonnable (souvent 2–4) plutôt que tout d'un coup.

### 3. Créer un worktree + une branche par issue

Pour chaque issue retenue, depuis `main` à jour :

```
git fetch origin
git worktree add ../<repo>--<numéro-issue> -b <type>/<slug> origin/main
```

- `<type>` = `feat` / `fix` / `chore` / `docs` / `refactor` selon la catégorie de l'issue.
- `<slug>` = description courte en kebab-case.
- Le dossier `../<repo>--<numéro-issue>` est un **frère** du dépôt, pour ne pas polluer l'arbre.

### 4. Tenir le tableau de bord

Maintenir un fichier `PR-PARALLELES.md` à la racine du dépôt (et le tenir à jour à chaque
changement d'état) :

```markdown
# PR en parallèle — <date>

| Issue | PR | Branche | Worktree | Session | État |
|-------|----|---------|----------|---------|------|
| #51 | #62 (draft) | feat/extraction-pdf | ../app--51 | prompt remis | 🟡 en cours |
| #52 | #63 (draft) | fix/quota-upload | ../app--52 | prompt remis | 🟡 en cours |
```

États : `🟡 en cours` → `🔵 en review` → `🟢 mergée` → `⚪ worktree nettoyé`.

La colonne **PR** se remplit dès l'Étape 2 de `cycle-pr` : chaque session ouvre sa **PR draft avant
d'écrire la moindre ligne**. C'est ce qui rend le lot lisible d'un coup d'œil — et détectable par
`repercussions`.

### 5. Préparer le prompt de chaque session

L'utilisateur **ouvre lui-même** ses sessions — application de bureau Claude Code ou extension
VS Code, sur le dossier du worktree — jamais par une commande `claude` dans un terminal. Le skill
ne donne donc pas une commande : il donne, pour chaque worktree, **un prompt prêt à coller**, dans
un bloc de code, précédé d'une seule ligne : « ouvre une session sur `<chemin absolu du
worktree>` et colle ceci ».

Le prompt, dans cet ordre :

```
/i-have-adhd

Tu travailles dans le worktree `<chemin absolu>` (branche `<branche>`), dédié à l'issue #N.
Vérifie-le d'abord : `git rev-parse --show-toplevel` doit rendre ce chemin, sinon arrête-toi.
Charge le skill `task-observer` (session longue ; le journal est hors du worktree, chemin dans
CLAUDE.md). Lis CLAUDE.md, .claude/pipeline.config.md et ta mémoire de phase.

Réalise le cycle complet de l'issue #N avec /cycle-pr N — brief : commentaire de l'issue.
<une ligne par point de vigilance propre à cette issue : HITL attendu, fichier partagé avec une
autre PR du lot et ordre de merge, décision verrouillée à ne pas rouvrir>
```

Le prompt commence par `/i-have-adhd` parce que la préférence ne survit pas d'une session à
l'autre ; la vérification du chemin existe parce qu'un prompt collé dans la mauvaise session
travaillerait sur `main` ou sur le worktree d'une autre issue, sans rien signaler.

Chaque session est **indépendante** : elle déroule le briefing pré-PR, **ouvre sa PR draft**, puis
le cycle de commit, l'auto-review, et sort du draft en fin de parcours. Les worktrees partageant le
même `.git`, les branches sont visibles entre elles, mais les fichiers de travail sont isolés.

**Récupérer le numéro de PR draft de chaque session** dès qu'il est créé et le reporter dans le
tableau : c'est le lien qui permet ensuite de classer l'issue comme « en vol ».

### 6. Surveiller et faire converger

- `git worktree list` montre tous les worktrees actifs.
- Quand une PR passe en review puis est mergée, mettre à jour `PR-PARALLELES.md`.
- Après chaque merge, la session concernée déroule la passe `repercussions` (Étape 8 de
  `cycle-pr`). **C'est le moment le plus dangereux d'une vague parallèle** : les autres issues du
  lot sont en cours de développement, et leurs sessions ont déjà lu leur spec.
  - `repercussions` les détecte comme **« en vol »** (via les PR ouvertes et ce tableau de bord) :
    il **n'édite pas** leur corps et **ne change pas** leurs labels, il dépose un commentaire sur
    **leur PR ouverte**, que `cycle-pr` traite à son Étape 6.
  - **Tenir `PR-PARALLELES.md` à jour est donc fonctionnel, pas décoratif** : une ligne périmée
    (issue mergée encore marquée en cours, ou worktree actif absent du tableau) fait mal classer
    une issue — et une issue en vol traitée comme dormante se fait réécrire sa spec sous les pieds.
  - Un signalement **bloquant** sur une issue du lot : mettre sa session en pause le temps
    d'arbitrer, plutôt que de la laisser produire du travail à jeter.
- En cas de conflit de merge entre deux PR du lot (recouvrement sous-estimé) : merger la première,
  puis rebaser la seconde sur `main` à jour avant de la finaliser.

### 7. Nettoyer après merge

Une fois une PR mergée et sa branche supprimée côté distant :

```
git worktree remove ../<repo>--<numéro-issue>
git branch -d <type>/<slug>
```

Marquer la ligne `⚪ worktree nettoyé` dans le tableau. Quand tout le lot est nettoyé, supprimer
`PR-PARALLELES.md` (ou archiver le tableau dans les notes du projet).

## Règles

- **Jamais deux worktrees sur des zones qui se recouvrent fortement** sans le signaler — c'est la
  première cause de conflits.
- Chaque session suit `cycle-pr` à la lettre (le parallélisme ne dispense d'aucune étape, ni du
  cleanup pass verbatim).
- **Jamais d'auto-merge**, même en parallèle : chaque PR attend son « go » humain.
- Ne jamais créer de worktree sur une branche déjà active dans un autre worktree.
