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

## Réponse « quelles sont les bonnes pratiques ? »

Quand l'utilisateur répond à une question par « fais selon les bonnes pratiques » (ou équivalent),
il demande le **cadre**, pas une opinion. Répondre en deux temps : (1) l'état de l'art en 3-5
points nommés ; (2) chaque point confronté aux contraintes écrites du projet (rules, cadrage,
décisions closes), avec retenu/écarté. Puis :

- **S'il a annoncé en ouverture qu'il délègue** (« choisis selon les bonnes pratiques ») → donner
  le cadre pour la traçabilité et **verrouiller la recommandation dans le même tour**, sans
  reposer la question. Consigner la décision comme « déléguée sur reco ».
- **Sinon** → reposer la question une fois. Si la même réponse revient, verrouiller et le dire.
  **Jamais de troisième tour** : une réponse identique à une question reposée n'est pas une
  nouvelle information, c'est le signal que la boucle doit se fermer.

## Une option que l'utilisateur ne peut pas évaluer n'est pas une décision

Avant de poser un arbitrage, vérifier si la décision dépend d'un savoir que l'interlocuteur peut
ne pas avoir — coût récurrent, terme technique, conséquence différée. Si oui : expliciter dans le
corps du message ce que chaque terme veut dire **concrètement**, ce que ça coûte, et ce qui se
passe si on ne fait rien, avant de proposer les options. Bannir les libellés qui supposent le
vocabulaire du domaine, et ne marquer « (Recommandé) » que si l'utilisateur peut évaluer la
recommandation — sinon c'est l'agent qui décide sous couvert de consultation, et l'accord obtenu
n'est qu'un acquiescement à son autorité.

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

**Chaque décision nomme son propriétaire avant d'être écrite** — le bon endroit est celui que lira
la session qui *réalisera* le point, pas celle qui l'a discuté :

1. **L'issue interrogée**, si c'est elle qui réalise le point.
2. **Une autre issue ouverte**, si c'est elle qui le réalisera → amender **son corps**, pas
   seulement le brief courant.
3. **Aucune issue n'existe encore** → la story du PRD (ou le document de rang supérieur) reçoit un
   rappel daté, que `vers-issues` retrouvera.

Dans les deux derniers cas, le brief courant garde une ligne « porté par #N » pour la traçabilité.
Une décision consignée au mauvais endroit est perdue au même titre qu'une décision non écrite.

**Chaque décision qui affirme un fait sur l'existant est confrontée aux sources avant d'être
écrite.** Une valeur, une composition, un comportement de spec : `grep` des sources de vérité
(`.claude/pipeline.config.md`, « Sources de vérité ») sur deux ou trois ancres **avant** d'écrire
le verrou, et l'ancre vérifiée notée dans la décision (« §1.2 muet », « §1.2 conforme »). Une
décision sans ancre porte `⚠️ non confrontée`. Le verrou est un point d'écriture comme un autre au
sens de `decisions-vs-doc` ; trois fois, une décision verrouillée ici a contredit une spec sans que
personne ne le voie avant le briefing d'une session ultérieure — un arrêt de chantier au lieu d'un
grep de trente secondes.

Puis, si la session partait d'une issue en `needs-interrogation`, dire à l'utilisateur que l'issue
peut passer à `ready-for-agent` (ou `ready-for-human`) — la transition elle-même appartient à
`triage`.
