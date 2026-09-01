---
name: audit-spec-ui
description: Audit mécanique d'une spécification d'interface (document normatif UX/UI) — établir le périmètre et l'autorité des livrables, épuiser les passes vérifiables (jetons déclarés vs utilisés, tables de priorité, arithmétique de mise en page, contraste en composition réelle, cohérence prose/tables) avant tout jugement de goût, puis appliquer les corrections en trois passes (édition, propagation, résidus). À utiliser quand l'utilisateur demande de relire, auditer ou corriger une spec d'interface ou un document de design — « relis la description de l'interface », « dis-moi ce qui semble mauvais dans cette spec », « applique ces corrections à la spec ».
---

# Audit de spécification d'interface

Dans un document normatif, les défauts les plus coûteux sont **vérifiables mécaniquement** —
jetons, tables de vérité, arithmétique, unités, contradictions entre deux endroits qui décrivent
la même chose. Un audit épuise ces passes **avant** d'émettre un avis de conception : elles sont
opposables, elles ne se discutent pas, et elles trouvent ce qu'une lecture attentive rate.

## Étape 0 — Périmètre et autorité, avant toute lecture

Quand plusieurs artefacts décrivent le même objet (spec textuelle, maquette HTML, fichier de
trace), un audit sans hiérarchie d'autorité explicite produit des findings dont le lecteur ne
peut pas évaluer la portée.

1. **Inventorier** tous les livrables qui décrivent l'objet audité.
2. **Chercher la déclaration d'autorité** — souvent dans un fichier de trace, un en-tête
   « Source normative », ou le README. Si aucune n'existe, c'est la **première** question à poser,
   pas la dernière.
3. **Annoncer le périmètre en une ligne avant de livrer** : « audité : X ; écarté : Y, parce
   que Z ».

## Les passes mécaniques — dans l'ordre, avant tout avis de conception

1. **Jetons déclarés vs utilisés**, dans les deux sens : un jeton utilisé mais jamais déclaré, un
   jeton déclaré que rien n'utilise.
2. **Valeurs partagées entre familles disjointes** : la valeur d'un jeton réutilisée depuis une
   autre famille censée être indépendante.
3. **Tables de priorité** : aucune condition ne doit être un sous-ensemble d'une condition plus
   prioritaire — sinon la ligne est logiquement inatteignable.
4. **Arithmétique** : refaire chaque budget d'espace annoncé, pour **tous** les composants
   concernés — pas seulement ceux que le document calcule lui-même.
5. **Contraste en composition réelle** : quand un composant est spécifié translucide, composer le
   fond réel avant de mesurer — un contraste calculé sur fond opaque ne prouve rien.
6. **Cohérence prose ↔ tables d'états ↔ récapitulatifs** : confronter systématiquement les trois,
   y compris à l'intérieur d'un même paragraphe.

Chaque finding **cite le §** (jamais un numéro de ligne, qui périme à la première édition) et
porte un **scénario d'échec concret** : ce qu'un implémenteur construirait de faux en suivant le
texte tel quel.

## Diagnostic de mise en page

Un vide de mise en page a deux causes possibles : une mauvaise répartition, ou **un conteneur
trop grand**. Tant qu'on suppose la première, chaque correction déplace le vide sans le résoudre
(ancré aux bords → trou central ; à gauche → marge de fin ; centré → deux demi-trous).

- Question préalable : **« ce conteneur a-t-il assez de contenu pour justifier sa taille ? »** Si
  le contenu occupe moins de ~80 % de la largeur disponible et que rien ne peut légitimement s'y
  ajouter, proposer d'emblée de retirer le conteneur ou de le faire épouser son contenu.
- Avant d'accepter une disposition centrée : **la largeur des blocs est-elle stable ?** Un bloc
  centré dont le contenu change de largeur dérive à chaque mise à jour ; centré *entre deux
  ancres*, il dérive une seconde fois quand les ancres bougent.

## Appliquer les corrections — trois passes, jamais une seule

Presque chaque correction a des occurrences ailleurs que là où le finding l'a trouvée. « Une
édition par finding » produit une correction locale et un document incohérent autrement.

1. **Édition** — appliquer chaque correction là où le finding l'a trouvée.
2. **Propagation** — pour chaque valeur, jeton, seuil ou règle touché, chercher la valeur
   **d'origine** dans tout le corpus et traiter chaque occurrence. La recherche porte sur
   l'ancienne valeur, pas la nouvelle : c'est la seule qui révèle ce qu'on a oublié.
3. **Résidus** — re-chercher les valeurs supprimées et vérifier qu'il n'en reste aucune, ou que
   celles qui restent sont délibérément citées. L'exécuter comme une liste d'assertions, pas
   comme une relecture.

Le rapport de correction énonce le **dénombrement** : « N occurrences repassées, k corrigées,
N−k vérifiées indemnes » — jamais « les findings sont corrigés ».

## Avant de livrer — vérification obligatoire

Relire cette liste et confronter le livrable à chaque point :

- [ ] Périmètre et autorité annoncés en tête (étape 0.3).
- [ ] Les six passes mécaniques exécutées — ou marquées « sans objet » avec la raison, une ligne
      chacune.
- [ ] Chaque finding : § cité + scénario d'échec.
- [ ] Les jugements de conception (goût, lisibilité, choix) présentés **après** les findings
      mécaniques, et clairement séparés d'eux.
- [ ] Si des corrections ont été appliquées : les trois passes déroulées, dénombrement donné.
