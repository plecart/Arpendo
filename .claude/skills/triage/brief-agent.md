# Rédiger des briefs d'agent

Un brief d'agent est un commentaire structuré publié sur une issue GitHub lorsqu'elle passe à `ready-for-agent`. C'est la spécification de référence à partir de laquelle un agent AFK travaillera. Le corps de l'issue original et la discussion constituent le contexte — le brief d'agent est le contrat.

## Principes

### La durabilité avant la précision

L'issue peut rester en `ready-for-agent` pendant des jours ou des semaines. Le code va évoluer entre-temps. Rédige le brief de façon à ce qu'il reste utile même si des fichiers sont renommés, déplacés ou refactorisés.

- **À faire** : décrire les interfaces, les types et les contrats comportementaux
- **À faire** : nommer les types spécifiques, les signatures de fonctions ou les formes de configuration que l'agent doit rechercher ou modifier
- **À éviter** : faire référence à des chemins de fichiers — ils deviennent obsolètes
- **À éviter** : faire référence à des numéros de ligne
- **À éviter** : supposer que la structure d'implémentation actuelle restera la même

### Un brief n'est jamais contredit en silence

Le brief est le contrat que `cycle-pr` exécute — le corps de l'issue et sa discussion ne sont que
le contexte. Quand une réconciliation post-merge (`repercussions`), un amendement de spec ou une
décision falsifie une ligne du brief, le brief est **amendé dans le même geste** : édition en place
du commentaire existant, jamais un second brief concurrent, jamais un correctif qui ne toucherait
que le corps de l'issue. Une entrée de journal qui dit « pas celui cité dans le brief » sans que le
brief change laisse deux specs en contradiction — et c'est la fausse qu'on exécute.

### Comportemental, pas procédural

Décris **ce que** le système doit faire, pas **comment** l'implémenter. L'agent explorera le code à neuf et prendra ses propres décisions d'implémentation.

- **Bon :** « Le type `SkillConfig` devrait accepter un champ optionnel `schedule` de type `CronExpression` »
- **Mauvais :** « Ouvre src/types/skill.ts et ajoute un champ schedule à la ligne 42 »
- **Bon :** « Quand un utilisateur lance `/triage` sans argument, il doit voir un résumé des issues qui requièrent son attention »
- **Mauvais :** « Ajoute un switch dans la fonction de gestion principale »

### Critères d'acceptation complets

L'agent doit savoir quand il a terminé. Chaque brief d'agent doit comporter des critères d'acceptation concrets et testables. Chaque critère doit être vérifiable indépendamment.

- **Bon :** « Lancer `gh issue list --label needs-triage` retourne les issues passées par la classification initiale »
- **Mauvais :** « Le triage doit fonctionner correctement »

### Limites de périmètre explicites

Indique ce qui est hors périmètre. Cela empêche l'agent de sur-développer ou de faire des suppositions sur des fonctionnalités adjacentes.

### Une dépendance verrouillée est une dépendance compilée

Un brief qui **verrouille un paquet tiers** engage l'agent sur lui. Avant de l'écrire, si le
paquet n'a pas été publié depuis plus d'un an, ou si le SDK épinglé a connu une rupture depuis sa
dernière publication : **prouver qu'il compile** avec le SDK du projet, dans un scratch (un fichier
qui importe et instancie un symbole du paquet, compilé — pas un simple `pub add --dry-run` ou
`uv add --dry-run`, qui ne prouve que la résolution des versions). Inscrire dans le brief l'âge du
paquet, le successeur éventuel, et **un critère « un test atteint le module qui importe le
paquet »** : une table de constantes qui n'est référencée nulle part n'est pas compilée, et les
gates du projet restent verts avec une dépendance cassée. Même exigence pour toute **propriété
affirmée** du paquet (taille, optimisation, performance) : la **mesurer**, pas la citer — rédiger
la décision avec sa preuve (« compile et mesuré à X »), jamais « se résout ».

### Rédiger les décisions verrouillées

Des règles de rédaction, chacune née d'un brief qui a fait dérailler une session :

