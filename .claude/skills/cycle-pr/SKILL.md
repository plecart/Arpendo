---
name: cycle-pr
description: Exécute le cycle complet de développement d'une PR — briefing pré-PR, ouverture de la PR en draft avant tout code, implémentation en TDD red-green-refactor, cycle de commit modif→test→cleanup→test→commit, auto-review, passage en ready for review, boucle de review et merge. Utiliser pour implémenter une issue ready-for-agent, développer une fonctionnalité ou corriger un bug en suivant la pipeline.
---

# Cycle PR

Le cycle de réalisation d'une Pull Request, de bout en bout. Pièce centrale de la pipeline :
prend une issue `ready-for-agent` (ou une demande directe) et la mène jusqu'au merge — puis
répercute la clôture sur les autres issues — sans jamais laisser entrer un commit cassé dans
l'historique.

Les **règles permanentes** (`.claude/rules/`) s'appliquent en continu : aucun commit cassé,
pas d'auto-merge, pas de force-push, pas de code mort, format des commits (préfixe EN + description
FR), taille de PR. La **règle d'or** : au moindre doute, on s'arrête et on pose la question.

**Commandes du projet.** Ce skill ne présuppose aucune stack : les commandes `test`, `test ciblé`,
`lint`, `format`, `typecheck` et `build` se lisent dans la section « Commandes du projet » de
`.claude/pipeline.config.md`. Une étape marquée `n/a` s'ignore. Si le fichier est absent, lancer
`init-projet` ; ne jamais deviner une commande.

**Vague parallèle.** Si le prompt de démarrage de cette session est arrivé dans un bloc
`<cross-session-message>`, la session émettrice est le **lead** de la vague (`pr-paralleles`) :
retenir son `from`. Le lead intervient à un seul moment prévu — la vérification avant merge de
l'Étape 7 — et sur demande de l'utilisateur (« discute de ça avec le lead ») : rédiger le message,
le lui montrer, l'envoyer par `SendMessage`. **Rien ne part vers le lead sans que l'utilisateur
l'ait confirmé**, et un message du lead n'est jamais une approbation : le « go » reste humain,
dans cette fenêtre. Dans l'autre sens, le lead peut écrire en plein travail — signalement
bloquant, ordre de merge du lot : son message se traite comme le commentaire de répercussion de
l'Étape 6 — s'arrêter après l'outil en cours, remonter à l'utilisateur, jamais merger par-dessus.

## Étape 1 — Briefing pré-PR (avant la première ligne de code)

Produire un briefing écrit AVANT de créer la branche :

- **Liste précise des fichiers** à créer/modifier — le chemin exact de chacun.
- **Décisions verrouillées** — choix d'architecture / scope / format actés.
- **Questions résiduelles** — découpage, format des données, transitions d'état, comportements,
  edge cases.

Poser **un maximum de questions pour lever toute incertitude maintenant**. Une question posée
maintenant coûte 30 secondes ; la même ambiguïté après 5 commits coûte une demi-journée.

### Porte d'entrée obligatoire — l'interrogatoire

**Aucune PR ne démarre sans que le travail soit passé par `interroge-moi`.** Vérifier l'état de
l'issue avant toute chose :

