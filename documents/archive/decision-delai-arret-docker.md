# Décision — le délai d'arrêt de Docker ne se suppose pas, il se déclare

*Archive non normative. L'état courant est au cadrage §13.7 ; ce fichier conserve le
raisonnement, pour qu'il ne soit pas rouvert sans élément nouveau.*

**Date :** 4 septembre 2026. **Déclencheur :** le lot 3/3 de l'issue #42 (PR #97), qui porte
`stop_grace_period` dans le compose local. La relecture indépendante du diff a mesuré le défaut
réel de Docker sur la chaîne d'outils du poste, et l'a trouvé différent de celui qu'annonçait le
cadrage.

## La contradiction

**§ concernés :** cadrage §13.7 (troisième piège) et son journal §18 ; issue #42, corps et brief
d'agent.

- **Citation source** — cadrage §13.7 : « L'arrêt gracieux doit couvrir les connexions SSE longues
  (§13.9, règle 6). **Le délai d'arrêt Docker par défaut est de 10 secondes** : trop court pour
  fermer proprement des flux ouverts. À porter explicitement dans le fichier compose. »
- **Citation décision** — mesuré deux fois indépendamment le 4 septembre 2026, sur Docker 29.2.1 /
  Compose 5.0.2 : un conteneur créé sans `stop_grace_period` porte `Config.StopTimeout = 1`, et
  `docker stop` sans `-t` tue un processus qui ignore SIGTERM en **1,3 seconde**, `ExitCode = 137`.
  Le défaut effectif est de **1 seconde**, pas 10.

La documentation officielle de Compose annonce bien 10 secondes ; l'écart est réel et propre à
cette version de la chaîne d'outils.

## Ce qui a été retenu

Le § n'avance plus un chiffre unique comme s'il était stable. Il dit que le défaut est **court et
dépend de la version**, cite la mesure avec sa version et sa date, et rappelle que la documentation
en annonce 10 — les deux valeurs étant de toute façon trop courtes pour des flux ouverts.

**Options écartées :**

- *Remplacer « 10 secondes » par « 1 seconde ».* Ce serait retomber dans le piège d'origine : un
  chiffre dépendant d'une version, épinglé dans un document de rang 1 que rien ne remesure. La
  prochaine version de Docker le rendrait faux à son tour, en silence.
- *Ne rien écrire, au motif que la conclusion opérationnelle est inchangée.* La règle
  `decisions-vs-doc` l'exclut : une affirmation mesurée fausse qui reste dans une source normative
  finit par être citée. C'est d'ailleurs ce qui s'était produit — l'issue #42 et son brief la
  recopiaient tous deux.
- *Ouvrir une issue de suivi plutôt qu'amender.* Échappatoire prévue quand l'amendement est trop
  gros pour la session ; il ne l'était pas — la cascade tient en quatre emplacements.

## Ce qui a été répercuté

| Emplacement | Rang | Nature |
|---|---|---|
| `01-cadrage.md` §13.7 | 1 | origine — le § réécrit |
| `01-cadrage.md` §18 | 1 | ligne au journal des changements |
| issue #42, corps | 5 | « supérieur aux 10 s par défaut de Docker » → « explicite, le défaut de Docker étant trop court » |
| issue #42, brief d'agent | 5 | deux lignes, même correction |

**Cascade mesurée à quatre emplacements, et pas davantage.** Balayage par ancre lexicale
(`10 secondes`, `dix secondes`, `délai d'arrêt`, `stop_grace`, `StopTimeout`, `SIGKILL`,
`arrêt gracieux`, `graceful`) et par affirmation, sur : les quatre documents de
`documents/reference/`, `documents/archive/`, `documents/setup/`, `documents/maquettes/`,
`.claude/pipeline.config.md`, `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, et les quinze issues
ouvertes — corps **et** tous commentaires. Le §13.9 règle 6, que le § amendé référence, énonce la
règle sans avancer de chiffre : rien à y changer.

Le code de la PR #97, lui, n'écrit plus aucun chiffre pour le défaut de Docker : sa prose nomme
l'ordre à respecter (la borne d'uvicorn sous le `stop_grace_period`) et laisse les deux seules
valeurs vivre là où un test les compare.
