---
name: init-projet
description: Met en place et maintient la pipeline de dev d'un projet, quelle que soit la stack — git + dépôt GitHub, profil du projet (langages, commandes de test/lint/build, domaines, zones sensibles), mapping rôle→label GitHub, template (.claude/rules, CLAUDE.md, CONTRIBUTING, CI générée), skills maison + publics, serveur MCP context7. Persiste tout dans .claude/pipeline.config.md. À utiliser au démarrage d'un projet, quand un autre skill signale « config de pipeline absente », ou pour reconfigurer (« change la commande de test », « ajoute un domaine », « réajuste les labels »).
---

# Init projet

Met en place, en une passe, toute la pipeline de dev dans un projet — et reste **le point d'entrée
unique pour la reconfigurer** ensuite. Source du template : ce dépôt `boilerplate` (dossier
`template/` + dossier `skills/`).

La configuration est persistée dans **`.claude/pipeline.config.md`** à la racine du projet
(versionnée). C'est le fichier que tous les autres skills lisent pour savoir quelles commandes
lancer, quels labels utiliser et quels sont les domaines du projet.

> **Aucune hypothèse de stack.** Ce skill ne présuppose ni langage, ni framework, ni gestionnaire
> de paquets. Tout ce qui est spécifique au projet est **demandé puis persisté**, jamais codé en
> dur.

> **Un document généré n'affirme que ce que le générateur a constaté.** Toute phrase de la forme
> « X est installé / configuré » posée par un template est une assertion non testée qui deviendra
> fausse en silence. Écrire à la place un pointeur vérifiable (« déclaré dans <fichier>, vérifier
> avec <commande> »), et ne poser la ligne qu'après avoir constaté l'artefact attendu (entrée dans
> `.mcp.json`, label créé, commande qui répond). De même, **toute référence croisée vers un
> document utilise un identifiant structurel stable** (numéro de section, ancre de titre) — jamais
> un numéro de ligne, qui périme à la première édition.

## Deux modes

- **Amorçage** — `.claude/pipeline.config.md` absent : dérouler tout le process.
- **Reconfiguration** — le fichier existe : le lire, afficher l'état actuel, demander ce qu'il faut
  changer, puis ne rejouer que les étapes concernées (typiquement 3 → 7). Ne jamais écraser en
  silence une valeur déjà renseignée.

## Process

### 1. Localiser le template

Déterminer le chemin du dépôt `boilerplate` (le demander si nécessaire). On y lira `template/` et
`skills/`.

### 2. Initialiser git + le dépôt GitHub

- Si le projet n'est pas un dépôt git : `git init` + premier commit.
- Lire `git remote -v`. Si un remote GitHub existe, le proposer comme dépôt cible (`owner/repo`).
- Sinon, proposer de le créer : `gh repo create <owner>/<repo> --private --source=. --remote=origin`
  (demander public/privé).
- Brancher trunk-based sur `main`.

### 3. Profil du projet — détecter, puis faire confirmer

**Ne rien inventer en silence.** Inspecter le repo, proposer des valeurs pré-remplies, et faire
corriger par l'utilisateur. Ce qui reste ambigu après inspection se **demande**.

**Signaux à inspecter** (liste non exhaustive — s'adapter à ce qu'on trouve) :

