# Standard de correction de bug

Utiliser ceci quand l'utilisateur a explicitement choisi l'option (c) « corriger en session » lors d'un échec de QA. Le flux par défaut est l'option (a) « déposer le bug via bug-vers-issue et continuer ». Ne pas se lancer dans des corrections en session par défaut.

## Standard minimal

1. Reproduire le chemin en échec avec la plus petite commande / séquence UI.
2. Classifier la sévérité (bloquante / majeure / mineure) et la phase / le bloc où elle se situe.
3. Lire la plus petite surface de code pertinente : la route, le composant, le worker, la migration qui détient l'invariant.
4. Trouver la cause racine. Ne pas s'arrêter au symptôme.
5. Ajouter ou mettre à jour un test ciblé qui échouerait avant la correction quand c'est faisable.
6. Implémenter la plus petite correction architecturale propre — épouser la forme du module existant et la propriété.
7. Exécuter les tests ciblés pour la correction.
8. Exécuter les garde-fous pertinents — commandes `lint`, `typecheck`, `build` de
   `.claude/pipeline.config.md`, en ignorant celles marquées `n/a`.
9. Ré-exécuter l'action de QA exacte en échec. Confirmer le passage.
10. Basculer la case du plan de QA et ajouter `— corrigé en session, <sha-commit>, <date>`.

## Inacceptable

- Traiter en cas particulier seulement la fixture observée alors que le bug est général.
- Cacher des échecs backend dans le frontend.
- Avaler les exceptions du worker sans persister une erreur de job.
- Changer le comportement de l'API sans tests.
- Corriger l'affichage frontend alors que l'état backend reste faux.
- Démarrer une phase / un bloc dépendant alors qu'un constat amont bloquant n'est pas résolu.

## Signaux d'une bonne correction

- La correction vit là où l'invariant appartient (modèle, validateur, gateway — pas le contrôleur en après-coup).
- Les tests couvrent la classe de régression, pas seulement la fixture exacte.
- Le comportement public existant est préservé sauf pour le bug.
- Les erreurs restent exploitables pour les utilisateurs / opérateurs (pas d'avalement).
- Les logs et l'état BD restent cohérents avec la réponse de l'API.

## Quand s'arrêter et déposer à la place

Arrêter la correction en session et revenir à `bug-vers-issue` si l'un de ces cas :

- La correction touche plus d'un module architectural.
- La correction nécessite une décision produit / de politique que l'utilisateur ne peut pas prendre en 30 secondes.
- La correction nécessiterait une migration sur un état partagé / proche de la production.
- La correction ferait déborder la campagne de QA au-delà d'une borne raisonnable.

Dans ce cas, NE PAS laisser traîner des changements partiels en session. Soit les committer sur une branche de feature que l'utilisateur nomme, soit les annuler. Puis déposer via `bug-vers-issue` et continuer la QA.
