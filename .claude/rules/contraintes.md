# Règle — Contraintes permanentes (à chaque commit)

Ces contraintes sont actives en continu, sur **chaque** commit, sans qu'on ait à les rappeler.

## Intégrité de l'historique
- **Aucun commit cassé n'entre dans l'historique.** La qualité est garantie *à chaque commit*,
  pas seulement à la fin. Si les tests sont rouges → pas de commit.
- **Jamais de force-push** sur une PR ouverte (sauf rebase/squash explicitement demandé), et
  **jamais** sur `main`.
- **Jamais d'auto-merge.** Même avec CI verte et audit propre, toujours attendre un « go » /
  « merge » humain explicite.

## Propreté du code
- **Aucun code mort, aucun scaffold inutilisé.** Supprimer les imports / classes /
  commentaires-tutoriels générés par les outils ; ne garder que ce qui sert *maintenant*.
- **Pas de fichiers placeholder « au cas où ».**
- **Pas d'imports wildcard / glob**, quelle que soit la forme qu'ils prennent dans le langage.
- **Aucune sortie de debug laissée en place** (log/print/console temporaire), ni `TODO`/`FIXME`
  sans propriétaire et explication.

## Qualité de conception
Le code visé est **modulaire, scalable, fractionné** — objectif permanent, pas une option :

- **Modulaire** : modules à responsabilité unique, derrière des interfaces petites et stables.
  Viser des **modules profonds** — petite interface, implémentation riche
  (`cycle-pr/references/modules-profonds.md`), jamais des modules qui passent-plat.
- **Fractionné** : décomposer les fonctions, séparer les responsabilités. Pas de fonction
  fourre-tout, pas de fichier monolithique.
- **Scalable** : concevoir pour que l'ajout d'un cas se fasse par **extension** plutôt que par
  modification invasive. Éviter le couplage fort et les hypothèses qui ne tiennent qu'à petite
  échelle (boucles N+1, état global, limites en dur non justifiées).

## Règle d'or — toujours poser un maximum de questions
- **Poser systématiquement un maximum de questions pour lever toute incertitude**, le plus tôt
  possible. Une question posée maintenant coûte 30 secondes ; la même ambiguïté découverte plus
  tard coûte une demi-journée.
- **Au moindre doute, on s'arrête et on demande.** Jamais de supposition silencieuse sur le scope,
  le format des données, les transitions d'état, les comportements attendus.
- **Toute prise de décision non triviale dans le doute → demander avant de trancher.** Choix
  d'architecture, de découpage, de format, de dépendance, de comportement : on ne décide pas en
  silence à la place de l'utilisateur. Présenter les options + une reco, puis demander.
- Exception : si la réponse se trouve dans le code, **explorer le code plutôt que demander**. Pour
  un grilling approfondi, utiliser `interroge-moi`.

## Maintenance continue
- Tenir à jour, sans qu'on le redemande, les supports d'exécution du projet : fichier de commandes
  (`Makefile` / `justfile` / scripts du manifeste) et `.env.example`.
- Si une commande du projet change (test, lint, build…), mettre à jour la section « Commandes »
  de `.claude/pipeline.config.md` **dans le même commit** — c'est elle que les skills lisent.
- **Tenir la documentation à jour dans le même commit que le changement** : `README`, `docs/`,
  `CLAUDE.md`, glossaire de domaine (`UBIQUITOUS_LANGUAGE.md`), docstrings/commentaires. Si un
  commit change un comportement, une commande, une interface ou l'architecture, la doc
  correspondante est mise à jour *dans ce commit* — jamais « plus tard ». Une doc fausse est pire
  qu'une doc absente.

## Points d'arrêt humains
- Commit touchant une **zone sensible** déclarée dans `.claude/pipeline.config.md` (section
  « Périmètre ») → rendre la main pour validation manuelle **avant** de committer.
- Par défaut, sont sensibles : l'**UI à valider visuellement** et tout changement de **schéma de
  données / migration**.
