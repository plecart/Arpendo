---
name: execution-qa
description: À utiliser pour dérouler un plan de QA créé par plan-qa — généralement une issue GitHub étiquetée `qa-plan` (ou un fichier de repli `docs/qa/qa-plan-*.md`). Déclencheurs : « lance la QA », « continue la phase QA », « déroule le plan de QA », « valide la checklist QA », « reprends la campagne QA », « faisons la QA de #N », ou toute session où l'utilisateur veut parcourir un plan en phases avec l'agent.
---

# Compagnon d'exécution QA

Accompagne l'utilisateur à travers un plan de QA existant, phase par phase, en cochant les cases directement dans le corps de l'issue du plan de QA à mesure qu'elles passent, et en routant les échecs vers `bug-vers-issue` uniquement avec une confirmation explicite de l'utilisateur. Le plan EST la trace — il n'y a pas de fichier de trace séparé.

## Principe fondamental

Chaque case basculée en `[x]` doit reposer sur une preuve observée. Chaque échec offre à l'utilisateur trois options explicites (déposer, reporter, corriger en session). Ne jamais auto-invoquer `bug-vers-issue`. **Ne jamais fusionner deux surfaces en un seul verdict** quand une seule a été réellement testée — « le service répond » ne dit rien de ce que l'utilisateur voit.

## Processus

### 1. Localiser le plan de QA

Par ordre de priorité :

1. **Argument fourni** — `/execution-qa #142` → utiliser l'issue 142.
2. **L'argument est un chemin** — `/execution-qa docs/qa/qa-plan-x.md` → utiliser le fichier (mode de repli markdown).
3. **Pas d'argument** — `gh issue list --label qa-plan --state open --json number,title,createdAt --limit 20`. S'il existe exactement une issue `qa-plan` ouverte, l'utiliser. S'il y en a plusieurs, les lister et demander. S'il n'y en a aucune, chercher `docs/qa/qa-plan-*.md`. S'il n'y en a toujours aucune, dire à l'utilisateur d'exécuter `plan-qa` d'abord et s'arrêter.

Récupérer le corps une fois : `gh issue view <N> --json body -q .body > /tmp/qa-plan-<N>.md`. Conserver cela comme copie de travail que tu patches et repousses. Re-récupérer avant chaque push pour capter les éditions concurrentes de l'utilisateur — voir `references/patch-checkbox-gh.md`.

### 2. Établir l'état courant

- Analyser le corps du plan. Identifier chaque ligne de case, sa phase / son bloc, et son état courant (`[ ]`, `[x]`, `🔴 needs-issue`, `🔴 BUG #N`).
- Trouver le premier point de contrôle non coché ou incomplet — c'est le « suivant ».
- Exécuter `git status --short` et `git log -10 --oneline` pour connaître l'état de l'arbre de travail. Préserver les changements de l'utilisateur ; ne jamais annuler du travail sans rapport.
- Lire tout `CLAUDE.md`, `Makefile`, `docker-compose*.yml`, les routes/composants nommés dans le prochain bloc en attente, et les fixtures de test qu'il référence. Faire cela une fois par bloc, pas une fois par case.

Résumer brièvement à l'utilisateur : quel plan, quelle phase / quel bloc est le suivant, quelle est la règle d'arrêt, quelle sera la première action.

### 3. Boucle d'exécution phase / bloc

Pour chaque phase ou chaque bloc par issue, répéter :

1. **Expliquer le bloc** en 2-3 lignes : objectif, préconditions, surfaces concernées (parmi celles que le projet possède), règle d'arrêt.

2. **Donner l'action suivante** — commandes exactes ou clics UI exacts. Garder des blocs assez petits pour que l'utilisateur puisse examiner les résultats entre les actions. Énoncer les résultats **attendus** avant que l'utilisateur ne les exécute.

3. **Examiner les résultats observés**. Comparer à l'attendu. Si quelque chose manque qui changerait la décision, le demander (code de statut, extrait de corps, ligne de console, nombre de lignes en BD). Ne pas demander de preuve qui ne change pas la décision.

