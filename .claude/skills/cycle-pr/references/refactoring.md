# Candidats au refactor

Après un cycle TDD, chercher :

- **Duplication** → extraire une fonction / classe
- **Méthodes longues** → découper en helpers privés (garder les tests sur l'interface publique)
- **Modules superficiels** → combiner ou approfondir
- **Feature envy** → déplacer la logique là où vivent les données
- **Obsession des primitifs** → introduire des value objects
- **Code existant** que le nouveau code révèle comme problématique
