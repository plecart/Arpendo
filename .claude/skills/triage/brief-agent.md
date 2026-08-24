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
