---
description: Déroule le cycle complet d'une PR — briefing, TDD, commits, auto-review, PR, merge, répercussions
argument-hint: [#issue ready-for-agent | description du travail]
---

Invoque le skill `cycle-pr`.

Travail à réaliser : $ARGUMENTS

Commence par l'Étape 1 (briefing pré-PR) et son auto-challenge — **aucune ligne de code avant que
le briefing soit validé**. Puis l'Étape 2 : **ouvre la PR en draft avec `Closes #N` avant d'écrire
quoi que ce soit** — c'est ce qui rend le travail visible comme en cours pour le reste de la
pipeline. Lis les commandes du projet (test, lint, typecheck…) dans `.claude/pipeline.config.md` ;
ne les devine pas.

Vérifie d'abord que le travail est passé par l'**interrogatoire**. Sans trace d'interrogation
(issue jamais passée en `needs-interrogation`, brief marqué `⚠️ Non interrogée au triage`, ou
demande directe sans issue), lance `interroge-moi` avant toute chose.