4. **Décider de la case** :
   - **Passe** → basculer `- [ ]` en `- [x]` dans la copie de travail et ajouter une courte annotation en ligne : ` — <résumé de preuve sur une ligne, date ISO>`. Exemple : `- [x] L'utilisateur A liste ses propres ressources — 200, 3 lignes, 2026-05-08`.
   - **Passe avec décision** → basculer en `- [x]` et ajouter ` — Décision : <politique choisie>, <date>`. Enregistrer le choix de l'utilisateur ; s'il nécessite un changement de code, c'est une tâche séparée.
   - **Échec** → voir l'étape 4 ci-dessous (gestion des échecs).
   - **N/A** → basculer en `- [x]` et ajouter ` — N/A : <raison>`.
   - **Bloqué** → laisser `- [ ]`, ajouter ` — BLOQUÉ : <raison>`. Dire à l'utilisateur ce qui le débloque.

5. **Repousser la copie de travail** à la fin du bloc (ou après un sous-groupe significatif au sein d'un bloc long). Utiliser la procédure de patch de `references/patch-checkbox-gh.md` — récupérer une version fraîche, appliquer le diff par correspondance exacte de ligne, pousser. Si une ligne que tu comptais mettre à jour a été éditée par l'utilisateur entre-temps, faire remonter un avertissement et demander avant de forcer.

6. **Décider du statut global du bloc** et publier un commentaire GitHub de synthèse de phase quand il y a une preuve plus lourde à joindre (extraits de logs, sortie de requête BD, captures d'écran). Utiliser `references/gabarit-commentaire-phase.md`. Sauter le commentaire pour les blocs verts triviaux.

### 4. Gérer une case en échec

Ne jamais basculer une case en échec en `[x]`. Ne jamais auto-invoquer `bug-vers-issue`. À la place :

1. Annoter la ligne dans la copie de travail : ` 🔴 needs-issue — <résumé sur une ligne>`.
2. Capturer la preuve de l'échec dans la conversation à l'aide de `references/gabarit-intake-echec.md`. Les champs sans contenu sont supprimés, pas laissés vides.
3. Repousser la copie de travail annotée pour que l'échec soit visible sur l'issue.
4. Offrir à l'utilisateur trois options explicites :
   - **(a) Déposer le bug maintenant** — invoquer `bug-vers-issue` avec la preuve d'échec capturée, le lien du plan de QA, le bloc par issue / la phase concernée, et le commit d'origine si connu. Une fois publié, remplacer le marqueur `🔴 needs-issue` par `🔴 BUG #<nouveau-numéro>` dans la copie de travail et repousser. Mise en avant par défaut.
   - **(b) Reporter** — laisser `🔴 needs-issue`, continuer la QA, déposer plus tard en lot.
   - **(c) Corriger en session** — uniquement quand l'utilisateur le demande explicitement. Passer en mode correction à la racine en utilisant `references/standard-correction-bug.md`. Une fois la correction en place et les tests au vert, ré-exécuter l'action en échec. En cas de succès, basculer `- [ ]` → `- [x]` et ajouter `— corrigé en session, <sha-commit>, <date>`.

Après l'option (a) ou (c), mettre à jour l'**Index des constats** au bas du corps du plan avec une entrée d'une ligne : `🔴 #<issue-bug> — <titre> — phase / bloc : <où>`.

### 5. Règles d'arrêt et passation entre phases

- Respecter chaque règle d'arrêt du plan. Si une règle d'arrêt se déclenche, ne pas démarrer la phase / le bloc dépendant suivant. Dire à l'utilisateur ce qui bloque et ce qui débloquerait.
- Après que chaque phase / bloc atteint un état terminal, résumer : « Phase X — passée / partielle / bloquée. Backend : <état>. Frontend : <état>. BD / logs : <état>. Suivant : <phase Y>. »
- Ne jamais fusionner deux surfaces en un seul verdict quand une seule a été testée.

### 6. Définition du Terminé

La phase finale du plan est la Définition du Terminé explicite. En l'approchant :

- Vérifier que chaque case requise de Phase 0 / Phase 1 / par issue / Phase R est `[x]` (ou explicitement `N/A : <raison>` ou `accepté : <décision>`).
- Vérifier que chaque constat bloquant a un lien `🔴 BUG #N` (déposé) ou une annotation explicite `accepté par l'utilisateur, <date>`.
- Ré-exécuter les commandes finales listées dans le plan après toute correction en place.
- Repousser la copie de travail finale.
- Dire à l'utilisateur que la campagne est terminée et résumer l'index des constats.

## Patrons par surface

Les deux patrons ci-dessous ne s'appliquent qu'aux **surfaces que le projet possède réellement**
(déduites de `.claude/pipeline.config.md`, sections Stack et Périmètre — le plan de QA les a déjà
tranchées). Sur un projet sans interface, le patron frontend ne s'applique pas ; sur une lib sans
persistance, les vérifications de ligne non plus. Ne pas dérouler un patron pour une surface
absente, et ne pas inventer de commandes pour une couche qui n'existe pas.

### Patron service / API / CLI

- Utiliser un `$QA_RUN` frais et isolé (horodatage). Créer des utilisateurs distincts pour les tests de propriété.
- Stocker les IDs dans des variables d'environnement (`$USER_A_TOKEN`, `$DOC_A_ID`) pour que les commandes suivantes soient copiables-collables.
- Pour chaque ressource liée à un utilisateur : lecture par le propriétaire, lecture inter-locataires, jeton manquant, jeton invalide.
- Pour chaque persistance : vérification de ligne (FK propriétaire, statut, horodatages, champs d'erreur).
- Pour chaque upload : le chemin de stockage existe, la taille correspond, les originaux sont préservés.
- Pour chaque job asynchrone : état terminal (succès et échec), logs du worker bornés.
- Un 500 inexpliqué est au minimum majeur.

### Patron interface

- Indiquer à l'utilisateur l'URL, le compte et l'état du navigateur à utiliser (« vider localStorage et recharger », « activer preserve log dans DevTools »).
- Toujours demander les observations Console + Réseau.
- Vérifier l'ensemble des états : vide / chargement / succès / erreur / échoué.
- Vérifier que le détail d'erreur backend est visible, pas remplacé par un wrapper générique.
- Vérifier que les boutons sont désactivés pendant l'attente.
- Vérifier que le polling s'arrête sur les états terminaux.
- Vérifier que le rafraîchissement / la persistance du contexte se comporte comme le plan l'indique.
- Recouper BD / logs après les opérations UI.

## Décisions de politique

Quand le comportement est réellement ambigu :

1. Énoncer le comportement actuel (d'après le code).
2. Énoncer le risque.
3. Recommander une politique.
4. Demander à l'utilisateur de décider.
5. Enregistrer la décision en ligne sur la case concernée : `— Décision : <politique choisie>, <date>`.
6. N'implémenter des changements de code que si la politique choisie l'exige — c'est une tâche séparée, pas une partie du cochage de la case.

## Passe finale avant de déclarer une phase terminée

Avant de répondre « phase X passée » :

- [ ] Chaque case de la phase / du bloc est `[x]` ou porte une annotation explicite de non-passage (`N/A`, `BLOQUÉ`, `🔴`, `accepté`).
- [ ] Chaque surface **existante** du projet (service/API/CLI, interface, persistance, traitements asynchrones, artefacts) est marquée individuellement là où c'est pertinent — jamais fusionnée en un verdict unique.
- [ ] La preuve plus lourde (logs / lignes BD / captures d'écran) est dans un commentaire de synthèse de phase, pas entassée en ligne.
- [ ] Chaque échec a un lien `🔴 BUG #N` OU une annotation reporté / accepté.
- [ ] La copie de travail est repoussée sur l'issue ; aucune édition uniquement locale ne subsiste.
- [ ] L'Index des constats reflète tous les bugs déposés dans cette phase.
- [ ] Aucune nouvelle erreur console / réseau / log sur les surfaces antérieures (vérification de régression).

## Erreurs courantes

| Erreur | Correction |
|---|---|
| Basculer `[x]` sans preuve observée | Toujours exiger : commande exécutée, statut / corps / ligne / log vu. |
| Fusionner deux surfaces en une seule affirmation de passage | Suivre chaque surface indépendamment, et ne rien affirmer d'une surface non testée. |
| Auto-invoquer bug-vers-issue sur un échec | Toujours proposer les trois options d'abord. Mise en avant par défaut = (a) déposer. |
| Maintenir un fichier de trace séparé | Non. Le corps du plan et ses commentaires SONT la trace. |
| Déverser d'énormes logs dans le corps du plan | Les commentaires de synthèse de phase reçoivent la preuve lourde. Le corps garde les annotations en ligne courtes. |
| Patcher le corps de l'issue sans re-récupérer | Toujours re-récupérer avant de pousser — voir `references/patch-checkbox-gh.md`. |
| Démarrer la phase suivante alors qu'une règle d'arrêt est active | Respecter la règle d'arrêt jusqu'à ce que l'utilisateur accepte explicitement l'exception. |
| Corriger un bug en session par défaut | Déposer d'abord, corriger seulement sur opt-in explicite de l'utilisateur. |
