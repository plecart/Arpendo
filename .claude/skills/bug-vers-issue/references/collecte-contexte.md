# Liste de contrôle de collecte du contexte

Ce que `bug-vers-issue` doit rassembler avant de rédiger le corps d'une issue. Saute une source si elle est réellement indisponible ; sinon, vérifie-la.

## 1. Contexte de la conversation

- La description la plus récente du bug par l'utilisateur, avec ses propres mots.
- Tout bloc d'**intake d'échec** capturé produit par `execution-qa` — c'est l'entrée de la plus haute qualité. Utilise les champs tels quels ; ne les paraphrase pas.
- Toute clarification que l'utilisateur a déjà donnée dans ce tour ou les ~10 derniers tours.

## 2. Lien vers le plan QA (mode piloté par un plan)

- Numéro de l'issue du plan.
- Texte exact de la ligne de la case en échec (copier-coller depuis le corps du plan).
- Nom de la phase ou du bloc par issue.
- Règle d'arrêt du bloc, le cas échéant.

Si plusieurs cases du même bloc ont échoué pour la même cause racine, note-les toutes sous « Découvert pendant ». Si elles ont des causes racines différentes, cela peut suggérer un découpage.

## 3. Issue(s) d'implémentation

En **mode piloté par un plan** : le bloc par issue dans le plan nomme la ou les issues d'implémentation. Utilise-les.

En **mode libre** : essaie, dans l'ordre :
- Cherche les issues récemment fusionnées touchant la zone concernée : `gh issue list --search "<termes clés> is:merged" --limit 10` (puis remonte des PR aux issues).
- `git log -- <chemins pertinents> --oneline -20` et repère les messages de commit qui référencent des numéros d'issue.
- Si ni l'un ni l'autre ne donne de réponse claire, liste les candidats les plus proches et laisse l'utilisateur trancher.

## 4. PRD

- Regarde le corps de l'issue d'implémentation pour une référence `Parent: #<prd>`.
- Regarde la section « Vue d'ensemble » du plan QA.
- Si trouvé, récupère-le avec `gh issue view <prd> --json title,url`. N'inclus le lien que si tu es sûr qu'il s'agit du bon PRD.

## 5. Commit(s) à l'origine

- `git log --grep="#<issue-impl>" --oneline -20` pour chaque issue d'implémentation.
- `git log -- <chemins de fichiers ou modules pertinents> --oneline -20`.
- Recoupe : un commit est un coupable probable s'il touche à la fois la surface défaillante ET référence l'issue d'implémentation.
- Liste jusqu'à 3 candidats sous la forme `<sha-court> — <message du commit>`. N'en liste pas plus — trop de candidats diluent la trace.

## 6. Langage métier

À lire une fois par session :

- `UBIQUITOUS_LANGUAGE.md` (ou le fichier glossaire du projet).
- `CLAUDE.md` s'il est présent.
- Les noms de route / composant / table utilisés dans la surface défaillante — ce sont les noms communs du projet.

Utilise ces termes dans le titre et le corps de l'issue. Remplace les noms de symboles internes (`uploadHandler`, `validateSize`) par leurs équivalents métier (`envoi de document de connaissance`, `validation de la taille de fichier`).

## 7. Recherche de doublons

Avant de rédiger :

- Corps du plan : `grep -n "🔴 BUG #" <corps-du-plan>` et vérifie si l'un d'eux se trouve sur ou près de la case en échec.
- Outil de suivi : `gh issue list --search "<3-4 termes clés>" --state all --limit 10`.
- Montre les candidats à l'utilisateur et demande avant de consigner une nouvelle issue.

## Ce qu'il NE FAUT PAS inclure

- Les chemins de fichiers et numéros de ligne précis — ils deviennent obsolètes.
- Les extraits de code complets — ils deviennent obsolètes.
- Les noms de classe / fonction internes — ils deviennent obsolètes.
- Les diagnostics spéculatifs (« c'est probablement causé par X ») — sauf si tu l'as réellement vérifié, c'est du bruit.
- Tout ce qui crée une dépendance obsolète dans le corps de l'issue. Du comportement, pas du code.
