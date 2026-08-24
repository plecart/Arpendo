---
name: repercussions
description: À la clôture d'une issue (PR mergée), corrige la planification des autres issues ouvertes que cette clôture a rendues fausses — hypothèses caduques, contrats déplacés, périmètres déjà couverts, ordres de dépendance. Le livrable est une édition du corps des issues impactées, jamais un commentaire. À utiliser juste après un merge qui ferme une issue, ou « vérifie l'impact de cette issue sur les autres ».
---

# Répercussions

Mouvement **sortant** de la pipeline, complémentaire de l'auto-challenge **entrant** de `cycle-pr`
(Étape 1, « le terrain a-t-il bougé depuis que l'issue a été écrite ? »).

Ici c'est l'inverse : une issue vient de se **fermer**. Les décisions actées pendant son
développement ont pu rendre **fausse la planification d'autres issues ouvertes**. Le rôle de ce
skill est de les **corriger**, pour que leur description et leur découpage redeviennent exacts.

## Le livrable est une édition, pas un commentaire

C'est la règle qui structure tout le reste.

- **Le corps de l'issue est la spec.** S'il est devenu faux, on le **réécrit**. Un commentaire ne
  remplace pas le texte faux — il s'assoit à côté, et l'issue continue d'affirmer une chose fausse
  pendant qu'un commentaire plus bas la contredit.
- **Ce skill ne commente jamais une issue.** La trace du *pourquoi* tient en une ligne dans le
  « Journal de spec » du corps ; l'historique d'édition GitHub garde le détail ; le récapitulatif
  complet reste dans la conversation, pour le mainteneur.
- **Pas d'édition formulable = pas de répercussion.** S'il n'y a rien à corriger dans le corps
  d'une issue, il n'y a rien à signaler à son sujet. On se tait. Il n'existe **pas** de catégorie
  « pour information ».
- **Unique exception : l'issue est déjà en cours de développement.** On ne réécrit pas une spec
  sous les pieds d'une session qui l'a déjà lue — on la prévient par un commentaire sur **sa PR
  ouverte** (étape 5). C'est la seule sortie commentée du skill.

**Règle d'or** : ce skill **propose**, il n'écrit jamais en silence. Aucune édition sans **« go »
explicite** du mainteneur.

## Document de référence

- [references/grille-impact.md](references/grille-impact.md) — les cinq types de répercussion, le
  signal qui les révèle et la correction type.

## Process

### 1. Capturer le delta réel, puis en extraire les ancres

Écrire un résumé court de **ce que cette clôture a réellement changé** — pas ce que l'issue
promettait, ce qui a été *fait*. Sources : le **diff mergé**
(`gh pr view <n> --json files,title,body`, `git log`), les **décisions actées** pendant le
développement (scope resserré ou élargi, hypothèse tranchée, format figé, edge case décidé), et les
**follow-ups différés** notés dans la PR.

Restituer sous `## 📦 Delta réel` : des faits courts et vérifiables.

Puis en extraire les **ancres** — les chaînes recherchables que d'autres issues pourraient
mentionner :

- noms de types, de fonctions, de champs publics touchés ;
- routes, endpoints, clés de payload, formats de données ;
- noms de modules / domaines déplacés, créés ou supprimés ;
- termes métier dont le sens a été tranché.

Chaque ancre doit provenir du diff ou d'une décision écrite. **Une ancre qu'on ne peut pas
rattacher à un fait du delta n'est pas une ancre.**

### 2. Sélectionner les issues à examiner

Sur le dépôt de `.claude/pipeline.config.md` :

1. **Même thème** — `gh issue list --state open --milestone "<thème de l'issue fermée>"`.
2. **Match d'ancre** — pour chaque ancre : `gh issue list --state open --search "<ancre>"`.

L'union des deux constitue le périmètre d'examen. **Le reste du backlog n'est pas examiné.**

Annoncer les décomptes sans rien masquer : « 4 issues du thème + 3 issues matchant une ancre = 6
issues examinées (une en commun) ; 22 autres issues ouvertes non examinées. » Si l'issue fermée n'a
pas de thème, ou si le merge ne ferme aucune issue, le périmètre se réduit aux matchs d'ancre.

**Ignorer les issues déjà réconciliées** avec cette issue fermée (voir le Journal de spec, étape 5)
— c'est ce qui rend le skill relançable sans retravail.

#### Marquer les issues « en vol »

Une issue **dormante** (planifiée, personne ne travaille dessus) peut voir son corps réécrit sans
risque. Une issue **en vol** est en cours de développement : une session a **déjà lu son corps** à
son briefing pré-PR et ne le relira pas. Réécrire sa spec sous elle ne la préviendrait de rien —
c'est le pire des cas, elle continuerait sur une spec périmée en croyant être à jour.

Repérer les issues en vol avant toute chose :

```bash
# PR ouvertes, drafts comprises, et ce qu'elles ferment ("Closes #N" / "Fixes #N" / "Resolves #N")
gh pr list --state open --json number,title,body,isDraft,headRefName
```

`cycle-pr` ouvre sa **PR draft à l'Étape 2, avant la première ligne de code**, avec `Closes #N`
dans le body. Une issue en cours de développement a donc **toujours** une PR ouverte qui la
référence — c'est ce qui rend cette détection fiable plutôt qu'approximative. Les drafts comptent
autant que les autres : c'est même leur seule raison d'exister ici.

Lire aussi le tableau de bord **`PR-PARALLELES.md`** s'il existe : toute ligne qui n'est pas
`⚪ worktree nettoyé` désigne une issue en vol. Il sert de filet si une session a sauté l'Étape 2.

Classer chaque issue impactée **dormante** ou **en vol**. Le traitement diffère radicalement
(étape 5) — dans le doute, considérer l'issue en vol : prévenir à tort coûte un commentaire, éditer
à tort coûte une PR construite sur une spec fausse.

### 3. Confronter — deux citations obligatoires

Pour chaque issue examinée, lire corps + brief d'agent, et chercher ce qui est devenu **faux**.

Une répercussion n'est retenue que si l'on peut produire **les deux citations** :

```
Citation issue : « <la ligne exacte du corps qui est devenue fausse> »
Citation delta : « <le fait exact du delta réel qui la falsifie> »
```

**Si l'une des deux manque, il n'y a pas de répercussion — ne pas la formuler.** Une impression
(« ça pourrait interagir avec… », « il faudra peut-être vérifier… ») n'est pas une citation. C'est
exactement ce qui noie le rapport et rend indécidable ce qui est vrai.

Deux niveaux, et deux seulement :

- **bloquant** — la spec est fausse sur un point structurant ; développer l'issue en l'état
  produirait du travail à jeter.
- **à ajuster** — la spec reste globalement valable, une référence ou un périmètre doit être repris.

### 4. Présenter les corrections sous forme de diff

Sous `## 🔭 Répercussions`, **uniquement les issues impactées**, groupées par niveau :

```
#52 — Export CSV des factures                        [bloquant] [dormante]
  Type   : contrat déplacé
  Issue  : « le total est exprimé en euros dans `Invoice.total` »
  Delta  : « `Invoice.total` est passé en centimes (entier) »
  ── correction proposée dans le corps ──
  - le total est exprimé en euros dans `Invoice.total`
  + le total est exprimé en centimes (entier) dans `Invoice.total` (voir #47)

#58 — Relances de paiement                    [bloquant] [EN VOL → PR #61]
  Type   : contrat déplacé
  Issue  : « comparer `Invoice.total` au seuil en euros »
  Delta  : « `Invoice.total` est passé en centimes (entier) »
  ── corps NON modifié — signalement sur la PR #61 ──
  La session développe déjà contre l'ancien contrat.
```

Toujours afficher le marqueur **[dormante]** ou **[EN VOL → PR #n]** : c'est lui qui dit au
mainteneur si une session est en train de partir dans le mur.

Montrer les **lignes** avant/après, pas une prose qui décrit le changement : un diff se juge en
deux secondes, un paragraphe demande de raisonner.

Si aucune issue n'est impactée, le dire en une ligne — « Aucune répercussion : la clôture de #47 ne
rend fausse la planification d'aucune issue examinée. » — et s'arrêter là.

### 5. Appliquer — sur « go » explicite

Après le « go » (global, ou issue par issue si le mainteneur préfère trier).

#### Issues dormantes → éditer le corps

**Éditer le corps** de chaque issue retenue, en appliquant exactement le diff présenté. Ne jamais
profiter de l'édition pour reformuler autre chose.

**Relire le corps juste avant d'écrire.** S'il a changé depuis la présentation du diff — une autre
passe de répercussions a pu passer entre-temps, ou le mainteneur a édité — ne pas écrire par-dessus :
re-présenter le diff recalculé. Deux merges rapprochés font tourner deux passes qui peuvent viser
la même issue.

#### Issues en vol → signaler sur la PR, ne rien éditer

Pour une issue en vol, **le corps reste intact** et **aucun label ne change**. La session qui la
développe a déjà lu ce corps ; le modifier ne l'atteindrait pas, et la repasser en
`needs-interrogation` alors qu'une PR est ouverte n'a pas de sens.

Le signalement va **en commentaire sur la PR ouverte** — c'est la seule sortie GitHub commentée de
ce skill, et elle est justifiée : `cycle-pr` traite déjà les commentaires de PR à son Étape 6, en
bouclant jusqu'à review vide. Le message atterrit donc exactement là où la session le lira.

```markdown
> *Généré par IA — répercussion de la clôture de #47.*

**⚠️ Répercussion bloquante sur la spec de cette PR**

L'issue #58 affirme : « comparer `Invoice.total` au seuil en euros ».
La clôture de #47 a acté : « `Invoice.total` est passé en centimes (entier) ».

Le corps de l'issue **n'a pas été modifié** (développement en cours). À intégrer dans cette PR,
ou à remonter au mainteneur si cela change le périmètre.
```

Un signalement **bloquant** sur une issue en vol se remonte **en tête du récapitulatif** (étape 6) :
c'est une session en train de construire quelque chose de faux, et le mainteneur doit décider s'il
la met en pause.

#### Transitions et fermetures (issues dormantes uniquement)

**Ajouter la ligne de journal**, en bas du corps :

```markdown
<!-- repercussions -->
### Journal de spec
- Réconciliée avec #47 — `Invoice.total` passé en centimes.
```

Une ligne par issue fermée réconciliée. C'est la **clé d'idempotence** de l'étape 2. Au-delà de
cinq lignes, compacter les plus anciennes en une seule (« Réconciliée avec #12, #19, #23 »).

**Repasser en `needs-interrogation`** toute issue `ready-for-agent` ou `ready-for-human` dont
l'édition touche le **périmètre** ou une **décision verrouillée** : son interrogatoire portait sur
une spec qui n'existe plus, il doit être refait. Une simple mise à jour de référence ne déclenche
pas ce retour en arrière.

**Fermer en doublon** — seul cas où ce skill ferme quelque chose. Exige un recouvrement **total et
non ambigu**, et un **« go » nommément sur cette issue** (un « go » global ne suffit pas à fermer).
Recouvrement partiel → on réduit le périmètre dans le corps, on ne ferme pas.

Au moindre cas ambigu — re-découpage non trivial, conflit de conception, fermeture incertaine —
**ne pas trancher seul** : le poser au mainteneur et laisser l'issue intacte.

### 6. Récapituler dans la conversation

**En tête : les signalements bloquants sur issues en vol** — sessions qui développent contre une
spec devenue fausse, avec la recommandation (poursuivre en intégrant la correction, ou mettre en
pause). C'est la seule information de ce rapport qui est urgente.

Puis : ce qui a été édité, ce qui est repassé en `needs-interrogation`, ce qui a été fermé, les
points laissés à l'arbitrage, et le nombre d'issues non examinées.

### 7. Le thème est-il terminé ? — proposer la campagne de QA

L'issue fermée appartenait à un **thème** (milestone). Vérifier s'il en reste des issues ouvertes :

```bash
gh issue list --state open --milestone "<thème de l'issue fermée>" --json number
```

**S'il n'en reste aucune, le thème vient de se terminer.** C'est la seule frontière de lot que
cette pipeline produise naturellement — et donc le bon moment, et le seul, pour proposer une
campagne de QA :

> « Le thème **Facturation** n'a plus d'issue ouverte (7 fermées). Lancer `/plan-qa` dessus ? »

Conditions pour proposer :

- le milestone est vide d'issues ouvertes ;
- **et** au moins une de ses issues touchait une surface visible du projet (surfaces déclarées dans
  `.claude/pipeline.config.md`). Un thème purement interne — refacto, outillage, dette — n'a rien à
  faire recetter à la main : ne rien proposer.

**Proposer, jamais lancer.** Et ne proposer qu'une fois par thème : si le milestone porte déjà une
issue `qa-plan`, se taire. Une proposition qu'on décline neuf fois sur dix devient un bruit qu'on
apprend à ignorer — c'est précisément ce qu'on cherche à éviter en ne la déclenchant qu'ici.

## Ce que ce skill ne fait pas

- **Il ne commente aucune issue.** Unique exception, décrite à l'étape 5 : un commentaire sur une
  **PR ouverte** quand l'issue qu'elle développe est impactée — parce que c'est le seul canal que
  la session en cours lira.
- **Il ne crée aucune issue.** Un besoin non couvert révélé par la clôture n'est pas une
  répercussion : c'est du travail neuf → `vers-issues` ou `bug-vers-issue`, à la main du mainteneur.
- **Il ne re-trie pas.** La seule transition d'état qu'il applique est le retour en
  `needs-interrogation` décrit ci-dessus ; tout autre changement d'état passe par `triage`.
- **Il ne relit pas le code.** Il confronte des specs à un delta, il n'audite pas la codebase.

## Les 4 idées à retenir

1. **Le livrable est un corps d'issue corrigé.** Aucun commentaire d'issue — un commentaire laisse
   le texte faux en place.
2. **Deux citations ou rien.** La ligne devenue fausse et le fait qui la falsifie. Sans les deux,
   la répercussion n'existe pas.
3. **Dormante ou en vol.** On réécrit la spec d'une issue que personne ne développe ; on **prévient
   sur sa PR** celle qui est en chantier. Éditer sous les pieds d'une session en cours est le seul
   dégât irrattrapable que ce skill puisse causer.
4. **Périmètre mécanique** (thème + ancres) et **idempotence** (journal de spec) : le skill se
   relance après chaque merge sans re-brasser le backlog.
