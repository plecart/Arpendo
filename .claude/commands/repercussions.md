---
description: Après un merge, corrige la planification des issues ouvertes que la clôture a rendues fausses
argument-hint: [#issue fermée]
---

Invoque le skill `repercussions`.

Issue fermée : $ARGUMENTS

Sans argument, prends la dernière issue fermée par un merge sur la branche trunk.

Le livrable est une **édition du corps** des issues impactées — **jamais un commentaire d'issue**.
Ne retiens une répercussion que si tu peux citer la ligne du corps devenue fausse **et** le fait du
delta qui la falsifie. Présente chaque correction sous forme de diff avant/après, et n'écris rien
sans « go » explicite.

Classe d'abord chaque issue impactée **dormante** ou **en vol** (PR ouverte qui la ferme, ou ligne
active dans `PR-PARALLELES.md`). Une issue en vol ne se fait **ni éditer ni re-labelliser** : son
signalement va en commentaire sur **sa PR ouverte**, et remonte en tête du récapitulatif s'il est
bloquant.
