---
name: contradiction
description: Réconcilie une décision prise en conversation avec les sources de vérité qu'elle contredit — amende le § du document concerné, archive le raisonnement, puis propage aux rangs inférieurs et aux issues ouvertes. À utiliser quand la règle decisions-vs-doc a levé un arrêt, ou « cette décision contredit la doc », « répercute cette décision dans la doc ».
---

# Contradiction

Mouvement **amont** de la pipeline, symétrique de `repercussions`.

| | `contradiction` | `repercussions` |
|---|---|---|
| Déclencheur | une **décision de conversation**, ou un § falsifié par un merge que `repercussions` lui remonte | un **merge** |
| Ce qui falsifie | la décision qui vient d'être prise | le diff mergé |
| Ce qui devient faux | un **§ de document**, puis les issues | des **corps d'issues** |

Les deux partagent la même discipline : **deux citations ou rien**, un diff avant/après, et aucune
écriture sans « go ». Ce skill ne la réimplémente pas côté issues — il **délègue à
`repercussions`** une fois le document amendé.

## Le livrable est un § amendé

- **Le document est la spec.** S'il est devenu faux, on le **réécrit**. On n'ajoute pas une note en
  bas qui contredit le corps : le lecteur suivant lirait les deux et ne saurait pas laquelle vaut.
- **Le raisonnement ne va pas dans le document normatif.** `01-cadrage.md` et
  `02-specification-ux.md` ne portent que l'**état courant** — c'est écrit dans leurs en-têtes. Le
  pourquoi, les options écartées et la date vont dans `documents/archive/`.
- **Pas d'amendement formulable = pas de contradiction.** On se tait.

**Règle d'or** : ce skill **propose**, il n'écrit jamais en silence. Aucune édition sans « go »
explicite.

## Process

### 1. Établir la contradiction et son rang

Reprendre les deux citations de l'arrêt (`.claude/rules/decisions-vs-doc.md`) et les **vérifier
dans le fichier** — pas de mémoire, on relit la ligne. Puis lire la table « Sources de vérité » de
`.claude/pipeline.config.md` pour situer le **rang** touché.

Si la contradiction porte sur plusieurs documents, **le rang le plus haut commande** : on amende
là, et les rangs inférieurs suivent en cascade. Amender la spec UX sans toucher le cadrage qu'elle
spécifie produit deux documents divergents — soit une contradiction de plus.

### 2. Mesurer la cascade

Chercher les §§ qui **dépendent** de celui qu'on amende, par **deux recherches distinctes** :

1. **Par ancre lexicale** — noms de symboles, routes, champs, valeurs : `grep` dans tous les
   fichiers de rang égal ou inférieur, plus les renvois explicites (« voir §x », « cadrage §x »).
   Fonctionne parce que ces chaînes sont stables.
2. **Par affirmation** — pour toute phrase de **prose** amendée : énoncer *ce qu'elle affirme* en
   une proposition vérifiable, puis chercher les §§ qui portent la **même affirmation sous
   d'autres mots**, en partant de la carte des documents (miroirs déclarés, renvois) plutôt que du
   texte. Un `grep` sur les mots du passage édité ne trouve que les copies, jamais les
   paraphrases — c'est structurel.

Établir la liste **avant** de proposer quoi que ce soit — une cascade découverte à mi-parcours
transforme un amendement validé en chantier non validé. **Une cascade mesurée à zéro sur un
amendement de prose doit nommer les documents parcourus**, pas seulement les termes cherchés : une
cascade nulle non justifiée est le mode d'échec le plus coûteux de ce skill, parce qu'il est
silencieux.

Cas particulier, **rang 3** : toute valeur d'identité a un § miroir dans la spec UX (§1.2, §1.5,
§1.6, §3.4.1, §4). Les deux bougent ensemble, ou aucun ne bouge.

Signaler aussi ce qui **retombe hors des documents** : une décision peut périmer une commande, un
domaine, une zone sensible ou une surface de `.claude/pipeline.config.md`, ou une règle
d'arbitrage de `CLAUDE.md`.

