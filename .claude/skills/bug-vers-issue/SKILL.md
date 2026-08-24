---
name: bug-vers-issue
description: À utiliser lorsqu'un bug fait surface et doit être consigné comme une issue GitHub avec le contexte QA / implémentation / PRD attaché. Déclencheurs : « ouvre une issue pour ce bug », « consigne ça comme un bug », « c'est cassé, logue-le », tout échec surfacé par execution-qa que l'utilisateur veut capturer, et les rapports libres de bug en dehors d'un plan QA actif (« ce truc est faux, logue-le »). Montre toujours un brouillon et demande confirmation avant de publier.
---

# Bug vers issue

Capturer un bug — découvert soit pendant l'exécution d'un plan QA, soit lors de tests libres — et le consigner comme une issue GitHub durable et centrée sur l'utilisateur, avec des liens explicites vers le plan QA (s'il y en a un), les issues d'implémentation, le PRD et les commits à l'origine. Montre toujours un brouillon à l'utilisateur et confirme avant de publier.

## Principe fondamental

L'issue de bug doit être **durable** (encore lisible après des refactos majeures), **centrée sur l'utilisateur** (décrit un comportement, pas du code), **traçable** (renvoie vers le plan / le PRD / le commit) et **sans doublon** (ne consigne pas à nouveau pour une case déjà liée à un `🔴 BUG #N`). Toujours pré-publier, ne jamais publier en silence.

## Deux points d'entrée

1. **Piloté par un plan** — invoqué par `execution-qa` (option (a) « consigner maintenant ») ou par l'utilisateur pendant le parcours d'un plan QA actif. L'issue du plan QA est connue ; la case qui échoue est connue.
2. **Libre** — invoqué en dehors d'un plan actif. L'utilisateur décrit un bug rencontré en utilisant l'application. Aucun plan QA à lier.

Le skill détecte le mode dans lequel il se trouve en cherchant : une invocation récente de `execution-qa` dans la conversation, une issue `qa-plan` ouverte avec un marqueur `🔴 needs-issue`, ou la formulation de l'utilisateur.

## Procédure

### 1. Écouter et clarifier légèrement

Laisse l'utilisateur décrire le problème avec ses propres mots. Pose **au plus 2 ou 3 courtes questions de clarification** centrées sur :

- Ce qu'il attendait vs ce qui s'est réellement passé.
- Les étapes pour reproduire, si elles ne sont pas évidentes.
- Si c'est systématique ou intermittent.

Ne sur-interroge pas. Si la description est assez claire pour consigner, passe à la suite. En mode piloté par un plan, l'essentiel se trouve déjà dans l'intake d'échec capturé — le redemander est pénible.

### 2. Rassembler le contexte environnant

Utilise `references/collecte-contexte.md` comme liste de contrôle. En résumé :

- **Contexte de la conversation** — les échanges récents qui cadrent le bug, y compris un bloc d'intake d'échec capturé si `execution-qa` en a produit un.
- **Lien vers le plan QA** (mode piloté par un plan) — numéro de l'issue, texte exact de la case qui échoue, nom de la phase / du bloc par issue.
- **Issue(s) d'implémentation** — la ou les issues qui ont introduit le comportement défaillant. En mode piloté par un plan, dérive-les du bloc par issue. En mode libre, cherche les issues récemment fusionnées touchant la zone concernée.
- **PRD** — récupère-le s'il est connu depuis l'issue d'implémentation ou le plan QA.
- **Commit(s) à l'origine** — `git log --grep="#<issue-impl>" --oneline -20` et `git log -- <chemins pertinents> --oneline -20`. Choisis le ou les coupables les plus probables ; liste-les en SHA court + message.
- **Langage métier** — lis `UBIQUITOUS_LANGUAGE.md`, `CLAUDE.md`, ou parcours la zone du code pour apprendre les termes du projet. Utilise-les dans le titre et le corps de l'issue. N'utilise pas les noms de modules internes.

### 3. Vérifier les doublons

Avant de rédiger :

- Si piloté par un plan, parcours le corps du plan QA à la recherche de marqueurs `🔴 BUG #<N>` près de la case qui échoue. Si un tel marqueur existe déjà pour cette case précise, signale-le à l'utilisateur et demande s'il faut consigner une nouvelle issue sœur ou rouvrir / commenter celle qui existe. Ne consigne pas en silence.
- Cherche dans les issues récentes : `gh issue list --search "<termes clés>" --state all --limit 10`. Montre à l'utilisateur les correspondances proches avant de rédiger.

### 4. Décider : issue unique vs découpage

Privilégie l'**issue unique**. Ne découpe que lorsque :

- L'utilisateur rapporte des symptômes avec des causes racines clairement séparables que différentes personnes pourraient corriger en parallèle.
- Ou bien les corriger ensemble produirait une PR pire que de les corriger individuellement.

