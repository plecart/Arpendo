# Règle — Une décision ne contredit jamais la doc en silence

S'applique à **toute décision prise en conversation** : réponse à une question, formulaire rempli,
arbitrage en cours de route, « décision verrouillée » d'un briefing ou d'un brief d'agent.

## Chercher avant de verrouiller

Avant d'inscrire une décision où que ce soit (brief, issue, PR, code, doc), **chercher son sujet
dans les sources de vérité** — `.claude/pipeline.config.md`, section « Sources de vérité ». Un
`grep` sur deux ou trois termes d'ancre suffit : nom de composant, terme métier, nom de champ,
route, § pressenti.

Pour un changement qui **remplace une valeur par une autre** — montée de version, nouveau défaut,
renommage — les ancres incluent **la valeur visée**, pas seulement celle en place. Une doc peut
être muette sur la nouvelle valeur, l'épingler, ou l'avoir **explicitement écartée** avec son
motif : trois situations différentes, et seule la troisième est une contradiction. Chercher
seulement la valeur qu'on retire fait manquer le cas où l'arrêt est le plus justifié.

Ce n'est pas une formalité. Les documents de référence pèsent ~320 Ko : ils ne sont **jamais** en
contexte. **Une contradiction ne se remarque pas, elle se cherche.**

**Cas le plus fréquent : la recommandation d'un skill tiers.** Un skill générique propose *son*
défaut, pas celui du projet. Toute valeur, dépendance, police, durée ou pattern venu d'un skill non
maison passe par la recherche ci-dessus **avant** d'être proposé.

## Deux citations, sinon silence

Il n'y a contradiction que si l'on peut produire les deux :

- **Citation source** — la ligne exacte du document ou du corps d'issue, avec son **§** (jamais un
  numéro de ligne).
- **Citation décision** — ce qui vient d'être décidé, et qui la rend fausse.

Un document **muet** sur le point n'est pas contredit : c'est un vide, on le comble sans rien
signaler. Un document qui dit « une couleur d'accent » quand on choisit laquelle n'est pas
contredit : c'est une précision. **Sans les deux citations, il n'y a rien à signaler.** C'est ce
seuil qui empêche le warning de devenir un bruit qu'on apprend à ignorer.

## L'arrêt

Contradiction avérée → **s'arrêter avant d'aller plus loin** et afficher :

```
## ⚠️ Contradiction — <fichier> §<n> (rang <r>)
Avant  : « <la ligne exacte du document> »
Après  : « <la décision qui vient d'être prise> »
Cascade: <ce que le rang atteint entraîne — spec UX, issues #…, pipeline.config.md>
Es-tu sûr du changement ?
```

## Deux sorties, pas trois

1. **Le document gagne** — la décision est abandonnée, on reprend le fil.
2. **La décision gagne** — le document est **amendé maintenant**, dans cette session, via
   `/contradiction` (qui propage aux rangs inférieurs et aux issues).

Si l'amendement est trop gros pour maintenant, l'échappatoire n'est pas « plus tard » : c'est un
**critère ou une issue ouverts sur-le-champ**, portant les deux citations, par la règle
« Création d'issues en cours de cycle » de `contraintes.md` — propriétaire ouvert d'abord,
brouillon soumis au mainteneur sinon. Une décision qui survit à l'arrêt sans que rien ne soit écrit laisse deux
sources normatives en contradiction — c'est exactement l'incident que cette règle existe pour
éviter.
