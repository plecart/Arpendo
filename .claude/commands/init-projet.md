---
description: Met en place ou reconfigure la pipeline de dev (stack, commandes, domaines, labels, CI, skills)
argument-hint: [ce qu'il faut configurer — vide pour tout]
---

Invoque le skill `init-projet`.

Demande : $ARGUMENTS

Si `.claude/pipeline.config.md` existe déjà, passe en **mode reconfiguration** : lis-le, montre
l'état actuel, et ne rejoue que les étapes concernées par la demande. Sinon, déroule l'amorçage
complet. Ne devine jamais une commande ou une valeur : détecte, propose, fais confirmer.
