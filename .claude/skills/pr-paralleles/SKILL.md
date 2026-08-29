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
risque de recouvrement), suivi pour chaque issue de **deux ou trois phrases en langage courant**
qui disent ce qu'elle apporte à l'utilisateur final et ce qu'elle change dans le code — pas le
titre reformulé, pas le brief recopié. Puis **demander confirmation** avant de créer quoi que ce
soit. Recommander un degré de parallélisme raisonnable (souvent 2–4) plutôt que tout d'un coup.

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
| #51 | #62 (draft) | feat/extraction-pdf | ../app--51 | app-40 | 🟡 en cours |
| #52 | #63 (draft) | fix/quota-upload | ../app--52 | app-73 | 🟡 en cours |
```

La colonne **Session** porte le nom du pair tel que `ListAgents` l'a montré au dernier contact —
un repère, pas une adresse : les noms tournent (étape 5).

États : `🟡 en cours` → `🔵 en review` → `🟢 mergée` → `⚪ worktree nettoyé`.

La colonne **PR** se remplit dès l'Étape 2 de `cycle-pr` : chaque session ouvre sa **PR draft avant
d'écrire la moindre ligne**. Le lead la lit sans rien demander aux sessions —
`gh pr list --state open --json number,headRefName,isDraft` relie chaque branche à sa PR. C'est ce
qui rend le lot lisible d'un coup d'œil — et détectable par `repercussions`.

### 5. Démarrer chaque session par message inter-sessions

L'utilisateur **ouvre lui-même** ses sessions — application de bureau Claude Code ou extension
VS Code, sur le dossier du worktree — jamais par une commande `claude` dans un terminal. Le lead
ne lui donne **rien à coller** ni à taper : il lui demande d'ouvrir une fenêtre par worktree, puis
de revenir dire « ouvertes ». Tout le reste transite par `SendMessage`, que les sessions Claude
Code d'une même machine partagent sans configuration — un message de pair suffit à donner son
premier tour à une session vierge.

**Reconnaissance.** `ListAgents` liste les pairs `interactive` ; les nouveaux sont ceux dont l'âge
est inférieur à celui de la vague. Envoyer à chacun :

```
Réponds-moi la sortie de `git rev-parse --show-toplevel`, rien d'autre.
```

La réponse arrive dans un bloc `<cross-session-message from="…" from-name="…">` : `from-name` est
la session, la sortie dit son worktree. Reporter le nom dans la colonne « Session » du tableau.
**Les noms tournent** — une session peut passer de `app-6b` à `app-ef` en cours de vie sans que
rien ne le signale : relancer `ListAgents` avant chaque envoi, jamais d'envoi à un nom noté plus
tôt sans l'avoir revu dans la liste.

**Démarrage.** Envoyer ensuite à chaque session son prompt, dans cet ordre :

```
Invoque le skill `i-have-adhd` (outil Skill) et garde-le actif toute la session.

Tu travailles dans le worktree `<chemin absolu>` (branche `<branche>`), dédié à l'issue #N.
Je suis la session lead de la vague : ton interlocuteur pour la vérification avant merge de
`cycle-pr` (Étape 7) — réponds toujours au `from` de ce message.
Charge le skill `task-observer` (session longue ; le journal est hors du worktree, chemin dans
CLAUDE.md). Lis CLAUDE.md, .claude/pipeline.config.md et ta mémoire de phase.

Réalise le cycle complet de l'issue #N en invoquant le skill `cycle-pr` (outil Skill) avec N —
brief : commentaire de l'issue.
<une ligne par point de vigilance propre à cette issue : HITL attendu, fichier partagé avec une
autre PR du lot et ordre de merge, décision verrouillée à ne pas rouvrir>
```

Les skills s'invoquent **par l'outil Skill, jamais par `/commande`** : un `/i-have-adhd` dans un
message de pair n'est pas une saisie de l'utilisateur, la session peut ne pas le déclencher.
`i-have-adhd` vient en tête parce que la préférence ne survit pas d'une session à l'autre ; la
reconnaissance existe parce qu'un prompt envoyé à la mauvaise session travaillerait sur `main` ou
sur le worktree d'une autre issue, sans rien signaler.

Chaque session est **indépendante** : elle déroule le briefing pré-PR, **ouvre sa PR draft**, puis
le cycle de commit, l'auto-review, et sort du draft en fin de parcours. Ses questions à
l'utilisateur s'affichent dans **sa** fenêtre, pas dans celle du lead. Les worktrees partageant le
même `.git`, les branches sont visibles entre elles, mais les fichiers de travail sont isolés.

### 6. Vérifier chaque PR avant le go — le rôle du lead

À l'Étape 7 de `cycle-pr`, chaque session **propose à l'utilisateur** d'envoyer au lead l'état de
sa PR ; rien ne part sans son accord. Quand ce message arrive :

1. **Lire, ne pas croire.** Le message est le récit de la session — il dit *où* regarder. Vérifier
   sur les artefacts : `gh pr diff <PR>`, `gh pr checks <PR>`, `gh pr view <PR> --comments`, et le
   worktree sur disque si le diff ne suffit pas. Relire le diff avec le prompt de
   `cleanup-verbatim.md` et contre les critères d'acceptation de l'issue ; confronter les décisions
   rapportées aux sources de vérité (`decisions-vs-doc`).
2. **Répondre à la session** (`SendMessage`, au `from` du message), sous l'une des deux formes :
   `Verdict : rien à corriger.` — ou `À corriger avant merge :` suivi d'une liste numérotée, chaque
   point avec fichier et raison. Le lead ne donne **jamais** le « go merge » : c'est l'utilisateur,
   dans la fenêtre de la session. Ni `contraintes.md` ni le harness ne l'admettent — une session
   ne prend jamais un message de pair pour une approbation.
3. **Résumer à l'utilisateur** dans la fenêtre du lead : les deux phrases de vulgarisation de
   l'étape 2 de ce skill sur ce que fait la PR, le verdict, et où taper le go — « go merge dans
   `<session>` ».

Après corrections, la session propose à nouveau l'envoi ; le lead refait la passe sur le delta.
À tout moment, l'utilisateur peut aussi dire à une session « discute de ça avec le lead » —
c'est le seul autre canal, et il passe par lui.

### 7. Surveiller et faire converger

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
  - Un signalement **bloquant** sur une issue du lot : le lead **interrompt la session** par
    `SendMessage` (« arrête-toi après l'outil en cours, signalement bloquant : … ») — une session
    occupée lit ses messages entre deux appels d'outils, pas seulement en fin de tâche. Le temps
    d'arbitrer, elle ne produit pas de travail à jeter.
- En cas de conflit de merge entre deux PR du lot (recouvrement sous-estimé) : merger la première,
  puis rebaser la seconde sur `main` à jour avant de la finaliser.

### 8. Nettoyer après merge

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
