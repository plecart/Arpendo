# Glossaire de domaine

Le vocabulaire d'Arpendo, **extrait** de `documents/reference/` — aucun terme n'a été inventé ici,
aucune définition n'y est décidée. Chaque entrée cite le **§ qui fait foi** : c'est lui la source,
ce fichier n'en est que l'index. Une entrée en cite plusieurs quand sa définition en agrège
plusieurs, et donne entre parenthèses l'identifiant technique quand le § en fixe un. Les § cités
renvoient à `documents/reference/01-cadrage.md` (noté **C**) et à
`documents/reference/02-specification-ux.md` (noté **UX**).

**À employer tel quel** dans les noms de tests et de modules, et dans les titres d'issues et de PR.
Un synonyme listé comme interdit n'est pas un détail de style : deux mots pour un concept, et la
moitié du code parle d'autre chose que l'autre moitié. Les interdictions valent **dans la portée
que chaque entrée leur donne** — plusieurs de ces mots sont justes ailleurs, et l'entrée le dit.

**Les identifiants techniques ne sont pas concernés.** Les noms de tables, de colonnes et de
champs sont fixés en anglais par le cadrage (`player_game`, `steal_cooldown_seconds`,
`position_batch`, `color_id`…) ; le glossaire nomme les concepts, pas le schéma.

**Quand un terme manque** — le glossaire est muet, ce n'est pas un vide à combler au jugé : le
terme se cherche d'abord dans `documents/reference/`, puis, s'il n'y est pas non plus, il se
tranche avec le porteur avant d'entrer dans le code. Voir `.claude/rules/decisions-vs-doc.md`.

---