Sinon, consigne une seule issue. Le gabarit d'issue unique se trouve dans `references/gabarit-issue-bug.md`. Le gabarit de découpage se trouve dans `references/gabarit-issue-decoupage.md`. En mode découpage, consigne une issue parente de suivi plus des issues enfants, dans l'ordre des dépendances, pour que les bloqueurs soient référencés par de vrais numéros.

### 5. Rédiger le corps

Utilise le gabarit pertinent dans `references/`. Remplis :

- **Titre** — court, en langage métier, décrit le problème visible par l'utilisateur (pas le chemin de code). Moins de ~70 caractères.
- **Ce qui s'est passé** — comportement observé, en langage clair.
- **Ce que j'attendais** — comportement attendu.
- **Étapes pour reproduire** — concrètes, numérotées, copiables-collables.
- **Découvert pendant** — lien vers l'issue du plan QA + phase / bloc + texte exact de la case (piloté par un plan) OU « QA libre / signalé par l'utilisateur » (libre).
- **Issue(s) d'implémentation** — liens vers la ou les issues qui ont introduit le comportement.
- **PRD** — lien si connu.
- **Commit(s) à l'origine** — SHA courts + messages.
- **Preuves de l'échec** — les champs renseignés de l'intake d'échec. Supprime les champs vides, ne les laisse jamais en `<vide>`.
- **Gravité** — bloquant / majeur / mineur avec une justification d'une ligne.
- **Zone de correction suggérée** — uniquement si elle est évidente d'après l'exploration ; sinon, omets-la.

Règles pour le corps :

- Pas de chemins de fichiers, pas de numéros de ligne — ils deviennent obsolètes.
- Langage métier, pas de noms de modules internes.
- Un développeur doit pouvoir lire l'issue en 30 secondes et reproduire en 2 minutes.

### 6. Montrer le brouillon, confirmer, puis publier

Montre toujours à l'utilisateur le brouillon complet (titre + corps + labels) et demande : **« On le publie tel quel, on l'édite, ou on annule ? »**

Après approbation, publie :

```bash
gh issue create \
  --title "<titre>" \
  --label qa-finding --label needs-triage \
  --body-file <brouillon>
```

En cas de découpage, crée d'abord le parent, puis les enfants dans l'ordre des dépendances, en renseignant `Bloqué par : #<parent>` au fur et à mesure.

### 7. Après la publication

- Affiche l'URL de chaque issue créée.
- Si piloté par un plan, édite le corps de l'issue du plan QA : remplace `🔴 needs-issue` sur la case qui échoue par `🔴 BUG #<nouveau-numéro>`. Ajoute une entrée à l'**Index des constats** en bas du corps du plan. Utilise la procédure de patch décrite dans `execution-qa/references/patch-checkbox-gh.md`.
- Dis à l'utilisateur que le bug est consigné, que le plan a été mis à jour, et que la QA peut reprendre.

## Règles du corps d'issue (tous les modes)

- **Pas de chemins de fichiers ni de numéros de ligne.**
- **Langage métier uniquement.**
- **Des comportements, pas du code** — « l'envoi de connaissance accepte un fichier de 30 Mo alors qu'il devrait le rejeter » et non « uploadHandler.ts validateSize() renvoie true à la ligne 42 ».
- **Étapes de reproduction obligatoires.** Si tu ne peux pas les déterminer, demande à l'utilisateur avant de rédiger.
- **Concis.** Un développeur le lit en 30 secondes et le reproduit en 2 minutes.
- **Gravité indiquée** avec une justification d'une ligne.

## Labels

- Toujours : `qa-finding`, `needs-triage`.
- N'applique jamais d'autres labels en silence. Si l'utilisateur veut `priority/high` ou similaire, il peut l'ajouter pendant le tri.

Si `qa-finding` n'existe pas, crée-le : `gh label create qa-finding --description "Bug découvert pendant la QA" --color "B60205"`.

## Erreurs courantes

| Erreur | Correctif |
|---|---|
| Consigner sans montrer le brouillon | Toujours montrer + demander « on le publie ? ». Aucune exception. |
| Consigner un doublon pour une case déjà liée | Parcours d'abord le corps du plan pour repérer `🔴 BUG #N` près de la case. |
| Inclure des chemins de fichiers et des numéros de ligne dans le corps | Ils deviennent obsolètes. Utilise le langage métier et les comportements. |
| Oublier de mettre à jour le plan QA après avoir consigné | Remplace `🔴 needs-issue` par `🔴 BUG #N` et ajoute à l'Index des constats. |
| Découper alors qu'une seule issue suffirait | Privilégie l'unique. Découpe uniquement pour des causes racines séparables. |
| Sauter les liens vers l'issue d'implémentation / le PRD / le commit | Ce sont la trace durable. Inclus-les toujours quand ils sont connus. |
| Appliquer automatiquement de nombreux labels | Seulement `qa-finding` + `needs-triage`. Le tri ajoute le reste. |
| Rédiger sans relire l'intake d'échec capturé par execution-qa | Le bloc d'intake est l'entrée de la plus haute qualité dont tu disposes. Utilise-le tel quel. |
