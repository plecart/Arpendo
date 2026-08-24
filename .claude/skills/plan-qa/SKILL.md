---
name: plan-qa
description: À utiliser quand l'utilisateur veut planifier la QA d'un lot de travaux récemment implémentés — généralement après avoir fusionné des issues issues d'un PRD. Déclencheurs : « écris un plan de QA », « plan QA pour les issues #X #Y », « plan de QA pour le PRD », « je veux faire la QA de ce qu'on vient de livrer », ou après une session d'implémentation TDD.
---

# Rédacteur de plan de QA

Construis un plan de QA exhaustif et exécutable, cadré sur un lot de travaux précis, et publie-le sous forme d'issue GitHub avec un corps à cases à cocher. Le plan est ensuite exécuté par `execution-qa`, et les bugs trouvés pendant l'exécution sont déposés par `bug-vers-issue`.

## Principe fondamental

Le plan de QA doit être **cadré** (uniquement ce qui vient d'être livré), **exhaustif** (aucune hypothèse cachée) et **ancré dans la réalité** (vraies routes, vrais composants, vraies tables, vrais fixtures — pas inventés). Les checklists génériques sont un mauvais signe.

### La règle qui décide de tout : ne pas doubler la CI

**Une case n'a le droit d'exister que si un test automatisé ne peut structurellement pas la couvrir.**

`cycle-pr` a déjà imposé du TDD avec suite verte à chaque commit, un cleanup verbatim, une auto-review de branche et des gates CI. Réécrire « la suite de tests passe » ou « l'API répond 200 » dans un plan de QA, c'est faire refaire à la main ce qu'une machine vient de faire — et c'est ce qui rend un plan si long que personne ne le déroule.

Ce qui mérite une case, c'est ce qu'aucun test ne voit :

- le **rendu réel** et les états d'interface (vide / chargement / succès / erreur) ;
- la **console et le réseau** du navigateur, les erreurs avalées par un wrapper générique ;
- l'**isolation entre comptes** avec de vrais jetons distincts ;
- un **job asynchrone** qui atteint réellement son état terminal, succès *et* échec ;
- les **effets de bord réels** : fichier écrit, ligne persistée, message émis ;
- l'**ergonomie** : bouton désactivé pendant l'attente, message compréhensible, polling qui s'arrête.

En cas de doute sur une case : « est-ce qu'un test aurait pu attraper ça ? » Si oui, elle sort du plan — et si ce test n'existe pas, c'est une issue pour `cycle-pr`, pas une case de QA.

### Les surfaces viennent de la config, pas d'un modèle en dur

Avant de rédiger, lire `.claude/pipeline.config.md` (sections **Stack**, **Périmètre**) et en déduire **quelles surfaces ce projet possède réellement**. Une CLI n'a pas de section frontend ; une lib n'a ni base ni worker ; un projet mono-utilisateur n'a pas d'isolation inter-comptes.

N'inclure que les surfaces existantes. Ne jamais générer une section pour une surface absente, même marquée « N/A » — c'est du bruit. En revanche, **si une surface existe et n'est pas couverte, l'omission doit être signalée** explicitement.

Si la config ne permet pas de trancher, **demander** plutôt que supposer.

## Entrées (un mode parmi quatre)

Mode 1 — **Référence PRD** : `/plan-qa #42` où `#42` est une issue PRD. Récupère le corps du PRD, puis `gh issue list --search "parent #42" --state all` (ou recherche les issues qui mentionnent `#42`) pour rassembler toutes les issues d'implémentation qui en découlent.

Mode 2 — **Liste explicite d'issues** : `/plan-qa #51 #52 #53`. Récupère le corps et les critères d'acceptation de chaque issue.

Mode 3 — **Thème terminé** : `/plan-qa "Facturation"` où l'argument est un thème (milestone). C'est le mode le plus courant, proposé automatiquement par `repercussions` quand le dernier ticket d'un thème se ferme. Récupère les issues du milestone : `gh issue list --milestone "<thème>" --state all --json number,title,body`.

Mode 4 — **Aucun argument** : liste les thèmes dont toutes les issues sont fermées et qui n'ont pas encore d'issue `qa-plan`, et demande lequel recetter. S'il n'y en a aucun, demande à l'utilisateur quelles issues sont dans le périmètre — **ne jamais deviner un périmètre de QA**, un plan mal cadré est un plan qu'on ne déroule pas.

Dans tous les modes :
- Récupère le PRD s'il est connu. Sers-t'en pour la section « Vue d'ensemble ».
- Récupère le corps et les critères d'acceptation de chaque issue dans le périmètre.
- Lance `git log --grep="#<numéro-issue>"` pour chaque issue dans le périmètre afin de trouver les commits de livraison.
- Lis les diffs de ces commits (ou au moins les chemins de fichiers modifiés) pour que le plan s'ancre aux **vraies** routes, composants, tables, fichiers, variables d'environnement.

## Processus

### 1. Inspecte le dépôt

- Lis `.claude/pipeline.config.md` (stack, commandes, domaines, surfaces), `CLAUDE.md`, `UBIQUITOUS_LANGUAGE.md` (ou glossaire équivalent), `docs/`, `README`, le fichier de commandes du projet, puis les points d'entrée réels de **chaque surface déclarée** — selon le projet : routeur/contrôleurs, définition des commandes CLI, routes d'interface, schéma/migrations, définition des jobs. Plus tout fixture touché par les commits dans le périmètre.
- Utilise `rg`/`rg --files` d'abord ; vérifie localement tout endpoint, commande ou chemin incertain avant de l'inclure comme instruction.
- Identifie le langage métier du projet. Le plan doit employer ces termes.

### 2. Décide où vit le plan

Essaie GitHub d'abord :
- Si `gh` est installé et que le cwd est un dépôt avec un remote GitHub, le plan est une **issue GitHub** portant le label `qa-plan` (crée le label s'il manque).
- Sinon, replie-toi sur un fichier markdown à `docs/qa/qa-plan-<slug>.md` (slug à partir du titre du PRD ou d'une courte étiquette de périmètre).

Indique à l'utilisateur quel mode tu utilises avant de rédiger.

### 3. Rédige le plan

Utilise `references/gabarit-plan-qa.md` comme squelette. Le plan a deux couches :

**Couche A — Phases transversales** (uniquement celles qui correspondent à des surfaces réelles du projet) :
- Phase 0 — Préliminaires (env, build, démarrage — commandes `install` / `build` / `run local` de la config)
- Phase 1 — Sécurité & Propriété (auth, isolation entre comptes) — **seulement si le projet a de l'authentification**
- Phase R — Régression (les flux existants fonctionnent toujours après la nouvelle livraison) — toujours inclure
- Phase Finale — Définition du Terminé

**Couche B — Blocs de fonctionnalité par issue**, intercalés entre les phases transversales dans l'ordre des dépendances. Un bloc par issue dans le périmètre. Utilise `references/exemple-bloc-issue.md` comme modèle. Chaque bloc inclut :

- Référence de l'issue (`#N — Titre`, lien)
- Référence au PRD source (le cas échéant)
- Critères d'acceptation (reformulés en cases `- [ ]`, copiés/normalisés depuis l'issue)
- **Une section par surface que le projet possède réellement**, chacune ancrée à du vérifié :
  API/CLI (vraies routes ou commandes, vrais codes de sortie), interface (vraies URLs, composants, états), persistance (vraies tables ou chemins), traitements asynchrones (vrais services et flux de logs), artefacts produits (vrais fichiers, formats)
- Commandes exactes ou actions utilisateur
- Résultats attendus avant chaque action
- Règle d'arrêt
- Indices de sévérité pour les défaillances probables

Une surface que le projet n'a pas **ne produit aucune section**. Ne pas l'écrire pour la marquer « N/A ».

Utilise `references/taxonomie-couverture.md` comme feuille d'indices de couverture — n'en tire que les sections pertinentes pour les fonctionnalités dans le périmètre. Ne colle pas la taxonomie entière.

### 4. Rends-le exhaustif dans le détail et la vue d'ensemble

Pour chaque bloc par issue, demande-toi :
- Ai-je couvert chaque critère d'acceptation par au moins une case ?
- **Chaque case survit-elle à la question « un test automatisé aurait-il pu attraper ça ? »** Si la réponse est oui, la case sort du plan.
- Chaque surface **que ce projet possède** est-elle considérée ? (Les surfaces absentes ne produisent rien ; une surface présente mais non couverte doit être signalée.)
- S'il y a une interface : les états d'erreur, vides, de chargement et de succès sont-ils tous listés ?
- S'il y a des comptes utilisateurs : les variantes propriétaire / accès croisé sont-elles testées pour chaque ressource liée à un utilisateur ?
- S'il y a des traitements asynchrones : atteignent-ils un état terminal vérifié, succès **et** échec ?
- S'il y a des fichiers entrants ou produits : les originaux sont-ils préservés, les invalides rejetés, les artefacts conformes au format annoncé ?

Pour le plan dans son ensemble :
- Y a-t-il une section **Vue d'ensemble** en haut indiquant : objectif du PRD, issues dans le périmètre, comportements visibles par l'utilisateur dans le périmètre, hors périmètre ?
- L'ordre des dépendances tient-il — une surface n'est testée qu'après celles dont elle dépend (ex. sécurité avant les fonctionnalités protégées ; primitives avant ce qui les consomme) ?
- La **Définition du Terminé** est-elle explicite et binaire ?

### 5. Ancre chaque commande à une réalité vérifiée

- Utilise des variables d'environnement pour la répétabilité : `$QA_RUN`, `$TOKEN_A`, `$TOKEN_B`, `$CLIENT_ID`, etc.
- Requêtes sur la persistance : uniquement après avoir vérifié les noms réels contre les migrations ou les modèles.
- Logs : toujours **bornés** (`--tail=200`), jamais un `--follow` non borné. Une preuve QA doit être petite et copiable-collable.
- Instructions d'interface : inclus l'URL ou la commande, le compte, l'état de départ (session vierge / préservée) et où lire les erreurs.
- Codes de sortie, statuts, états terminaux et volumes attendus font partie des « résultats attendus », pas des arrière-pensées.

### 6. Marque explicitement les décisions de politique

Quand un comportement dépend du produit ou est ambigu, marque la case avec `Décision QA :` et indique :
- Comportement actuel (d'après le code)
- Risque
- Politique recommandée
- Ce qui change si l'utilisateur choisit autrement

Le compagnon d'exécution enregistre le choix de l'utilisateur lorsqu'il y parvient.

### 7. Montre le brouillon à l'utilisateur, puis publie

- Affiche le corps complet du brouillon (ou un résumé plus le corps complet dans un bloc replié) et demande : « Publier ceci comme issue GitHub avec le label `qa-plan`, ou réviser ? »
- À l'approbation, publie :
  - GitHub : `gh issue create --label qa-plan --title "Plan QA: <périmètre>" --body-file <brouillon>`
  - Repli markdown : écris le fichier, affiche le chemin.
- Affiche l'URL de l'issue ou le chemin du fichier. Indique à l'utilisateur que c'est ce qu'il passe à `execution-qa` (ou que le compagnon découvrira automatiquement l'issue `qa-plan` la plus récente).

## Sortie : titre et labels de l'issue GitHub

- Titre : `Plan QA: <court périmètre>` — ex. `Plan QA: PRD #42 (base de connaissances v2)` ou `Plan QA: issues #51 #52 #53`.
- Labels : `qa-plan`. Crée le label s'il manque (`gh label create qa-plan --description "Checklist QA active" --color "0E8A16"`).
- Ne ferme AUCUNE issue source. Ne modifie PAS le PRD.

## Passe finale avant publication

Avant d'envoyer le corps à `gh issue create`, vérifie :

- [ ] La section **Vue d'ensemble** nomme le PRD, les issues dans le périmètre, les comportements dans le périmètre, les éléments hors périmètre.
- [ ] Chaque issue dans le périmètre a son propre bloc par issue.
- [ ] Chaque critère d'acceptation de chaque issue dans le périmètre apparaît comme au moins une case à cocher.
- [ ] **Aucune case ne re-teste ce que la CI couvre déjà** (suite de tests, lint, typecheck, build).
- [ ] **Aucune section ne porte sur une surface que le projet n'a pas** (déduite de `.claude/pipeline.config.md`).
- [ ] Aucune case n'utilise une route, table, fichier, variable d'environnement ou fixture non vérifié contre le dépôt.
- [ ] *S'il y a des traitements asynchrones* : chacun a des vérifications d'état terminal (succès ET échec).
- [ ] *S'il y a des fichiers entrants ou produits* : chacun a des vérifications d'artefact (chemin, taille, format) et de persistance.
- [ ] Chaque échec d'action utilisateur a une vérification de visibilité de l'erreur UI attendue.
- [ ] Chaque phase transversale a une règle d'arrêt.
- [ ] Les paliers de sévérité (bloquant / majeur / mineur) sont définis une fois en haut.
- [ ] Le gabarit de saisie d'échec (depuis `execution-qa/references/gabarit-intake-echec.md` ou en ligne) est inclus pour usage pendant l'exécution.
- [ ] La Définition du Terminé est binaire (`phases requises vertes, bloquants corrigés ou acceptés, ...`).
- [ ] Français, vocabulaire du domaine, pas de fuite de jargon interne.
- [ ] Aucun marqueur de remplissage (`TODO`, `<à compléter>`, etc.) ne subsiste.

## Erreurs fréquentes

| Erreur | Correction |
|---|---|
| **Cases qui refont le travail de la CI** (« les tests passent », « le lint est vert ») | Les supprimer. Le plan ne contient que ce qu'un test ne peut pas voir. |
| **Sections pour des surfaces inexistantes** (frontend sur une CLI, BDD sur une lib) | Déduire les surfaces de `.claude/pipeline.config.md`. Une surface absente ne produit aucune section, pas même un « N/A ». |
| Le plan couvre des zones qu'aucune issue récente n'a touchées | Recadrer. Uniquement les phases de couche A pour le transversal, les blocs de couche B liés aux issues dans le périmètre. |
| Vérifications génériques (« l'API marche », « l'UI s'affiche ») | Ancrer à des routes/composants/états/codes de statut attendus spécifiques. |
| Jobs asynchrones sans vérifications d'état terminal | Ajouter les chemins explicites succès ET échec, avec l'état persisté attendu pour chacun. |
| Fichiers entrants/produits sans assertion sur l'artefact | Vérifier chemin, taille, format, préservation de l'original, et la trace persistée correspondante. |
| Un unique état « réussi/échoué » par phase | Chaque surface du projet est suivie séparément — ne jamais les fusionner en un verdict. |
| Longues queues de logs (`docker logs --follow`) | Utiliser des queues bornées. Les logs en preuve QA doivent être petits et copiables-collables. |
| Langues mélangées | Français, vocabulaire du domaine, pas de fuite de jargon interne. Les preuves collées par l'utilisateur restent dans leur forme native. |