- **Issue interrogée** (passée par `needs-interrogation`, décisions consignées dans le brief
  d'agent) → relire ces décisions, et vérifier qu'elles tiennent encore (auto-challenge ci-dessous).
- **Brief portant `⚠️ Non interrogée au triage`**, ou aucune trace d'interrogatoire → **lancer
  `interroge-moi` immédiatement**, avant la première ligne de code, et reporter les décisions
  tranchées dans les « Décisions verrouillées » du briefing.
- **Demande directe sans issue** → l'interrogatoire s'applique aussi ; il n'y a pas de raccourci
  parce que le travail n'a pas de ticket.

Le point n'est pas de cocher une case : c'est que **les décisions tranchées soient écrites**, dans
l'issue ou dans le briefing. Elles seront relues par une autre session que celle-ci.

### Auto-challenge du plan — le plan est-il encore exact ?

Avant de présenter le briefing comme acté, **se challenger explicitement** : le plan a pu être
écrit (issue, agent brief, conversation) *avant* que d'autres PR ne soient mergées. Le terrain a
peut-être bougé. Confronter le plan à la réalité **actuelle** du code :

- **Relire l'état réel** de la zone touchée (`git log` récent sur `main`, fichiers concernés) — pas
  l'état supposé au moment où l'issue a été écrite.
- **Pour chaque décision verrouillée et chaque fichier listé**, vérifier qu'elle tient toujours :
  l'interface existe-t-elle encore sous cette forme ? une PR récente a-t-elle déjà fait une partie
  du travail, déplacé un module, changé un contrat, rendu une hypothèse caduque ?
- **Vérifier que la suite du dev tient** : ce que cette PR prépare pour les issues suivantes est-il
  toujours cohérent, ou l'ordre / le découpage doit-il être revu ?
- **Énoncer à voix haute** sous un titre `## 🔍 Auto-challenge du plan` : ce qui reste valable, ce
  qui a changé, et les ajustements proposés (fichiers en plus/en moins, décision à rouvrir, scope à
  resserrer ou re-découper).

S'il y a un écart qui change le cours du dev, **s'arrêter et le remonter à l'utilisateur** avant le
« go » — ne pas dérouler un plan périmé en silence. Si tout tient, le dire explicitement (« plan
confirmé contre l'état actuel »).

Attendre un **« go » explicite**, puis créer la branche (trunk-based depuis `main`) :

```
git checkout -b <type>/<description>   # feat/  fix/  chore/  docs/  refactor/
```

## Étape 2 — Ouvrir la PR en draft (toujours avant la première ligne de code)

**La PR est le premier artefact produit, pas le dernier.** C'est elle qui rend le travail
*visible comme en cours* pour le reste de la pipeline : `repercussions` s'en sert pour savoir
qu'une issue est « en vol » et ne pas réécrire sa spec sous les pieds de cette session, et
`pr-paralleles` pour tenir son tableau de bord. **Une branche locale sans PR est invisible** — le
travail existe, mais rien ne le sait.

GitHub refuse une PR sans commit : amorcer avec un commit vide, pousser, ouvrir en draft. Le
message d'amorce suit `taille-pr.md` comme tout autre commit — **pas de numéro d'issue dans le
titre**, le lien vit dans le `Closes #N` de la PR.

```
git commit --allow-empty -m "chore: amorce <description courte>"
git push -u origin <type>/<description>
gh pr create --draft --assignee @me \
  --title "<type>(<scope>): <description FR>" \
  --body "$(cat <<'EOF'
Closes #<N>

## Briefing (provisoire — remplacé à l'Étape 5)
<le briefing validé à l'Étape 1>
EOF
)"
```

La PR draft porte **dès sa création** :

- **`Closes #<N>`** dans le body. C'est **la** ligne qui rend l'issue détectable comme en vol.
  Sans elle, `repercussions` la croira dormante et éditera sa spec en cours de développement.
- Le **briefing de l'Étape 1** comme corps provisoire — le plan devient lisible par le mainteneur
  et par les autres sessions, avant que le code n'existe.
- **Assignee**, **labels** et **milestone** (mapping de `.claude/pipeline.config.md`).
- Le marqueur **draft**, qui dit « en cours, ne pas reviewer » et interdit le merge accidentel.

Pour une **demande directe sans issue**, ouvrir quand même la draft : sans `Closes`, mais le
travail reste visible du reste de la pipeline.

> **La CI ne tourne pas sur une draft** (garde `if:` dans le `ci.yml` du template). C'est voulu :
> les étapes 3.2 et 3.4 imposent une suite verte en local avant chaque commit, donc le filet est
> déjà tendu — inutile de dépenser des runs sur du code incomplet. La CI démarre au `gh pr ready`
> de l'Étape 5. **Ne pas interpréter l'absence de run comme une CI cassée.**

En vague parallèle (`pr-paralleles`), le lead relève lui-même le numéro de PR (`gh pr list`) pour
son tableau de bord : rien à lui envoyer.

## Étape 3 — Le cycle de commit (jamais sauté, jamais raccourci)

Chaque commit suit **exactement** :

```
1. modif (TDD)  →  2. test (vert)  →  3. cleanup pass  →  4. test (vert)  →  5. commit
```

### 3.1 Modification — en TDD (tracer bullet vertical)

**Frontières tierces : on vérifie, on ne suppose pas.** Avant d'appuyer un comportement sur une
bibliothèque ou un framework tiers à une frontière (réseau, encodage, secrets, fusion avec un
thème ou une config par défaut, cycle de vie de ressources), lire ce que fait réellement l'API —
documentation via `context7` ou sources du paquet — et le noter dans les `Notes` de la PR avec sa
référence. Les défauts les plus coûteux d'une PR « verte » sont des suppositions sur un paquet :
un décodage par défaut, un retry silencieux, une fusion de valeurs, un `repr` qui affiche un secret.

Implémenter **un comportement à la fois** en red-green-refactor. **Ne jamais** écrire tous les
tests d'abord puis toute l'implémentation (slicing horizontal = mauvais tests) :

```
ROUGE : écrire UN test du prochain comportement → il échoue
VERT  : écrire le minimum de code pour le faire passer → il passe
```

Règles : un test à la fois ; juste assez de code pour passer le test courant ; ne pas anticiper
les tests futurs ; tester le comportement observable via l'interface publique.

- Bons vs mauvais tests : [references/tests.md](references/tests.md)
- Quand mocker (frontières du système uniquement) : [references/mocking.md](references/mocking.md)
- Concevoir des interfaces testables : [references/design-interface.md](references/design-interface.md)
- Viser des modules profonds : [references/modules-profonds.md](references/modules-profonds.md)

**Documentation maximale** : chaque fonction écrite est documentée à fond (intention, params,
valeur de retour, erreurs, effets de bord, pré/postconditions, exemples, edge cases) au format
idiomatique du langage. La doc explique le contrat, les tests prouvent le comportement.

**Doc projet en sync** : si le delta change un comportement, une commande, une interface ou
l'architecture, mettre à jour la doc concernée (`README`, `docs/`, `CLAUDE.md`, glossaire) **dans
le même commit** — voir `.claude/rules/contraintes.md`. La doc ne se met jamais à jour « plus tard ».

### 3.2 Premier passage de tests

Lancer la suite rapide. **Si rouge → pas de commit.** On répare.

### 3.3 Le « cleanup pass » — relecture distincte du delta

Une fois le delta fonctionnel et vert, faire une **relecture distincte** (pas du nettoyage au fil
de l'eau).

**Le prompt à exécuter et la façon de l'appliquer vivent dans `.claude/rules/cleanup-verbatim.md`**
— règle permanente, donc déjà chargée. Le prompt s'exécute **mot pour mot** depuis ce fichier ; ne
jamais le recopier ici, une copie finit toujours par diverger de l'original.

Spécifique à cette étape :

- Pistes de refactor : [references/refactoring.md](references/refactoring.md).
- Vérifier aussi les 3 axes de conception de `.claude/rules/contraintes.md` (modulaire /
  fractionné / scalable), en plus de KISS, DRY et YAGNI.
- **PR « foundation »** : YAGNI peut être suspendu ponctuellement (scaffold pour la suite), mais
  le **noter explicitement**. KISS, DRY et la structure restent actifs.

### 3.4 Second passage de tests

Le cleanup a pu casser quelque chose. Relancer les tests → **vert obligatoire**.

### 3.5 Commit

Uniquement si tout passe. Message = **titre conventional commit seul** (préfixe EN, description FR) :

```
git commit -m "type(scope): description"
```

Pas de corps, pas de footer, pas de `Co-Authored-By`, pas de numéro de PR. Breaking change : `!`
dans le titre. Puis enchaîner sur le commit suivant (retour 3.1).

### Point d'arrêt humain

Si le commit touche une **zone sensible** déclarée dans `.claude/pipeline.config.md` (section
« Périmètre »), rendre la main pour validation manuelle **avant** de committer.

## Étape 4 — Relecture indépendante de fin de PR (avant `git push`)

Quand tous les commits sont faits, deux passes, dans cet ordre.

**4.1 Auto-review** — revue critique du **diff complet de la branche** (`main..HEAD`), en vision
d'ensemble : problèmes d'architecture (couplage, frontières), naming incohérent entre commits,
edge cases / erreurs / race conditions, KISS/DRY/YAGNI à l'échelle de la PR — notamment la
**duplication inter-commits**.

**4.2 Relecture par un contexte vierge — obligatoire.** L'auto-review est faite par la session qui
a écrit le code, avec les hypothèses qui l'ont produit ; elle ne les met pas à l'épreuve.
**L'exigence** : le diff est relu par un lecteur qui n'a pas ces hypothèses. **Le moyen par
défaut** : un **agent de relecture** (sous-agent, lecture seule, sans accès à cette conversation).
L'invocation de `cycle-pr` — `/cycle-pr` tapé par l'utilisateur, ou prompt de démarrage d'une
vague `pr-paralleles` — **vaut demande** pour cet agent : une consigne de session « pas de
sous-agent sans demande de l'utilisateur » est déjà satisfaite, ne pas re-demander. **Repli** si
le harness ne permet réellement pas de lancer un sous-agent : rendre la main au relecteur humain
avec le diff et le prompt de relecture verbatim, et le noter dans la section « Relecture
indépendante » du body de PR — jamais de saut silencieux. L'agent reçoit **uniquement** :

- le corps de l'issue et son brief d'agent (ou le briefing de l'Étape 1) ;
- le diff `main..HEAD` et le droit de lire les fichiers touchés ;
- `.claude/rules/contraintes.md`, `.claude/rules/cleanup-verbatim.md` et le prompt de relecture
  **verbatim** ;
- la consigne **frontières tierces** : pour chaque appel à une bibliothèque ou un framework tiers à
  une frontière — réseau, sérialisation/encodage, secrets, fusion avec un thème ou une config par
  défaut, cycle de vie de ressources — **vérifier le comportement réel** dans la documentation
  (`context7`) ou dans les sources du paquet, jamais de mémoire, et signaler tout écart avec ce que
  le code suppose.

Il rend : chaque critère d'acceptation ✅ / ❌ / ⚠️ avec preuve, puis ses constats classés
bloquant / important / mineur, chacun avec fichier et raison. **Ne pas discuter un constat depuis
la mémoire de la session : le vérifier dans le code.**

Chaque constat retenu → **un commit de fix dédié** (cycle complet 3.1→3.5). Relancer la relecture
tant qu'il reste un bloquant ou un important. Les constats écartés sont notés avec leur raison —
ils iront dans les `Notes` de la PR (Étape 5).

Une fois la relecture propre → `git push`.

## Étape 5 — Finalisation de la PR (passage en ready for review)

La PR **existe déjà** depuis l'Étape 2. Il s'agit ici de remplacer le briefing provisoire par le
body définitif, puis de sortir du draft.

- **Titre** conventional commit (préfixe EN + description FR) — le réajuster si le scope a bougé
  en cours de route.
- **Assignee**, **labels**, **milestone** : vérifier qu'ils sont toujours justes.
- **Conserver la ligne `Closes #<N>`** — la perdre en réécrivant le body casserait à la fois la
  fermeture automatique de l'issue et la détection « en vol ».
- Remplacer le corps par un **body structuré** :

```markdown
## Summary
<1-3 phrases : l'intention de la PR>

## Changes
<commits regroupés par thème : infra / feature / tests / docs>

## Test plan
- [x] CI locale verte
- [x] CI verte
- [x] <vérifs manuelles si pertinent>

## Relecture indépendante
<verdict de l'agent de l'Étape 4.2 : constats corrigés (commit) / écartés (raison)>

## Notes
<décisions, follow-ups différés, hors-scope, comportements tiers vérifiés (doc citée)>
```

Au-delà de **~10 fichiers** ou **~500 lignes** de diff, découper la PR.

Puis seulement, sortir du draft :

```
gh pr ready <numéro>
```

Tant que la PR est en draft, elle n'est **pas** à reviewer : c'est ce marqueur qui distingue
« travail en cours » de « prêt à être relu ».

C'est aussi ce `gh pr ready` qui **déclenche le premier run de CI** (événement `ready_for_review`).
Attendre son résultat avant l'Étape 6 — une PR fraîchement sortie du draft n'a encore aucun run.

## Étape 6 — Review + CI

- **CI verte** : tous les gates déclarés dans `.claude/pipeline.config.md` (« gates bloquants en
  CI »), dont le seuil de couverture s'il y en a un.
- **Revue** : revue automatisée (bot) ou self-audit ligne par ligne (sécurité, correctness,
  lisibilité, KISS/DRY/YAGNI, cohérence avec la stack).
- Chaque commentaire **pertinent** → cycle complet (3.1→3.5) + push + re-trigger de la review.
  Chaque commentaire **non pertinent** → noter brièvement pourquoi, ne pas corriger.
- **Boucler jusqu'à review vide.**

> **Commentaire de répercussion.** Un merge survenu ailleurs pendant que cette PR était ouverte a
> pu rendre sa spec fausse ; `repercussions` le signale ici même (le corps de l'issue n'est
> volontairement pas modifié tant que la PR est ouverte). Un signalement **bloquant** se traite
> comme tel : intégrer la correction dans cette PR, ou remonter au mainteneur si cela déplace le
> périmètre — ne jamais merger par-dessus.

## Étape 7 — Avant le merge

Quand la review est vide et la CI verte, **avant de demander le go** : un **dernier cleanup pass
holistique** sur le diff complet de la branche (même prompt verbatim qu'en 3.3, mais à l'échelle
de la PR). C'est le filet final pour les findings inter-commits.

- Findings → présenter, corriger (cycle complet), re-tester, push.
- Sinon → verdict explicite « code propre, prêt à merger ».

**Relire l'issue une dernière fois.** Le corps a pu bouger depuis le briefing de l'Étape 1 — d'autres
PR ont été mergées entre-temps, et une passe `repercussions` a pu la corriger ou déposer un
signalement sur cette PR. Comparer le corps actuel au briefing : si la spec a changé sur un point
que la PR ne couvre pas, **s'arrêter et le remonter** plutôt que de merger un travail construit sur
une spec périmée.

### Vérif de fumée — regarder le logiciel tourner

Tout ce qui précède examine du **code** : tests, diffs, specs. Personne n'a encore vu la
fonctionnalité fonctionner. Pour tout ce qui est visible par un utilisateur, c'est un angle mort
qu'aucun test unitaire ne couvre.

**Condition de déclenchement** : la PR touche une surface visible du projet (une des surfaces
déclarées dans `.claude/pipeline.config.md` — interface, API publique, sortie de commande, format
de fichier produit). Une PR de refacto interne, de doc ou d'outillage **saute cette étape** — le
dire en une ligne et passer.

Si elle se déclenche, proposer **3 à 5 vérifications, pas plus**, dérivées des critères
d'acceptation de l'issue et exécutables sur l'application qui tourne (commande `run local` de la
config) :

- Chaque vérification nomme l'**action exacte** et le **résultat attendu**.
- Ne vérifier que ce qu'un **test automatisé ne peut pas voir** : rendu réel, état d'erreur affiché,
  console propre, comportement d'un job jusqu'à son état terminal, fichier réellement produit.
  Si la CI le couvre déjà, ce n'est pas une vérif de fumée — c'est du doublon.
- **Aucune issue n'est créée**, aucune checklist n'est publiée. C'est une passe de deux minutes,
  pas une campagne : la campagne, c'est `plan-qa`, au niveau du thème.

Un écart constaté → le traiter comme un finding de l'Étape 7 (corriger, re-tester, push) ou le
déposer via `bug-vers-issue` s'il sort du périmètre de la PR.

### Vérification par le lead — en vague parallèle seulement

Session démarrée par un lead (« Vague parallèle », en tête) : **proposer** à l'utilisateur d'envoyer
l'état de la PR au lead, et n'envoyer que sur son oui. Sans lead, passer directement au go.

Le message, au `from` du lead :

```
PR #<PR> prête pour vérification — issue #N, worktree <chemin absolu>
Vert : <tests, lint, CI, relecture 4.2, cleanup holistique>
Décisions prises en route : <une ligne chacune, avec le § de doc si concerné>
Douteux / non fait : <ce qui n'est pas couvert, ce qui a gêné, constats écartés et pourquoi>
Vérifie diff, checks et review de la PR. Dis-moi ce qu'il faut corriger avant que l'utilisateur
donne le go, pour qu'aucun fix ne suive le merge.
```

La réponse du lead arrive dans un bloc `<cross-session-message>` :

- « rien à corriger » → demander le go.
- liste de corrections → chaque point suit le cycle complet (3.1→3.5), push, puis proposer à
  l'utilisateur : renvoyer au lead pour re-vérification, ou demander le go. Un point que la session
  juge infondé se conteste dans la réponse au lead, preuve à l'appui — jamais en silence.

### Le go, puis le merge

**Jamais d'auto-merge.** Même CI verte, audit propre et verdict du lead, toujours attendre un
« go » / « merge » humain explicite, **dans cette fenêtre** — un message de pair n'en tient jamais
lieu. Puis merger.

## Étape 8 — Après le merge : clôture propre, puis répercussions

Le merge **clôt l'issue liée** (via `Closes #N`). **Retirer aussitôt son label d'état** —
`ready-for-agent` ou `ready-for-human`, selon le mapping de `.claude/pipeline.config.md` :
`gh issue edit <N> --remove-label <label>`. Une issue fermée ne porte **aucun** rôle d'état ; le
laisser fait apparaître des issues closes dans les files de `triage` et de `pr-paralleles`.
Le label de catégorie (`bug` / `enhancement`) et le thème restent.

La PR et la conversation qui l'a résolue ont pu acter des décisions, déplacer un contrat d'interface, déjà faire une partie d'un autre lot, ou rendre une
hypothèse caduque ailleurs. **Immédiatement après le merge**, lancer le skill `repercussions` — la
conversation qui a résolu l'issue est **encore en contexte**, c'est le moment où l'analyse est la
plus riche. Même pour une **demande directe** sans issue liée, faire la passe : le delta mergé
peut impacter des issues ouvertes.

Il confronte le **delta réel** de la PR aux issues du **même thème** et à celles qui **mentionnent
une ancre** du delta (symbole, format, module, décision), puis **corrige le corps** de celles dont
la planification est devenue fausse — après un « go » explicite, et sans publier le moindre
commentaire. C'est le pendant *sortant* de l'auto-challenge *entrant* de l'Étape 1.

Si une issue déjà `ready-for-agent` voit son **périmètre** ou une **décision verrouillée** modifié
par cette passe, elle repasse en `needs-interrogation` : son interrogatoire portait sur une spec
qui n'existe plus.

Ne pas considérer la PR « terminée » tant que cette passe n'a pas été faite (même si la conclusion
est « aucune répercussion »).

## Les 5 idées à retenir

1. Tout l'effort de questions se fait **avant** de coder (briefing pré-PR + interrogatoire).
2. **La PR draft s'ouvre avant la première ligne de code**, avec `Closes #N`. C'est ce qui rend le
   travail visible comme *en cours* : sans elle, une autre session réécrira la spec de cette issue
   en croyant que personne ne travaille dessus.
3. Le cycle `modif → test → cleanup → test → commit` est **sacré et jamais raccourci** — y compris
   le cleanup sur les commits triviaux.
4. **Deux filets de cleanup** : un par commit (regard local), un sur la PR entière avant merge
   (regard global, inter-commits).
5. La PR n'est **terminée qu'après la passe `repercussions`** : une clôture peut bouleverser les
   autres issues — on le vérifie pendant que la conversation est encore en contexte.
