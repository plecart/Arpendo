# Taxonomie de couverture

Feuille d'indices pour `plan-qa`. **N'en tirer que les sections correspondant aux surfaces que le
projet possède réellement** — ne jamais coller la taxonomie entière dans un plan.

> **Filtre préalable, appliqué à chaque ligne ci-dessous** : un test automatisé pourrait-il attraper
> ça ? Si oui, la ligne ne va pas dans le plan de QA — elle va dans la suite de tests, via une issue
> pour `cycle-pr`. Ce qui suit ne liste que des vérifications qu'une machine ne fait pas à notre
> place : comportement observé en environnement réel, perception utilisateur, effets de bord.

## Démarrage réel

*(toujours pertinent — c'est ce que la CI ne prouve pas)*

- Les fichiers d'environnement requis existent et correspondent à l'exemple versionné.
- L'application démarre avec la configuration locale réelle, pas seulement en conteneur de CI.
- Les services dont elle dépend montent ensemble et se joignent entre eux.
- Chaque surface exposée répond à son point d'entrée.
- La configuration façon production refuse les valeurs par défaut non sûres (debug actif, secrets
  par défaut, cookies non signés).

## Sécurité & Propriété

*(si le projet a de l'authentification et des ressources rattachées à un utilisateur)*

- Authentification absente, invalide ou expirée → refus, et session vidée côté client.
- Le compte A ne voit que ses propres ressources sur chaque point de listing.
- Le compte B ne peut ni lister, ni lire, ni modifier, ni exporter, ni télécharger celles du compte A.
- Ressources absentes et ressources d'autrui suivent la même convention anti-énumération.
- Le client ne persiste que du contexte sûr ; les sélections périmées sont réconciliées après
  rechargement ou changement de contexte.

## Entrées et fichiers

*(si le projet accepte des fichiers ou des entrées externes)*

- Formats valides acceptés ; contenu réel ne correspondant pas à l'extension rejeté **avant** tout
  stockage.
- Entrées vides, trop volumineuses, ou de format hérité : échec contrôlé et message exploitable.
- La politique des cas ambigus (sans extension, encodage inattendu) est testée et consignée.
- Les originaux sont préservés et récupérables quand ils sont exposés.
- Une entrée rejetée ne laisse **ni enregistrement ni artefact** exploitable.
- Les tentatives répétées sont idempotentes ou explicitement reprises.

## États d'interface

*(si le projet a une interface)*

Pour chaque surface qui affiche des données, les cinq états :

- vide, chargement (contrôles neutralisés), succès, erreur, échec terminal.

Plus :

- Le détail de l'erreur réelle est visible, non remplacé par un message générique.
- Le rechargement ne préserve que le contexte voulu.
- Les liens et téléchargements fonctionnent avec le modèle d'authentification réel.
- Aucune attente ne se poursuit après un état terminal.
- Console et réseau sans erreur inexpliquée.

## Intégrité des données

*(si le projet persiste quelque chose)*

- Les rattachements de propriété pointent vers le bon périmètre.
- Les enregistrements créés portent les statuts et horodatages attendus.
- Les données dérivées conservent le lien vers leur source.
- Un traitement échoué conserve une erreur claire et ne laisse pas d'état « en cours » périmé.
- Les règles de doublon et de reprise sont vérifiées sur cas réel.

## Traitements asynchrones

*(si le projet a des jobs, files ou workers)*

- Une exception ne fait pas tomber la boucle de traitement.
- Les erreurs externes produisent une trace persistée, pas un échec silencieux.
- Une réponse amont vide, nulle ou malformée échoue clairement.
- Les reprises sont bornées et observables.

## Workflow métier

*(toujours pertinent dès qu'il y a un domaine)*

- Les objets du domaine sont persistés structurellement, pas comme des blobs opaques.
- Les garde-fous sont appliqués côté serveur ; le client ne fait que refléter le blocage.
- Les décisions utilisateur requises sont explicites et auditables.
- Les exports proviennent de l'état persisté, jamais d'une régénération à la volée.

## Régression manuelle

*(toujours — la non-régression automatisée appartient à la CI)*

- Le plan nomme les parcours manuels minimaux à rejouer après correction.
- Les avertissements connus sont séparés des blocages réels.
- Les cas de référence évitent les comparaisons fragiles de longs textes.
- Le plan consigne l'échec original **et** la vérification après correction, via l'issue de bug liée.
