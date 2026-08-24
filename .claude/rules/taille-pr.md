# Règle — Taille et format des PR

## Découpage
- **Une PR = une unité de travail cohérente et reviewable.**
- Au-delà de **~10 fichiers** ou **~500 lignes de diff**, découper la PR.

## Format des messages
- **Commits et titre de PR** au format conventional commit : `type(scope): description`.
  - Types : `feat` `fix` `chore` `docs` `refactor`.
  - **Préfixe en anglais, description en français.** Ex : `feat(auth): ajoute la connexion par e-mail`.
  - Breaking change : `!` dans le titre (`feat!: …`), pas de footer.
- Message de commit = **titre seul**. Pas de corps, pas de footer, pas de `Co-Authored-By`,
  pas de préfixe de phase ni de numéro de PR (traçables via l'outil de suivi).

## Branches
- Trunk-based depuis `main` : `git checkout -b <type>/<description>`.