- **Une décision négative nomme ce qui survit au rejet.** Quand l'option rejetée est une
  *combinaison*, « écarté : X seul » est ambigu — écrire « écarté : X **sans** Y ; X reste
  nécessaire ». Lu vite, « écarté » se comprend comme « ne pas le mettre », et l'implémentation
  part sur une configuration qui ne peut pas fonctionner.
- **Une exception verrouillée est une liste, et une liste se produit par recherche.** Toute règle
  de la forme « les X qui viennent de Y ne bougent pas » est accompagnée de la liste exhaustive
  de ces X, obtenue en cherchant dans Y **au moment du triage** — jamais reprise d'une liste
  écrite dans un document tiers, jamais de mémoire.
- **Un découpage en lots se valide par ses tests.** Avant d'écrire « si > N fichiers, découper :
  (1) … ; (2) … », répondre pour chaque lot : « avec quoi ses tests tournent-ils ? ».
  L'infrastructure qui fait tourner les tests (schéma, compose, fixtures) va dans le premier lot
  ou dans un lot antérieur à ses consommateurs.
- **Un critère qui exige une preuve nomme son canal.** Pour des preuves visuelles (« captures en
  PR ») : ni l'API GitHub ni `gh` ne savent joindre une image — prescrire la branche orpheline
  `captures/pr-<n>` (liens `?raw=true`, supprimée après merge) **et les moyens d'obtention** (quel
  lanceur, quel réglage produit chaque rendu demandé), sinon chaque PR improvise un canal
  différent.
- **Une capacité d'un fournisseur tiers se vérifie à la source.** Tout critère d'acceptation qui
  repose sur un mécanisme d'un service tiers (restriction, plafond, quota, révocation) porte une
  ligne « vérifié à la source le <date> : <doc du fournisseur> » — ou, à défaut, le marqueur
  « ⛔ à vérifier avant engagement ». Une contre-mesure recopiée sans vérification monte de rang
  à chaque copie et éclate au moment le plus coûteux, la console ouverte.
- **Un ordre de gestes chez un tiers cite sa source, geste par geste.** Pour une issue HITL dont
  les gestes s'exécutent dans une console, chez un registrar ou un fournisseur de paiement, ne
  jamais écrire d'« ordre conseillé » de mémoire : soit chaque geste porte l'URL officielle qui
  fixe ses préconditions (« réserver le nom de package exige le certificat de la clé d'upload,
  donc geste 2 avant geste 1 »), soit l'ordre est marqué « ⚠️ non vérifié — à confronter à la doc
  du fournisseur avant exécution ». Rien dans le dépôt ne rougit quand l'ordre devient faux, et
  `cycle-pr` le retraite à son Étape 1 comme une hypothèse.

## Modèle

```markdown
## Brief d'agent

**Catégorie :** bug / enhancement
**Résumé :** description en une ligne de ce qui doit se passer

**Comportement actuel :**
Décris ce qui se passe actuellement. Pour les bugs, c'est le comportement cassé.
Pour les enhancements, c'est l'état existant sur lequel la fonctionnalité s'appuie.

**Comportement souhaité :**
Décris ce qui doit se passer une fois le travail de l'agent terminé.
Sois précis sur les cas limites et les conditions d'erreur.

**Interfaces clés :**
- `NomDuType` — ce qui doit changer et pourquoi
- type de retour de `nomDeFonction()` — ce qu'elle retourne actuellement vs ce qu'elle devrait retourner
- forme de la config — toute nouvelle option de configuration nécessaire

**Critères d'acceptation :**
- [ ] Critère 1 précis et testable
- [ ] Critère 2 précis et testable
- [ ] Critère 3 précis et testable

**Hors périmètre :**
- Élément qui NE doit PAS être modifié ou traité dans cette issue
- Fonctionnalité adjacente qui pourrait sembler liée mais qui est distincte
```

## Exemples

### Bon brief d'agent (bug)