### 3. Présenter en diff, et demander

Sous `## ⚖️ Amendements proposés`, un bloc par § touché, dans l'ordre des rangs :

```
01-cadrage.md §9.3                                        [rang 1] [origine]
  Avant : « trois autorisations distinctes à obtenir dans l'onboarding »
  Après : « quatre autorisations, la quatrième non bloquante »

02-specification-ux.md §12.1                              [rang 2] [cascade]
  Avant : « le bandeau couvre trois états de permission »
  Après : « le bandeau couvre quatre états de permission »
```

Montrer les **lignes** avant/après, pas une prose qui décrit le changement : un diff se juge en
deux secondes. Terminer par la liste des issues candidates à la propagation (étape 5) — sans les
traiter encore.

**Rappeler l'alternative** : abandonner la décision reste une sortie valide, et souvent la bonne
quand la cascade est large. Une section close ne se rouvre pas parce que c'était plus rapide.

### 4. Appliquer — sur « go » explicite

Dans l'ordre, sans en sauter :

1. **Amender chaque §** exactement comme présenté. Ne jamais profiter de l'édition pour reformuler
   autre chose. Dans les §§ alignés, **écrire la même formulation partout** : deux énoncés
   identiques se retrouvent au grep suivant, deux paraphrases divergent à nouveau en silence.
2. **Rang 1 uniquement — journaliser** : une ligne dans le journal des changements du cadrage
   (§18), au format du tableau existant `| Ancienne décision | Nouvelle décision |`.
3. **Archiver le raisonnement** dans `documents/archive/` : la contradiction, les options, ce qui a
   été retenu, la date **absolue**, et la liste des §§ répercutés. Le format existe déjà — §17 de
   `journal-decisions-ux.md`, à imiter.
4. **Répercuter hors documents** ce que l'étape 2 a listé (`pipeline.config.md`, `CLAUDE.md`),
   **dans le même commit** que l'amendement — `.claude/rules/contraintes.md` l'exige.

### 5. Propager aux issues — invoquer `repercussions`

Ne pas réimplémenter. Invoquer `repercussions` en lui donnant l'**amendement comme delta réel**, à
la place d'un diff mergé : ses étapes 2 à 6 s'appliquent telles quelles — ancres, périmètre
thème + match, deux citations, classement dormante / en vol, édition sur « go ».

Deux ajustements, à annoncer en le lançant :

- **Son étape 7 ne s'applique pas** : aucun thème ne s'est vidé, il n'y a pas de campagne de QA à
  proposer.
- **La ligne de Journal de spec** référence l'amendement (« Réconciliée avec l'amendement du
  cadrage §9.3 du 26 août 2026 »), pas un numéro d'issue fermée.

### 6. Récapituler

Les §§ amendés, l'entrée d'archive créée, ce qui a été répercuté hors documents, ce que
`repercussions` a fait des issues, et **ce qui reste ouvert**. Une cascade laissée à moitié est
pire que la contradiction de départ : elle est invisible.

## Ce que ce skill ne fait pas

- **Il ne détecte pas.** La détection est le rôle de `.claude/rules/decisions-vs-doc.md`, toujours
  active. Ce skill part d'une contradiction déjà établie.
- **Il ne tranche pas.** Il présente l'amendement et la cascade ; le mainteneur décide si la
  décision vaut son prix. Une cascade large est un argument **contre** la décision, pas pour.
- **Il n'édite aucune issue lui-même.** C'est `repercussions`, étape 5.
- **Il ne touche pas au code.** Une décision qui périme du code déjà écrit produit une issue, pas
  une édition sauvage.

## Les 3 idées à retenir

1. **Le rang le plus haut commande.** On amende à la source, jamais au milieu de la chaîne.
2. **L'état courant dans le document, le pourquoi dans l'archive.** Les en-têtes des docs
   l'imposent ; c'est ce qui les garde lisibles.
3. **La cascade se mesure avant le « go ».** C'est elle, pas l'amendement, qui dit si la décision
   est raisonnable.
