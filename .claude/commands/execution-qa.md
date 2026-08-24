---
description: Déroule un plan de QA phase par phase en cochant les cases dans l'issue
argument-hint: [#issue du plan de QA]
---

Invoque le skill `execution-qa`.

Plan à dérouler : $ARGUMENTS

Chaque case cochée doit reposer sur une **preuve observée**. À chaque échec, propose les trois
options (déposer, reporter, corriger en session) et n'invoque jamais `bug-vers-issue` sans accord
explicite de l'utilisateur.
