# Décision — un déploiement dure le temps de fermer les flux ouverts, pas « quelques secondes »

*Archive non normative. L'état courant est au cadrage §13.9 (note sur le déploiement à chaud) ;
ce fichier conserve le raisonnement, pour qu'il ne soit pas rouvert sans élément nouveau.*

**Date :** 7 septembre 2026. **Déclencheur :** le lot 2/2 de l'issue #45 (PR #112), qui livre le
compose de production et le Caddyfile. La relecture indépendante a mesuré l'arrêt de `caddy` avec
un flux `text/event-stream` tenu ouvert à travers lui, et la passe `repercussions` de la clôture a
confronté la mesure au §13.9.

## La contradiction

**§ concernés :** cadrage §13.9, « Note sur le déploiement à chaud », et son journal §18.

- **Citation source** — cadrage §13.9 : « Un `docker compose up -d` interrompt le service
  quelques secondes. »
- **Citation décision** — `infra/compose.prod.yml` et `infra/Caddyfile` (PR #112) : `stop_grace_period:
  30s` sur chaque service, `grace_period 25s` pour Caddy, borne uvicorn 25 s — ce que le §13.7
  exige (« l'arrêt gracieux doit couvrir les connexions SSE longues »). Mesuré le 7 septembre 2026
  sur Docker 29.2.1, un flux SSE ouvert à travers `caddy` : `docker stop -t 30` → **24 372 ms,
  code 0** avec `grace_period` ; **29 069 ms, code 137** (SIGKILL) sans. Pendant la période de
  grâce, Caddy n'accepte plus de connexion nouvelle.

Le §13.7 et le §13.9 étaient en tension à l'intérieur du même document : l'un impose de laisser les
flux se fermer, l'autre affirmait que l'interruption tient en quelques secondes.

## Ce qui a été retenu

Le § garde sa phrase et sa conclusion, et dit la durée réelle quand des flux sont ouverts —
« jusqu'à une trentaine de secondes » — en renvoyant au §13.7 qui la justifie. La conclusion
« invisible pour le joueur » reste vraie : la SSE se reconnecte nativement (§13.3), le service
d'arrière-plan réessaie avec espacement progressif (§10), et la spec UX §13 n'affiche un
avertissement que sur des coupures bien plus longues.

**Options écartées :**

- *Le document gagne — retirer `grace_period` et le délai de `caddy`.* Contredirait le §13.7, de
  rang égal et postérieur en révision (4 septembre 2026) ; et ramènerait le SIGKILL mesuré.
- *Un chiffre exact (« 25 secondes »).* Il dépend de deux valeurs de configuration
  (`grace_period`, borne uvicorn) que `api/tests/test_compose_prod.py` et `test_compose.py`
  comparent au délai Docker : les épingler dans un document de rang 1 recréerait le piège du
  4 septembre (`decision-delai-arret-docker.md`). « Une trentaine » nomme l'ordre de grandeur,
  borné par le `stop_grace_period`.
- *Ne rien écrire.* La règle `decisions-vs-doc` l'exclut dès que deux citations tiennent.

## Ce qui a été répercuté

| Emplacement | Rang | Nature |
|---|---|---|
| `01-cadrage.md` §13.9 | 1 | origine — la note réécrite |
| `01-cadrage.md` §18 | 1 | ligne au journal des changements |

**Cascade mesurée à ces deux emplacements, et pas davantage.** Balayage par ancre lexicale
(`quelques secondes`, `déploiement à chaud`, `interrompt le service`, `up -d`) et par
affirmation (« un déploiement est bref et invisible pour le joueur »), sur les quatre documents de
`documents/reference/`, `documents/archive/`, `documents/setup/`, `README.md`, `CONTRIBUTING.md`,
`.claude/pipeline.config.md`, `CLAUDE.md`, les README d'`api/` et d'`infra/`, et les neuf issues
ouvertes — corps et commentaires. La spec UX §13 ne fixe que des seuils d'affichage (coupure
< 5 min, ≥ 5 min), non falsifiés ; l'issue #47 vérifie « un déploiement ne coupe pas un client »
et n'avance aucune durée : rien à y changer.