| Terme | Définition | § qui fait foi | Synonymes interdits |
|---|---|---|---|
| **Bandeau** | Composant unique et paramétré qui porte tout message d'état persistant — permissions, réseau, action sans effet, mise à jour — un seul affiché à la fois. | UX §2.4 | « toast » ; ne pas dire « snackbar » ni « alerte » pour le bandeau — le `SnackBar` de UX §7.4 est un autre composant, et l'alerte est celle du monitoring (C §16) et du canal de la notification permanente (C §10.3) |
| **Bilan périodique** | Entrée de flux qui agrège la progression de chaque joueur sur la période écoulée, à une fréquence fixée par la durée de la partie. | C §11.3, C §11.5 | « résumé », « digest », « récap » |
| **Capture** | Prise instantanée d'une tuile par le joueur qui marche dessus, appliquée à chaque position reçue si la tuile est capturable. | C §4.1, C §10.1 | « claim », « coloriage » |
| **Cellule parente** | Cellule H3 de résolution inférieure ; chaque tuile en stocke **deux** en colonnes dénormalisées (ex. résolutions 7 et 5), qui servent à agréger l'affichage au dézoom et à requêter par viewport. | C §7.1, C §13.6 | « agrégat », « cluster », « macro-hexagone » |
| **Classement** | Ordre des participations d'une partie par score décroissant ; il n'a de sens que sur une partie terminée par le timer, jamais sur une partie abandonnée. | C §4.5, UX §9 | « leaderboard », « podium » (le podium est les 3 premiers du classement, pas le classement) |
| **Code de partie** | Code court à 6 caractères, sans caractère ambigu, qui permet de rejoindre une partie et qui expire avec elle. | C §6, UX §1.7 | « code d'invitation », « code de salon », « token » |
| **Couleur** | Identité visuelle d'une participation, découplée en deux champs — `color_id` parmi les 10 couleurs de la palette, et `pattern_id`, toujours « plein » au MVP. | C §5.2, UX §3.1 | « skin », « avatar » ; ne pas dire « teinte » pour `color_id` — le mot reste valide en colorimétrie, où les documents l'emploient (C §5.2) |
| **Départ définitif** | Sortie irréversible d'une partie : les tuiles du joueur sont neutralisées, il est retiré du classement et ne récupère rien s'il rejoint à nouveau. | C §4.4 | « abandon » (réservé à la partie, C §4.5), « quitter le jeu », « déconnexion » |
| **Fenêtre hors ligne** | Tolérance de 5 minutes, mesurée côté serveur, pendant laquelle les captures d'un client sans réseau restent valides ; au-delà, la file locale est purgée. | C §10 | « timeout », « période de grâce », « buffer » |
| **Feuille « Partie »** | Panneau glissant de l'écran Jeu à **deux onglets** — « Joueurs » et « Inviter » — plus une icône ouvrant la modale Paramètres ; ni le flux d'activité ni le départ définitif n'y vivent. | UX §7.4 | « modale Partie » (c'est un panneau, pas une modale), « drawer », « panneau Joueurs » (c'est un de ses deux onglets) |
| **Flux d'activité** | Journal d'événements de la partie, généré côté serveur, identique pour tous, agrégé et sans aucune mention de lieu. | C §11 | « fil », « feed », « timeline », « chat » |
| **Instantané de fin** | Ligne de résultats figée écrite à la clôture d'une partie — pseudo, couleur, points, nombre de tuiles — jamais recalculée depuis les tables de jeu. | C §8.4 | « historique » (l'historique liste les instantanés) ; ne pas dire « snapshot » ni « archive » pour un instantané — le premier nomme la sauvegarde de VM (C §13.7), le second un répertoire du dépôt |
| **Journal d'événements de domaine** | Journal structuré des événements métier, source unique dont dérivent le flux d'activité et le futur back-office. | C §12.6, C §11.5 | « event log », « audit trail », « logs » |
| **Lot de positions** | Groupe de positions GPS envoyé en un seul POST idempotent, porteur d'un identifiant de lot que le serveur déduplique. | C §13.0, C §13.9, C §12.3 (`position_batch`) | « ping », « paquet GPS » ; ne pas dire « trace » pour un lot — « traces GPS brutes » nomme la donnée transportée, pas son enveloppe (C §12.3) |
| **Neutralisation** | Passage des tuiles d'un joueur parti à l'état libre, exécuté par lots en tâche de fond et diffusé progressivement aux autres joueurs. | C §4.4 | « suppression », « effacement » (les tuiles ne disparaissent pas), « reset » |
| **Notification permanente** | Notification Android non balayable du service de capture en arrière-plan, qui sert aussi de canal d'alerte quand l'app est fermée. | C §9.1, C §10.3, UX §10 | « notification persistante », « foreground notification », « notification de service » |
| **Participation** | Lien entre un joueur et une partie (`player_game`), qui porte son statut, sa couleur et son horodatage de dernier vol. | C §4.2, C §4.4, UX §3.1 | « membership », « membre » ; ne pas dire « inscription » pour une participation — l'inscription est la création du compte (UX §4) |
| **Partie** | Instance de jeu créée par un joueur, de durée choisie entre 30 minutes et un mois, limitée à 10 joueurs, et dont un joueur ne peut avoir qu'une active à la fois. | C §4.1, C §4.2, C §8, UX §5.1 | « room », « salon » ; ne pas dire « match » ni « session » pour une partie — `['match', …]` est l'expression Mapbox (UX §3.3), et la session est celle de l'authentification (UX §2.1, C §12.1) |
| **Pile d'activité** | Surcouche de carte en bas à gauche de l'écran Jeu, qui affiche les 4 dernières entrées du flux avec un dégradé d'opacité ; surface d'affichage, pas un contrôle. | UX §7.2.1 | « liste d'activité », « toasts », « overlay de flux » |
| **Plafond de vitesse** | Seuil de 50 km/h calculé côté serveur en moyenne glissante sur 3 positions, au-dessus duquel les positions sont reçues mais ne capturent rien. | C §4.3 | « speed cap », « anti-triche vitesse », « limite de vitesse » (vocabulaire du régime remplacé, C §18.1) |
| **Score** | 100 × le nombre de tuiles possédées à l'instant T — une valeur vivante, qui baisse quand les tuiles sont volées. | C §4.1 | « XP », « nombre de tuiles » (colonne distincte de l'instantané, C §8.4) |
| **Tuile** | Hexagone H3 de résolution 10 (~130 m de large), unité atomique de territoire, neutre ou attribuée à un propriétaire unique. **Terme préféré** dans le code, les tests, les issues et les PR ; « hexagone » désigne le même objet et reste employé par les documents, notamment pour la couche de rendu. | C §4.1, C §7.2, UX §3.3 | « case », « cellule » (réservé à H3 : cellule parente), « zone », « territoire » (le territoire est l'ensemble des tuiles d'un joueur, C §11.2) |
| **Verrou de vol** | Recharge par joueur — et non par tuile — qui n'autorise qu'un vol par période, figée à la création de la partie (`steal_cooldown_seconds`). | C §4.2 | « verrou de tuile » (mécanisme remplacé, C §4.2), « cooldown » en prose française |
| **Vol** | Capture d'une tuile déjà possédée par un autre joueur, toujours possible quelle que soit sa présence, et soumise au verrou de vol. | C §4.2 | « attaque » ; ne pas écrire « capture » quand on veut dire « vol » — le vol est un **cas particulier** de la capture (C §4.1), pas son contraire |
