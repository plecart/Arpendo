---
name: vers-prd
description: Transforme le contexte de la conversation actuelle en PRD et le publie sur le dépôt GitHub du projet. À utiliser lorsque l'utilisateur veut créer un PRD à partir du contexte actuel.
---

Ce skill prend le contexte de la conversation actuelle ainsi que la compréhension de la base de code et produit un PRD. Ne pas interroger l'utilisateur sur le **contenu produit** — c'est une synthèse de ce qui est déjà su. Le **seul** point de validation est celui de l'étape 2 (liste des modules et périmètre de tests), présenté **en une fois**, avec une recommandation par question. Si le contexte est un corpus documentaire clos, les interprétations posées (là où deux documents semblent diverger) font partie de cette validation unique.

Le dépôt GitHub et le mapping de labels doivent être dans `.claude/pipeline.config.md` — sinon lancer le skill `init-projet`.

## Process

1. Explore le dépôt pour comprendre l'état actuel du codebase, si ce n'est pas déjà fait. Utilise le vocabulaire du glossaire métier du projet tout au long du PRD, et respecte les ADR existants dans la zone que tu modifies.

2. Esquisse les principaux modules que tu devras construire ou modifier pour mener à bien l'implémentation. Cherche activement les opportunités d'extraire des modules profonds (deep modules) qui peuvent être testés de manière isolée.

Un module profond (par opposition à un module superficiel) est un module qui encapsule beaucoup de fonctionnalités derrière une interface simple, testable et qui change rarement.

Vérifie avec l'utilisateur que ces modules correspondent à ses attentes. Vérifie avec l'utilisateur pour quels modules il souhaite que des tests soient écrits.

3. Rédige le PRD en utilisant le template ci-dessous, puis publie-le sur le dépôt GitHub du projet (via `gh`). Applique le **label de nature `prd`** (mapping dans `.claude/pipeline.config.md`) — **ni rôle d'état, ni thème** : un PRD est un document parent que `vers-issues` découpe sans jamais le modifier ni le fermer ; la machine à états de `triage` est conçue pour des unités de travail (un état, un thème) et ne sait pas le faire avancer. Un PRD étiqueté `needs-triage` resterait indéfiniment dans la file « requiert l'attention ».

**Règle de rédaction — l'état courant seul.** Un PRD est lu par des agents, et un agent n'a pas de mémoire de lecture : tout ce qui figure dans le document est vrai au même titre. Écrire chaque section à la voix affirmative, sans date de révision, sans bloc « Avant / Après », sans mention de ce qui a été envisagé puis abandonné. Quand une révision est intégrée plus tard, réécrire le passage **comme s'il avait toujours été ainsi**, et chercher toutes les occurrences de la valeur révisée avant de clore. Le raisonnement et l'historique vivent dans un fichier d'archive séparé, marqué non normatif. Une justification garde sa place tant qu'elle explique pourquoi la règle actuelle est celle-là ; elle part dès qu'elle explique pourquoi elle a changé.

<prd-template>

## Énoncé du problème

Le problème auquel l'utilisateur est confronté, du point de vue de l'utilisateur.

## Solution

La solution au problème, du point de vue de l'utilisateur.

## User Stories

Une LONGUE liste numérotée de user stories. Chaque user story doit être au format :

1. En tant que <acteur>, je veux <fonctionnalité>, afin de <bénéfice>

<user-story-example>
1. En tant que client mobile d'une banque, je veux voir le solde de mes comptes, afin de prendre de meilleures décisions concernant mes dépenses
</user-story-example>

Cette liste de user stories doit être extrêmement exhaustive et couvrir tous les aspects de la fonctionnalité.

## Décisions d'implémentation

Une liste des décisions d'implémentation qui ont été prises. Cela peut inclure :

- Les modules qui seront construits/modifiés
- Les interfaces de ces modules qui seront modifiées
- Les clarifications techniques apportées par le développeur
- Les décisions architecturales
- Les changements de schéma
- Les contrats d'API
- Les interactions spécifiques

N'inclus PAS de chemins de fichiers spécifiques ni d'extraits de code. Ils risquent de devenir obsolètes très rapidement.

## Décisions de test

Une liste des décisions de test qui ont été prises. Inclus :

- Une description de ce qui fait un bon test (ne tester que le comportement externe, pas les détails d'implémentation)
- Quels modules seront testés
- Les exemples existants sur lesquels s'appuyer (c.-à-d. des types de tests similaires dans la base de code)

## Hors périmètre

Une description de ce qui est hors périmètre pour ce PRD.

## Notes complémentaires

Toute note complémentaire concernant la fonctionnalité.

</prd-template>
