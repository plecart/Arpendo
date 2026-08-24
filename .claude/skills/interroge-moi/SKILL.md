---
name: interroge-moi
description: Interroger l'utilisateur sans relâche sur un plan, une issue ou un design jusqu'à atteindre une compréhension partagée, en résolvant chaque branche de l'arbre de décision, puis consigner les décisions tranchées. Passage obligé de la pipeline — c'est ce qui fait sortir une issue de l'état needs-interrogation. À utiliser quand l'utilisateur veut stress-tester un plan, se faire cuisiner sur son design, ou mentionne « interroge-moi » ou « cuisine-moi sur ce plan ».
---

# Interroge-moi

Interroge l'utilisateur sans relâche sur chaque aspect du plan jusqu'à atteindre une compréhension
partagée. Descends chaque branche de l'arbre de décision, en résolvant les dépendances entre les
décisions une par une.

- **Une question à la fois.**
- **Chaque question s'accompagne de ta réponse recommandée** — interroger n'est pas se décharger de
  l'analyse sur l'utilisateur.
- **Si une question peut être résolue en explorant le code, explore le code** plutôt que de
  demander.

## Sa place dans la pipeline

Ce skill n'est pas seulement un outil à la demande : c'est le **garde-fou obligatoire** avant tout
développement.

- `triage` y passe toute issue destinée à `ready-for-agent` ou `ready-for-human` — l'issue porte
  l'état `needs-interrogation` tant que la session n'a pas eu lieu.
- `cycle-pr` le rattrape à son Étape 1 si le travail n'y est jamais passé (issue non interrogée,
  brief marqué `⚠️ Non interrogée au triage`, ou demande directe sans issue).

## Consigner les décisions — l'étape qui n'est pas optionnelle

**Une interrogation dont les conclusions ne sont pas écrites n'a pas eu lieu.** Ce qui est tranché
ici sera relu des jours plus tard, par une autre session, sans aucun accès à cette conversation.

À la fin de la session, écrire :

- **Les points tranchés** → dans les « Décisions verrouillées » du brief d'agent de l'issue si la
  session part d'une issue ; dans le briefing pré-PR sinon.
- **Les questions restées ouvertes** → en notes de triage sur l'issue, pour que la prochaine
  session sache ce qui manque encore.

Puis, si la session partait d'une issue en `needs-interrogation`, dire à l'utilisateur que l'issue
peut passer à `ready-for-agent` (ou `ready-for-human`) — la transition elle-même appartient à
`triage`.
