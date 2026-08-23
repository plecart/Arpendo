# Corrections à demander à Claude Design

> ## Vérification de la version 2 — 13 août 2026
>
> **Neuf points sur treize corrigés.** Ce qui suit reste dû ; le prompt plus bas est à rejouer en
> ne gardant que les points non traités.
>
> | | Point | v2 |
> |---|---|---|
> | 1 | Les **deux versions** de la modale Paramètres, avec Permissions dans les deux, Quitter en partie, Déconnexion + Suppression au Menu | ✅ **exactement la logique demandée** |
> | 2 | Modale d'entrée en partie non annulable | ✅ « Joue prudemment » présente |
> | 3 | Bande de distance dans le journal | ✅ |
> | 5 | Liens juridiques retirés de l'Accueil, gardés sur Connexion et Paramètres | ✅ |
> | 6 | Code de partie à 6 caractères partout | ✅ `K7MQ4P` seul |
> | 7 | « Partager » sans « le lien » | ✅ |
> | 9 | Entrée réseau retirée du journal | ✅ |
> | — | Palette joueur, absence de texte sur la carte, échelle typo, couleur d'eau | ✅ inchangés |
>
> **Une régression, sur une contrainte dure.** Le sélecteur de durée est devenu **un curseur** :
> huit crans, mais une **poignée de 22 dp** — moins de la moitié du plancher de 48 dp du §1.4,
> qui n'admet aucune exception. La spec §5.1 avait examiné puis rejeté cette forme, et le motif
> n'a pas changé : entre « 48 h » et « 1 semaine » il y a cinq jours, entre « 30 min » et « 1 h »
> trente minutes. Un rail continu ment sur ce qu'il représente. **À corriger — voir le point 4.**
>
> **Deux absences assumées par le porteur, sans suite à donner :** les libellés de section
> « Cette partie » / « Ce compte » (devenus inutiles, les deux blocs ne coexistant jamais), et le
> lien web de suppression (la page n'existe pas encore — mais le cadrage §12.2 la donne comme
> **obligatoire pour Google Play**, elle reste due avant publication).

> **À coller dans la conversation où la maquette a été produite**, sans rien rejoindre : elle a
> déjà le brief et les assets.
>
> **Ordre de lecture :** les points 1 à 5 sont des manques par rapport à des obligations écrites.
> Les points 6 à 9 sont des ajustements. Le point 10 dit ce qu'il faut **garder**, parce qu'une
> demande de correction qui ne dit pas ce qui va fait toujours régresser autre chose.
>
> **Le point 1 demande une planche de plus** — la modale Paramètres existe désormais en deux
> versions selon qu'une partie est en cours ou non. C'est la seule demande qui ajoute un écran.

---

---

## Ce que ce document est, et n'est plus

Le prompt de correction qui figurait ici a été **supprimé le 13 août 2026** : il a été consommé, la
version 2 y a répondu, et il ne resservira pas. Ce document ne conserve que **la trace de ce qui a
été demandé et de ce qui a été obtenu** — utile le jour où l'on se demandera pourquoi la maquette
diffère de la spécification sur tel point.

**Les deux derniers écarts ont été tranchés en faveur de la maquette**, et les documents de
référence ont suivi :

- **Le curseur de durée** est conservé — *« une liste de pastilles fait trop AI slop pour un MVP »* —
  et rendu conforme au plancher de 48 dp : zone tactile étendue autour de la poignée, ligne de
  48 dp, aimantation stricte sur les huit valeurs, tap sur le rail, crans dessinés et valeur
  affichée en clair (`02-specification-ux.md` §5.1).
- **La modale de visibilité des zones** est supprimée de l'interface. L'obligation qu'elle portait
  est passée aux CGU et à la politique de confidentialité, où elle est désormais une clause écrite
  (`01-cadrage.md` §13.12 et §16, `02-specification-ux.md` §6.1).

**En cas de divergence entre cette maquette et la spécification, la spécification l'emporte.**