```markdown
## Brief d'agent

**Catégorie :** bug
**Résumé :** La troncature de description de skill coupe en plein mot, produisant une sortie cassée

**Comportement actuel :**
Quand une description de skill dépasse 1024 caractères, elle est tronquée à exactement
1024 caractères sans tenir compte des limites de mots. Cela produit des descriptions
qui se terminent en plein mot (par ex. « Utiliser quand l'utilisateur veut confi »).

**Comportement souhaité :**
La troncature doit s'effectuer à la dernière limite de mot avant 1024 caractères
et ajouter « ... » pour indiquer la troncature.

**Interfaces clés :**
- Le champ `description` du type `SkillMetadata` — aucun changement de type nécessaire,
  mais la logique de validation/traitement qui le remplit doit respecter
  les limites de mots
- Toute fonction qui lit le frontmatter de SKILL.md et en extrait la description

**Critères d'acceptation :**
- [ ] Les descriptions de moins de 1024 caractères restent inchangées
- [ ] Les descriptions de plus de 1024 caractères sont tronquées à la dernière limite de mot
      avant 1024 caractères
- [ ] Les descriptions tronquées se terminent par « ... »
- [ ] La longueur totale, « ... » compris, ne dépasse pas 1024 caractères

**Hors périmètre :**
- Modifier la limite de 1024 caractères elle-même
- La prise en charge de descriptions multilignes
```

### Bon brief d'agent (enhancement)

```markdown
## Brief d'agent

**Catégorie :** enhancement
**Résumé :** Ajouter la prise en charge du répertoire `.out-of-scope/` pour suivre les demandes de fonctionnalités rejetées

**Comportement actuel :**
Quand une demande de fonctionnalité est rejetée, l'issue est fermée avec un label `wontfix`
et un commentaire. Il n'existe aucune trace persistante de la décision ou du raisonnement.
Les demandes similaires futures obligent le mainteneur à se souvenir ou à rechercher
la discussion antérieure.

**Comportement souhaité :**
Les demandes de fonctionnalités rejetées doivent être documentées dans des fichiers
`.out-of-scope/<concept>.md` qui consignent la décision, le raisonnement et les liens vers toutes
les issues qui ont demandé la fonctionnalité. Lors du triage de nouvelles issues, ces fichiers
doivent être vérifiés pour détecter les correspondances.

**Interfaces clés :**
- Le format de fichier Markdown dans `.out-of-scope/` — chaque fichier doit comporter un
  titre `# Nom du concept`, une ligne `**Décision :**`, une ligne `**Raison :**`,
  et une liste `**Demandes antérieures :**` avec des liens vers les issues
- Le workflow de triage doit lire tous les fichiers `.out-of-scope/*.md` tôt
  et confronter les issues entrantes avec eux par similarité de concept

**Critères d'acceptation :**
- [ ] Fermer une fonctionnalité en wontfix crée/met à jour un fichier dans `.out-of-scope/`
- [ ] Le fichier inclut la décision, le raisonnement et le lien vers l'issue fermée
- [ ] Si un fichier `.out-of-scope/` correspondant existe déjà, la nouvelle issue est
      ajoutée à sa liste « Demandes antérieures » plutôt que de créer un doublon
- [ ] Pendant le triage, les fichiers `.out-of-scope/` existants sont vérifiés et remontés
      quand une nouvelle issue correspond à un rejet antérieur

**Hors périmètre :**
- La correspondance automatique (l'humain confirme la correspondance)
- La réouverture de fonctionnalités précédemment rejetées
- Les rapports de bug (seuls les rejets d'enhancements vont dans `.out-of-scope/`)
```

### Mauvais brief d'agent

```markdown
## Brief d'agent

**Résumé :** Corriger le bug de triage

**Quoi faire :**
Le truc du triage est cassé. Regarde le fichier principal et corrige-le.
La fonction autour de la ligne 150 a le problème.

**Fichiers à modifier :**
- src/triage/handler.ts (ligne 150)
- src/types.ts (ligne 42)
```

C'est mauvais parce que :
- Aucune catégorie
- Description vague (« le truc du triage est cassé »)
- Référence des chemins de fichiers et des numéros de ligne qui deviendront obsolètes
- Aucun critère d'acceptation
- Aucune limite de périmètre
- Aucune description du comportement actuel vs souhaité
