---
description: Orchestre plusieurs PR en parallèle via des git worktrees (une session par issue)
argument-hint: [#issues | nombre de PR à lancer]
---

Invoque le skill `pr-paralleles`.

Lot souhaité : $ARGUMENTS

Ne retiens que des issues `ready-for-agent` sans bloqueur en attente et à faible recouvrement de
fichiers. Présente le lot proposé sous forme de tableau et **attends confirmation** avant de créer
le moindre worktree.
