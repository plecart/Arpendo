---
name: vers-issues
description: Découpe un plan, une spec ou un PRD en issues indépendamment récupérables sur GitHub (via `gh`) en utilisant des tranches verticales tracer-bullet. À utiliser quand l'utilisateur veut convertir un plan en issues, créer des tickets d'implémentation, ou découper le travail en issues.
---

# Vers Issues

Découpe un plan en issues indépendamment récupérables en utilisant des tranches verticales (tracer bullets).

Le dépôt GitHub et le mapping de labels sont dans `.claude/pipeline.config.md` — sinon lancer `init-projet`.

## Processus

### 1. Rassembler le contexte

Travaille à partir de ce qui est déjà présent dans le contexte de la conversation. Si l'utilisateur passe une référence d'issue (numéro d'issue, URL ou chemin) en argument, récupère-la depuis GitHub (via `gh`) et lis son corps complet et ses commentaires.

### 2. Explorer la base de code (optionnel)

Si tu n'as pas encore exploré la base de code, fais-le pour comprendre l'état actuel du code. Les titres et descriptions d'issues doivent utiliser le vocabulaire du glossaire métier du projet, et respecter les ADR de la zone que tu touches.

### 3. Esquisser les tranches verticales

Découpe le plan en issues **tracer bullet**. Chaque issue est une fine tranche verticale qui traverse TOUTES les couches d'intégration de bout en bout, et NON une tranche horizontale d'une seule couche.

Les tranches peuvent être 'HITL' ou 'AFK'. Les tranches HITL nécessitent une interaction humaine, par exemple une décision d'architecture ou une revue de design. Les tranches AFK peuvent être implémentées et mergées sans interaction humaine. Préfère AFK à HITL lorsque c'est possible.

<vertical-slice-rules>
- Chaque tranche livre un chemin étroit mais COMPLET à travers chaque couche (schéma, API, UI, tests)
- Une tranche terminée est démontrable ou vérifiable à elle seule
- Préfère de nombreuses tranches fines à quelques tranches épaisses
</vertical-slice-rules>

### 4. Interroger l'utilisateur

Présente le découpage proposé sous forme de liste numérotée. Pour chaque tranche, montre :

- **Titre** : nom court et descriptif
- **Type** : HITL / AFK
- **Bloquée par** : quelles autres tranches (le cas échéant) doivent être terminées d'abord
- **User stories couvertes** : quelles user stories cette tranche adresse (si le matériel source en contient)

Demande à l'utilisateur :

- La granularité semble-t-elle correcte ? (trop grossière / trop fine)
- Les relations de dépendance sont-elles correctes ?
- Faut-il fusionner ou découper davantage certaines tranches ?
- Les bonnes tranches sont-elles marquées comme HITL et AFK ?

Itère jusqu'à ce que l'utilisateur approuve le découpage.

### 5. Publier les issues sur GitHub

Pour chaque tranche approuvée, publie une nouvelle issue sur GitHub (via `gh`). Utilise le template de corps d'issue ci-dessous. Applique le label de triage `needs-triage` pour que chaque issue entre dans le flux de triage normal.

**Rattache chaque issue à son thème** quand le domaine est évident : le découpage vient d'un plan, tu sais donc de quel domaine relève chaque tranche. Utilise les **domaines** de `.claude/pipeline.config.md` et le milestone homonyme (`gh issue edit <n> --milestone "<Domaine>"`) — voir `triage/themes-milestones.md`. Si aucun domaine ne couvre une tranche, laisse le thème vide et signale-le : c'est soit du hors-périmètre, soit un domaine manquant dans la config. Rattacher ici évite à `triage` de le refaire issue par issue.

Publie les issues dans l'ordre des dépendances (bloqueurs d'abord) afin de pouvoir référencer les identifiants d'issues réels dans le champ « Bloquée par ».

**Critères reposant sur un service tiers.** Quand un critère d'acceptation suppose une capacité d'un fournisseur (restriction d'usage, plafond, quota, révocation, rotation), ne jamais la recopier d'un document du projet sans l'avoir vérifiée : ajouter la ligne « vérifié à la source le <date> : <doc du fournisseur> », ou marquer le critère « ⛔ à vérifier avant engagement ». Une contre-mesure copiée sans vérification survit à tous les rangs de doc et n'éclate qu'au moment le plus coûteux — la console ouverte.

<issue-template>
## Parent

Une référence à l'issue parente sur GitHub (si la source était une issue existante, sinon omettre cette section).

## Quoi construire

Une description concise de cette tranche verticale. Décris le comportement de bout en bout, pas l'implémentation couche par couche.

## Critères d'acceptation

- [ ] Critère 1
- [ ] Critère 2
- [ ] Critère 3

## Bloquée par

- Une référence au ticket bloquant (le cas échéant)

Ou « Aucun - peut démarrer immédiatement » s'il n'y a aucun bloqueur.

</issue-template>

Ne ferme NI ne modifie aucune issue parente.