- **Manifeste** : `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `composer.json`,
  `Gemfile`, `pom.xml`, `build.gradle`, `*.csproj`, `mix.exs`…
- **Gestionnaire de paquets** : le lockfile présent (`pnpm-lock.yaml`, `uv.lock`, `Cargo.lock`…).
- **Commandes déjà déclarées** : scripts du manifeste, cibles d'un `Makefile` / `justfile` /
  `Taskfile.yml`, workflows CI existants sous `.github/workflows/`.
- **Arborescence** : les dossiers de premier niveau sous la racine du code, qui suggèrent les
  domaines.
- **Version de runtime** : `.nvmrc`, `.tool-versions`, contrainte du manifeste, image Docker.

Présenter le résultat comme un **tableau à valider**, valeur par valeur. Pour chaque commande
absente ou introuvable, demander — ou enregistrer `n/a` si le projet n'a pas cette étape (un projet
sans type-checker met `n/a`, il ne faut pas en inventer un).

Les **domaines** sont la brique la plus utile à long terme : ce sont les périmètres nommés que
`vers-issues`, `triage` et `plan-qa` réutiliseront pour cadrer leur travail. Les faire nommer
explicitement, en vocabulaire **métier** (`Facturation`, `Ingestion`), pas en chemins techniques —
avec le ou les chemins en regard.

> Les domaines sont aussi la **source de vérité des thèmes** de `triage` : chaque milestone GitHub
> reprend le nom d'un domaine, à l'identique. Peu de domaines larges et stables valent mieux qu'une
> liste fine — un domaine par issue produirait un milestone par issue.

Les **zones sensibles** alimentent les points d'arrêt humains de `.claude/rules/contraintes.md`
(migrations, paiements, écrans à valider visuellement…).

Les **surfaces** disent ce que le projet expose réellement — c'est ce qui empêche `plan-qa` de
générer une section frontend pour une CLI ou des vérifications de base pour une lib. Les faire
nommer explicitement plutôt que de les déduire d'un archétype : une CLI, une lib, un service et une
application web n'ont presque rien en commun ici. Le sous-ensemble « visible par un utilisateur »
est ce qui déclenche la vérif de fumée avant merge et la proposition de campagne QA en fin de
thème ; s'il est vide, ces deux propositions ne se déclenchent jamais.

### 4. Établir le mapping de labels

Les skills raisonnent en **rôles canoniques**. Le dépôt utilise des **chaînes de labels** réelles.
Établir la correspondance (proposer ces valeurs par défaut) :

| Rôle canonique | Type | Label par défaut | Couleur |
|---|---|---|---|
| bug | catégorie | `bug` | `d73a4a` |
| enhancement | catégorie | `enhancement` | `a2eeef` |
| needs-triage | état | `needs-triage` | `fbca04` |
| needs-info | état | `needs-info` | `d4c5f9` |
| needs-interrogation | état | `needs-interrogation` | `d876e3` |
| ready-for-agent | état | `ready-for-agent` | `0e8a16` |
| ready-for-human | état | `ready-for-human` | `1d76db` |
| wontfix | état | `wontfix` | `ffffff` |
| qa-plan | suivi | `qa-plan` | `0e8a16` |
| qa-finding | suivi | `qa-finding` | `b60205` |

Demander à l'utilisateur s'il veut des chaînes différentes (ex. labels existants du projet).

### 5. Écrire `.claude/pipeline.config.md`

Utiliser ce gabarit, puis confirmer à l'utilisateur :

<gabarit-config>
# Configuration pipeline

## Dépôt GitHub
- repo : `owner/repo`
- branche trunk : `main`

## Stack
- langages : <ex. TypeScript, Go>
- frameworks : <ex. Next.js, Fiber — ou "aucun">
- gestionnaire de paquets : <ex. pnpm, uv, cargo, go mod>
- runtime + version : <ex. node 22, python 3.12, go 1.23>

## Commandes du projet
Lues par `cycle-pr`, `execution-qa` et la génération de CI. `n/a` = étape absente du projet.
- install      : <cmd>
- test         : <cmd>                  # suite complète
- test ciblé   : <cmd> <chemin|motif>   # une seule cible, pour la boucle TDD
- lint         : <cmd>
- format       : <cmd>                  # écrit
- format:check : <cmd>                  # vérifie sans écrire
- typecheck    : <cmd | n/a>
- build        : <cmd | n/a>
- run local    : <cmd | n/a>

## Qualité
- seuil de couverture : <ex. 80 % | aucun>
- gates bloquants en CI : <ex. lint, format:check, typecheck, test>
- services requis en CI : <ex. postgres:16, redis:7 | aucun>

## Périmètre
- domaines (nom métier → chemin) — servent aussi de thèmes/milestones à `triage` :
  - <Domaine A> : <chemin/>
  - <Domaine B> : <chemin/>
- zones sensibles (arrêt humain avant commit) : <ex. migrations, paiements, écrans publics>
- hors périmètre : <ce que le projet ne couvre pas / ne doit pas toucher>
- surfaces exposées — ce que la QA a le droit de vérifier ; ne lister que ce qui existe :
  <ex. API HTTP, interface web, CLI, persistance, traitements asynchrones, fichiers produits,
  comptes utilisateurs / isolation>
- surfaces visibles par un utilisateur : <sous-ensemble des précédentes ; déclenche la vérif de
  fumée de `cycle-pr` et la proposition de campagne QA — vide si le projet n'expose rien>

## Langue
- skills / issues / PRD / descriptions : français
- identifiants du code : <ex. anglais — observer le code existant à l'initialisation>
- commentaires / docstrings / noms de tests : <ex. français>
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
- <liste retenue>
- Écartés : <skill> — <raison>
</gabarit-config>

### 6. Créer les labels manquants dans GitHub

Pour chaque label du mapping absent du dépôt :
`gh label create <nom> --description "<rôle>" --color <couleur>`. Confirmer ce qui a été créé.

### 7. Copier le template + générer la CI

Copier depuis `boilerplate/template/` vers la racine du projet :

- `CLAUDE.md` (importe les règles via `@.claude/rules/...`)
- `.claude/rules/` (contraintes, cleanup-verbatim, taille-pr)
- `.claude/commands/` (une commande par skill de la pipeline — voir étape 8)
- `.claude/settings.json` (permissions de base ; fusionner s'il en existe déjà un)
- `CONTRIBUTING.md` (pointeur vers `cycle-pr`)

Puis **générer `.github/workflows/ci.yml`** à partir de `template/.github/workflows/ci.yml`, qui
est un modèle à trous :

- Remplacer chaque `{{CMD_*}}` par la commande correspondante de la section « Commandes ».
- **Supprimer purement et simplement** toute étape dont la commande vaut `n/a` — ne jamais laisser
  un placeholder ni une étape vide dans le fichier généré.
- Remplir `{{SETUP_STEPS}}` avec l'action de mise en place officielle de l'écosystème, version
  épinglée depuis « runtime + version » (`actions/setup-node`, `astral-sh/setup-uv`,
  `actions/setup-go`, `actions/setup-java`…).
- Remplir `{{SERVICES}}` depuis « services requis en CI », ou retirer le bloc s'il n'y en a pas.
- **Conserver le garde `if:` et le type `ready_for_review`.** Ils forment une paire : le garde
  empêche la CI de tourner sur les PR en draft (que `cycle-pr` ouvre avant tout code), et le type
  `ready_for_review` est ce qui la déclenche au passage en ready. Retirer l'un sans l'autre donne
  soit une CI qui ne tourne jamais, soit une CI qui tourne sur tous les commits de développement.

Montrer le `ci.yml` généré avant de l'écrire.

**Runtime épinglé — une version, des fournisseurs.** Si le profil déclare un gestionnaire de
version (FVM, pyenv, nvm, asdf, mise…), séparer *quelle version* de *qui la fournit* :

- La version a **une source unique** (fichier d'épinglage) lue par tous les environnements.
- Le fichier de commandes route le runtime **à travers le gestionnaire par défaut** — un épinglage
  que les commandes n'empruntent pas est décoratif, pire qu'aucun — mais via une **variable
  surchargeable** (`flutter := env('FLUTTER_CMD', 'fvm flutter')`) : la valeur par défaut est le
  chemin qui a besoin d'isolation (le poste de dev).
- La CI **surcharge la variable** et provisionne le runtime avec l'action qui lit le **même**
  fichier d'épinglage — jamais un canal indépendant (`channel: stable` flottant) : deux mécanismes
  de provisionnement pour la même version divergent silencieusement.
- À la génération, vérifier qu'aucune recette n'invoque le binaire nu d'un runtime épinglé, et
  simuler la résolution des deux environnements.

**`.gitignore` — généré depuis le profil, puis testé.** Générer le fichier à partir des **chemins
déclarés** (une section par langage présent, motifs indépendants de la profondeur `**/` dès qu'un
paquet vit hors racine), jamais d'un gabarit mono-paquet dont les motifs sont ancrés à la racine.
Puis **tester mécaniquement** avec `git check-ignore` sur une liste de chemins fabriqués depuis le
profil : ceux qui doivent être exclus, et les lockfiles/sources qui doivent rester suivis. Un
fichier de motifs ne se relit pas, il se teste.

### 8. Déployer les skills MAISON et leurs commandes

Copier les skills de la pipeline depuis `boilerplate/skills/` vers **`.claude/skills/`** et
**`.agents/skills/`** du projet :

`init-projet`, `vers-prd`, `vers-issues`, `triage`, `interroge-moi`, `cycle-pr`, `repercussions`,
`pr-paralleles`, `plan-qa`, `execution-qa`, `bug-vers-issue`.

Chaque skill a une **commande homonyme** dans `template/.claude/commands/` (`/triage`, `/cycle-pr`,
`/plan-qa`…), copiée à l'étape 7. Ce sont des **wrappers fins** : elles ne dupliquent pas le
process, elles invoquent le skill en lui passant `$ARGUMENTS`. La source de vérité reste le
`SKILL.md`.

**Un skill retiré du projet ⇒ sa commande aussi.** Après la copie, vérifier qu'il reste exactement
une commande par skill déployé — une commande orpheline pointe vers un skill inexistant.

### 9. Repérer les automatisations utiles, puis installer les skills publics

**Point de départ — le plugin `claude-code-setup`** (Anthropic, lecture seule) : il analyse le
projet — structure, dépendances, langages — et propose des automatisations dans **cinq
catégories** : serveurs MCP, skills, hooks, sous-agents, commandes. Le lancer avec « recommande
des automatisations pour ce projet ». S'il n'est pas installé, le proposer à l'utilisateur depuis
l'annuaire des plugins et **continuer sans lui** plutôt que de bloquer l'amorçage.

1. **Récolter les recommandations** — lancer `claude-code-setup`. Il ne rend que le **top 1–2 par
   catégorie** ; demander explicitement une catégorie (« quels skills ? », « quels hooks ? ») pour
   obtenir 3–5 options. Ses sorties *MCP* alimentent l'**étape 10** ; ses sorties
   *hooks / sous-agents / commandes* sont à proposer telles quelles.
2. **Repli si `claude-code-setup` est indisponible** — plugin non installé, session distante sans
   accès au catalogue — ne pas s'arrêter là, dérouler dans cet ordre :
   1. le skill **`find-skills`**, s'il est installé : il consulte le classement skills.sh (les plus
      installés, donc les plus éprouvés) avant toute recherche CLI ;
   2. `npx skills find <langage>`, `<framework>`, `testing` — recherche brute par mot-clé ;
   3. le catalogue https://skills.sh/ à la main.

   Ne **jamais** proposer un set en dur : un projet Go n'a rien à faire avec des skills Django.
   **Dire en une ligne que le repli a servi**, et que relancer `init-projet` une fois le plugin
   installé complétera la liste — l'étape 9 se rejoue seule, sans toucher au reste de la config.
3. **Présenter en cases à cocher** — l'utilisateur active/désactive chaque ligne. Ne **jamais**
   rien installer sans confirmation.
4. **Installer** la sélection (vérifier la CLI : `npx skills --version`) :
   `npx skills add <owner/repo> -s <skill> --agent claude-code -y`.
   - **Répéter `-s` pour chaque skill** — la forme `-s a,b,c` séparée par des virgules ne marche pas.
   - **Vérifier `ls .claude/skills/` après chaque `add`** : un skill tiré d'un gros dépôt
     communautaire en amène souvent d'autres. Retirer les intrus — chaque skill coûte du contexte
     à chaque session.
   - **Vérifier la compatibilité avec la stack *avant* d'installer**, pas après. Beaucoup de skills
     « design » ou « frontend » supposent un DOM (React / Tailwind) et sont inertes sur une stack
     qui n'en a pas.
   - Un outil recommandé n'est pas toujours un skill : certains s'installent en **plugin**, en
     **paquet** (npm, uv/pipx) ou en **serveur MCP**. Ne pas forcer `npx skills add` sur eux.
5. **Enregistrer** la sélection dans la section « Skills du projet » de
   `.claude/pipeline.config.md` — **et les candidats écartés avec leur raison**, sinon la passe
   suivante les repropose.

### 10. Installer les serveurs MCP utiles (context7)

Reprendre ici les **serveurs MCP** remontés par `claude-code-setup` à l'étape 9, en plus de
context7 qui, lui, est installé dans tous les cas.

**context7** donne à Claude la **doc à jour des bibliothèques**, résolue à la demande, au lieu de la
deviner de mémoire ou de la chercher sur le web — c'est un **gain de tokens** direct, d'autant plus
utile que la stack s'appuie sur des libs qui évoluent vite.

1. Vérifier s'il est déjà présent : `claude mcp list` (idempotent — ne pas réinstaller si listé).
2. Sinon, l'ajouter (transport HTTP distant, portée utilisateur, sans clé — suffisant, débit
   limité) :

   ```
   claude mcp add --scope user --transport http context7 https://mcp.context7.com/mcp
   ```

   Pour un débit plus élevé, une clé (gratuite sur `context7.com/dashboard`) se passe par en-tête.
   **Ne jamais la committer** : la garder en portée `user` (config locale hors dépôt), ou via
   variable d'environnement si on préfère `--scope project` (`.mcp.json` versionné) :

   ```
   claude mcp add --scope user --header "CONTEXT7_API_KEY: <clé>" --transport http context7 https://mcp.context7.com/mcp
   ```

   Variante locale (process local au lieu du serveur distant) :
   `claude mcp add --scope user context7 -- npx -y @upstash/context7-mcp`.
3. Une fois installé, **l'utiliser en priorité** pour toute question sur une lib de la stack (une
   note le rappelle dans le `CLAUDE.md` du template).

### 11. Vérifier que les commandes déclarées fonctionnent

Avant de committer, lancer réellement les commandes `lint`, `typecheck` et `test` de la config.
Une commande déclarée mais fausse est pire qu'absente : elle casse `cycle-pr` et la CI au premier
usage. Corriger la config si l'une échoue pour cause d'erreur de saisie.

Deux pièges de diagnostic à cette étape :

- **Un binaire installé dans cette session peut être introuvable** : le shell hérite du PATH figé
  au démarrage, antérieur à l'installation. Avant de conclure à un échec d'installation, augmenter
  explicitement le PATH avec les répertoires d'installation connus, ou vérifier l'existence du
  binaire sur disque.
- **Un contrôle « doctor » en échec accuse ce qu'il contrôle autant que lui-même.** Avant de
  mettre à jour l'outil de contrôle (l'action la plus facile, pas la plus probable), établir ce
  que le contrôle exécute réellement et si cette cible a changé récemment — lire le message
  d'erreur de la cible, pas seulement le verdict du contrôleur.

### 12. Commit d'amorçage

D'abord vérifier qu'aucun fichier suivi ne viole les règles d'ignore — `.gitignore` n'agit pas
rétroactivement sur des fichiers déjà stagés :

```
git ls-files -i -c --exclude-standard   # doit sortir vide ; sinon git rm --cached les fichiers listés
git add -A && git commit -m "chore: amorçage pipeline de dev"
```

### 13. Récapituler

Afficher : dépôt GitHub, profil du projet retenu (stack + commandes + domaines), labels créés, CI
générée, skills maison déployés, skills publics installés, context7 disponible, et les prochaines
étapes (`vers-prd` ou `vers-issues` pour démarrer la planification).

## Checklist finale

- [ ] git + remote GitHub en place, branche `main`
- [ ] profil du projet confirmé par l'utilisateur (aucune valeur devinée en silence)
- [ ] `.claude/pipeline.config.md` écrit, sans placeholder résiduel
- [ ] labels manquants créés dans GitHub
- [ ] `CLAUDE.md` + `.claude/rules/` + `settings.json` + `CONTRIBUTING.md` copiés
- [ ] `ci.yml` généré depuis les commandes réelles, sans `{{PLACEHOLDER}}` ni étape `n/a`
- [ ] skills maison déployés dans `.claude/skills/` et `.agents/skills/`
- [ ] `.claude/commands/` copié — exactement une commande par skill déployé, aucune orpheline
- [ ] skills publics cochés installés (choisis d'après la stack, pas d'un set en dur)
- [ ] serveur MCP context7 disponible (`claude mcp list`)
- [ ] commandes `lint` / `typecheck` / `test` vérifiées en local
- [ ] commit d'amorçage fait

## Note pour les autres skills

Quand un skill a besoin du dépôt, du vocabulaire de labels, des commandes ou des domaines, il lit
`.claude/pipeline.config.md`. S'il est absent ou incomplet, lancer `init-projet`.
