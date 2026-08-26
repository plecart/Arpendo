---
description: Réconcilie une décision de conversation avec la doc et les issues qu'elle contredit
argument-hint: [la décision, ou le § contredit]
---

Invoque le skill `contradiction`.

Décision à réconcilier : $ARGUMENTS

Sans argument, prends la contradiction levée par le dernier arrêt de
`.claude/rules/decisions-vs-doc.md` dans cette conversation.

Vérifie les deux citations **dans le fichier** avant toute chose — pas de mémoire. Situe le **rang**
via la table « Sources de vérité » de `.claude/pipeline.config.md`, et amende **au rang le plus
haut** touché. Mesure la cascade complète avant de proposer, présente chaque amendement en diff
avant/après, et n'écris rien sans « go » explicite.

Rappelle que l'abandon de la décision reste une sortie valide : une cascade large est un argument
contre la décision.

Pour les issues, **invoque `repercussions`** avec l'amendement comme delta réel — ne réimplémente
pas sa grille.
