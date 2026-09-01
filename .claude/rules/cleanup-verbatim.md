# Règle — Le prompt de relecture (cleanup pass)

**Dès que le travail demande de relire, nettoyer ou améliorer du code**, exécuter **ce prompt mot
pour mot**. Ne jamais le paraphraser, ne jamais le raccourcir, ne jamais le recopier ailleurs.

Cela couvre aussi bien les étapes de la pipeline (cycle de commit, auto-review de PR, refactor
TDD, avant merge) qu'une **demande directe et informelle** de l'utilisateur — « relis ça »,
« nettoie ce fichier », « améliore ce code », « tu peux revoir ce que tu viens d'écrire ? ».
Il n'y a pas de relecture « informelle » qui échapperait à ce prompt : s'il s'agit de repasser sur
du code, c'est ce prompt qui s'applique.

> Veuillez examiner l'ensemble du code ajouté et des modifications apportées aux fichiers
> existants. Réorganisez, structurez, optimisez et nettoyez ces modifications pour produire un
> code clair, cohérent et facilement maintenable. Éliminez tout code dupliqué, inutile ou
> obsolète. Décomposez les fonctions et séparez les responsabilités en suivant les principes
> KISS, DRY et YAGNI. Rendez le code le plus **générique et modulaire** possible : des unités à
> responsabilité unique, découplées de leur contexte d'appel, réutilisables telles quelles, et
> conçues pour que l'ajout d'un cas se fasse par extension plutôt que par modification — sans
> pour autant anticiper un besoin non avéré. L'objectif est d'obtenir un code propre, clair,
> concis, générique, modulaire et optimisé.

## Comment l'appliquer

- **Examen fichier par fichier**, pas un regard global vague. Pour chaque fichier modifié, lister
  les findings concrets : magic numbers, duplication, naming douteux, fonction trop longue,
  responsabilité mal séparée, code mort.
- **Rapporter à voix haute** sous un titre `## 🧹 Cleanup pass`, pour que le relecteur vérifie
  d'un coup d'œil que l'étape n'a pas été sautée.
- **Même rigueur sur les deltas triviaux.** Si « rien à corriger », l'expliquer ligne par ligne
  plutôt que de l'affirmer.
- **Un constat qui décrit une classe de défaut se traite en balayant toute la population
  concernée**, jamais les seules occurrences citées — un constat de relecture est un échantillon,
  pas un inventaire. Le rapport énonce le dénombrement (« N éléments repassés, k corrigés, N−k
  vérifiés indemnes »), pas « les 2 constats sont corrigés ». Quand la classe est reconnue,
  inscrire le critère dans l'artefact lui-même pour qu'il tienne sans relecteur.
- **Vérifier aussi les 3 axes de conception** de `.claude/rules/contraintes.md` (modulaire /
  fractionné / scalable), en plus de KISS / DRY / YAGNI.
- **Relancer les tests après le cleanup** : il a pu casser quelque chose.
