# Grille d'impact

Les cinq types de répercussion qu'une issue fermée peut avoir sur la **planification** d'une issue
ouverte. Pour chacun : le **signal** qui le révèle et la **correction type** à apporter à la spec
de l'issue — son corps, et son brief d'agent quand la ligne fausse y figure aussi. Une même issue
peut en cumuler plusieurs.

Chaque type ci-dessous se conclut par une **édition de la spec**. C'est la définition d'une
répercussion : si aucune édition n'est formulable, il n'y a rien à signaler.

| Type | Signal (dans le delta réel) | Correction type dans la spec |
|---|---|---|
| **Hypothèse caduque** | L'issue décrit un état du code (module, flux, donnée) que la PR a changé. | Réécrire le passage pour décrire l'état actuel. Si l'hypothèse était structurante → retour en `needs-interrogation`. |
| **Contrat déplacé** | Une signature, un format de payload, un nom public ou une route que l'issue référence a bougé. | Remplacer les références par le nouveau contrat, avec le renvoi vers l'issue fermée. |
| **Périmètre déjà couvert** | La PR a fait tout ou partie de ce que l'issue prévoyait. | *Partie* → retirer du corps ce qui est déjà fait et resserrer les critères d'acceptation. *Tout*, sans ambiguïté → fermeture en doublon (« go » nommé requis). |
| **Ordre & dépendances** | L'issue dépendait de celle fermée, ou en débloque d'autres dans un ordre devenu faux. | Mettre à jour la ligne de dépendance du corps (bloqueur levé, nouvel ordre). |
| **Décision contradictoire** | L'issue demande l'inverse d'une décision actée pendant le développement. | Réécrire l'issue selon la décision actée, ou la poser au mainteneur si l'arbitrage n'est pas évident. Ne jamais trancher la conception seul. |

## Niveaux

- **Bloquant** — la spec est fausse sur un point structurant ; développer l'issue en l'état
  produirait du travail à jeter.
- **À ajuster** — la spec reste globalement valable, une référence ou un périmètre doit être repris.

Il n'existe pas de niveau « info ». Une observation qui ne débouche sur aucune édition ne se
formule pas.

## Garde-fous

- **Deux citations, sinon rien** : la ligne exacte du corps devenue fausse, et le fait exact du
  delta qui la falsifie. Une intuition (« ça pourrait interférer avec… ») n'est pas une
  répercussion.
- **Une fermeture en doublon exige un recouvrement total et non ambigu**, plus un « go » portant
  nommément sur cette issue. Dans le doute : périmètre réduit dans le corps, jamais fermeture.
- **Tout re-découpage non trivial ou conflit de conception se remonte au mainteneur.** Ce skill
  corrige une planification devenue fausse ; il ne refait pas la conception à sa place.
- **Ne pas élargir l'édition** au-delà du diff présenté et validé. Corriger une coquille au passage,
  c'est déjà écrire sans « go ».
