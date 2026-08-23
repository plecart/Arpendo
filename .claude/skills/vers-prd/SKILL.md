---
name: vers-prd
description: Transforme le contexte de la conversation actuelle en PRD et le publie sur le dépôt GitHub du projet. À utiliser lorsque l'utilisateur veut créer un PRD à partir du contexte actuel.
---

Ce skill prend le contexte de la conversation actuelle ainsi que la compréhension de la base de code et produit un PRD. N'interroge PAS l'utilisateur — synthétise simplement ce que tu sais déjà.

Le dépôt GitHub et le mapping de labels doivent être dans `.claude/pipeline.config.md` — sinon lancer le skill `init-projet`.

## Process

1. Explore le dépôt pour comprendre l'état actuel du codebase, si ce n'est pas déjà fait. Utilise le vocabulaire du glossaire métier du projet tout au long du PRD, et respecte les ADR existants dans la zone que tu modifies.

2. Esquisse les principaux modules que tu devras construire ou modifier pour mener à bien l'implémentation. Cherche activement les opportunités d'extraire des modules profonds (deep modules) qui peuvent être testés de manière isolée.

Un module profond (par opposition à un module superficiel) est un module qui encapsule beaucoup de fonctionnalités derrière une interface simple, testable et qui change rarement.

Vérifie avec l'utilisateur que ces modules correspondent à ses attentes. Vérifie avec l'utilisateur pour quels modules il souhaite que des tests soient écrits.

3. Rédige le PRD en utilisant le template ci-dessous, puis publie-le sur le dépôt GitHub du projet (via `gh`). Applique le label de triage `needs-triage` pour qu'il entre dans le flux de triage normal.

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
