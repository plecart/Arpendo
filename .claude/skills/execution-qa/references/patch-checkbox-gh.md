# Patcher les cases dans le corps d'une issue GitHub

Comment `execution-qa` met à jour l'issue du plan de QA sans perdre les éditions de l'utilisateur.

## Règle fondamentale

**Toujours re-récupérer le corps avant de pousser. Faire correspondre par texte de ligne exact, pas par index. Faire remonter un avertissement si la ligne que tu comptais mettre à jour a changé.**

## Procédure

### 1. Récupérer le corps courant

```bash
gh issue view <issue-plan> --json body -q .body > /tmp/qa-plan-<N>.md
```

Conserver cela comme copie de travail. Ne pas la muter sur place ; produire une copie patchée.

### 2. Construire le patch en mémoire

Pour chaque case à mettre à jour, conserver une paire `(ancienne_ligne, nouvelle_ligne)`. Exemple :

```
ancienne : - [ ] L'utilisateur A liste ses propres ressources
nouvelle : - [x] L'utilisateur A liste ses propres ressources — 200, 3 lignes, 2026-05-08
```

Appliquer la substitution par **correspondance exacte de ligne complète**. Ne jamais faire correspondre par numéro de ligne. Ne jamais faire correspondre par préfixe seul — un préfixe `- [ ]` n'est pas unique.

### 3. Détecter les éditions concurrentes

Re-récupérer le corps immédiatement avant de pousser :

```bash
gh issue view <issue-plan> --json body -q .body > /tmp/qa-plan-<N>.fresh.md
```

Ré-appliquer toutes les substitutions en attente sur `qa-plan-<N>.fresh.md`. Pour chaque substitution :

- Si l'`ancienne_ligne` est trouvée exactement une fois → appliquer.
- Si trouvée zéro fois → l'utilisateur (ou un autre agent) a édité cette ligne. **S'arrêter et faire remonter un avertissement** à l'utilisateur avec l'`ancienne_ligne` originale et la ligne la plus ressemblante actuellement dans le corps. Demander s'il faut sauter cette mise à jour, forcer une version au mieux, ou abandonner.
- Si trouvée plus d'une fois → le corps a des lignes de case en double (ce que le gabarit de plan devrait empêcher, mais défends-toi quand même). S'arrêter et faire remonter un avertissement. Demander à l'utilisateur de désambiguïser avant de continuer.

### 4. Pousser

```bash
gh issue edit <issue-plan> --body-file /tmp/qa-plan-<N>.fresh.md
```

Après un push réussi, mettre à jour ta copie de travail en mémoire à partir du corps frais pour que le prochain lot de patches parte du nouvel état.

### 5. Cadence

Pousser à la fin d'une phase ou d'un bloc par issue (ou à la fin d'un sous-groupe significatif au sein d'un bloc long). Ne pas pousser après chaque bascule de case — cela gonfle l'historique de l'issue et augmente la surface de risque d'édition concurrente.

Pour un bloc de longue durée, pousser périodiquement de toute façon (toutes les ~5-10 minutes d'activité), afin que si la session est interrompue, la progression de l'utilisateur soit reflétée sur l'issue.

## Mode de repli markdown

Si le plan de QA est un fichier `docs/qa/qa-plan-*.md` (pas de `gh` disponible, ou pas de remote GitHub) :

- Lire le fichier avec `Read` avant chaque lot de patches.
- Utiliser l'outil `Edit` avec la même règle de correspondance exacte de ligne.
- Pas besoin de la danse re-récupération / édition concurrente — le fichier est local.
- Suggérer à l'utilisateur de committer le fichier périodiquement pour que la progression soit durable.

## Ce que cela ne fait PAS

- Cela ne verrouille pas l'issue. GitHub n'expose pas de primitive de verrou sur les corps d'issue.
- Cela ne vérifie pas la version via ETag. `gh issue edit` n'en expose pas non plus.
- La détection est au mieux, basée sur la correspondance exacte de ligne. C'est suffisant pour le patron de concurrence réaliste (un utilisateur, un agent, retouches UI occasionnelles) et garde l'implémentation simple.
