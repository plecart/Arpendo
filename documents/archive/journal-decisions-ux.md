# Archive — journal des décisions de la spécification UX

> **Ce document n'est pas normatif.** Il conserve le raisonnement, les options écartées et
> l'historique des révisions retirés de `documents/reference/02-specification-ux.md`, pour que
> rien ne soit perdu. **La spécification ne porte que l'état courant** : un agent ou un
> développeur qui la lit ne doit pas avoir à distinguer une décision en vigueur d'une décision
> abandonnée.
>
> **En cas de contradiction, la spécification l'emporte, toujours.** Ce fichier est une trace,
> pas une source.

---
## 16. L'identité visuelle — ce qui a été intégré, ce qui reste ailleurs

**Statut : close.** Le questionnaire `brief-identite-visuelle.md` a été rempli le 13 août 2026,
trois directions ont été produites dans `03-identite-visuelle.md`, et la direction
**« Relevé »** a été retenue. Le point d'insertion prévu a fonctionné comme prévu : la **couche
sémantique du §1.5** a absorbé le changement sans qu'aucun composant soit retouché.

**Intégré dans ce document :**

| § | Ce qui y est entré |
|---|---|
| §1.2 | Roboto confirmée définitive, graisse par défaut, chiffres tabulaires, interlettrage |
| §1.5 | Les onze jetons de chrome, **en clair et en sombre**, avec leurs contrastes mesurés |
| §1.6 | Deux courbes au lieu d'une, `motion-press`, `motion-stagger`, le principe d'entrée |
| §3.1 | Note de revalidation de la palette sur la nouvelle `surface-dim` |
| §3.3 | Remplissage radial depuis le point de contact du marqueur |
| §3.4.1 | La spécification complète du modèle glTF |
| §4 | Le signe, le logotype et la hiérarchie de la marque à l'écran |
| §7.4 | Transition d'élément partagé sur le tap joueur, cascade de liste |

**Resté dans `03-identite-visuelle.md`**, et qui n'a pas sa place ici : le raisonnement, les
deux directions écartées et leurs coûts, les calculs de séparation ΔE, les sorties du validateur,
les ressources SVG (signe, logotype, icône d'app, vue de face du marqueur), et le ton d'écriture.

**Deux contraintes issues de l'identité, à ne pas rouvrir :**

1. **`accent` ne peut pas être clair.** Les dix couleurs joueur occupent toute la roue chromatique
   entre L 0,470 et 0,761 : **aucune teinte au-dessus de L 0,40 n'est à ΔE ≥ 15 des dix.** Tout
   accent de mode clair est donc sombre, et tout accent de mode sombre est pâle. Ce n'est pas un
   goût, c'est le résultat d'un balayage complet de l'espace OKLCH.
2. **La palette joueur (§3.1) ne fait pas partie de l'identité de marque** et n'a pas été
   retouchée. Elle est contrainte par l'accessibilité et validée. Toute modification future doit
   repasser le validateur en mode `--pairs all` **et** revérifier la séparation de l'accent.

**Ce que l'identité n'a pas tranché** : le réglage fin du style Mapbox (la contrainte de ΔE 15 du
fond de carte, §3.2, se vérifie sur le style réel), le dessin des cinq motifs `pattern_id` du
post-MVP (§15.3), et les accessoires du marqueur — seul le nœud d'ancrage est spécifié (§3.4.1).

---

## 17. Décisions du cadrage à revoir

Trois points, **tous arbitrés et répercutés le 12 août 2026** dans `01-cadrage.md` et son
journal des changements (§18.2). Cette section conserve le raisonnement, pour qu'il ne soit pas
rouvert sans élément nouveau.

### 17.1 — `POST_NOTIFICATIONS` absent du modèle de permissions — **validé le 12 août 2026**

**§ concernés :** 9.1, 9.2, 9.3, 10.3, 14.2. **Cas 3** : rend une autre décision du cadrage
impossible à afficher.

Le §9.3 décrit un modèle à trois niveaux et le §9.3 parle de « **trois autorisations distinctes** à
obtenir dans l'onboarding ». Depuis Android 13, poster une notification exige une permission
d'exécution ; refusée, la notification du service de premier plan **n'est pas affichée** — le
service tourne, son interface disparaît. Or le §10.3 fonde tout son dispositif d'alerte sur elle :
« La notification permanente devient le canal d'alerte », pour le cas que le même § qualifie de
**dominant**. Les trois notifications push du §14.2 tombent avec.

**Décision retenue :** un **quatrième niveau non bloquant** dans le modèle unique de §9.3, spécifié
en §12.1 de ce document. Coût : une ligne de tableau, une entrée de bandeau, un état de pastille —
tous les composants existent déjà. Contrepartie assumée : l'onboarding passe de trois à quatre
autorisations, ce que §9.3 signale déjà comme une charge. La séquence du §12.3 étale les demandes
pour ne pas aggraver le taux de refus.

**Répercussion faite dans `01-cadrage.md`** (§9.1, §9.2, §9.3, §10.3, §14.2 et journal §18).

### 17.2 — §5.2 : « passer à 50 joueurs sans migration ni changement de rendu » — **validé le 12 août 2026**

**Cas 1** : infaisable tel que décrit. *Source : spécification de style Mapbox. Les skills
`mapbox-flutter-patterns` et `mapbox-android-patterns` ne couvrent pas ce point — je le signale
plutôt que de laisser croire à une vérification que je n'ai pas faite.*

Le §5.2 écrit : « Le moteur de rendu lit **déjà les deux champs**. Passer à 50 joueurs = débloquer
des valeurs, **sans migration ni changement de rendu**. »

Un `FillLayer` colore par `fill-color`. Les motifs passent par `fill-pattern`, qui référence une
image du sprite et **ignore `fill-color`**. Conséquences :

- au MVP, avec un seul calque en `fill-color`, **`pattern_id` n'est lu par rien** ;
- atteindre 50 identités demande soit 50 images (la couleur dupliquée dans les ressources, contraire
  à DRY), soit **un second calque de motif** (§15.3) — ce qui est bien un changement de rendu.

**Ce que ça casse à l'écran :** rien aujourd'hui. Le risque est différé : la phrase donne
l'impression qu'aucun travail de rendu ne reste, et le jour où l'on voudra 50 joueurs, la surprise
sera un calque à ajouter et 5 images à dessiner — pas une catastrophe, mais pas « zéro » non plus.

**Remplacement proposé :** reformuler en « sans migration de données ; le rendu ajoute un calque de
motif, dont la recette est écrite d'avance ». Coût aujourd'hui : zéro. La recette est en §15.3.

**Ce que le cadrage perdrait :** rien sur le fond. La décision produit — deux dimensions découplées,
`color_id` et `pattern_id`, 10 × 5 = 50 identités — est bonne et confirmée par les mesures du §3.1,
qui montrent qu'aucune palette de 10 couleurs ne peut être lisible en niveaux de gris. Seule la
promesse « zéro changement de rendu » est trop forte.

**Répercussion faite dans `01-cadrage.md`** (§5.2 et journal §18.2).

### 17.3 — §4.3 : retour visuel du plafond de 50 km/h — **validé le 12 août 2026**

**Cas 4** : crée une situation que le joueur ne peut pas comprendre — exactement le raisonnement qui
a justifié le compte à rebours du verrou de vol au §4.2.

Le §4.3 pose : « Au-delà, la position est **reçue mais ne capture rien**. Le joueur n'est ni bloqué,
ni déconnecté. » Rien n'est prévu pour le lui dire. Le §4.2 justifie pourtant son propre compte à
rebours par : « sans lui, marcher sur une tuile adverse sans rien obtenir passera pour un bug ». La
même phrase s'applique mot pour mot à un joueur qui traverse des hexagones sans en prendre aucun.

**Ajout proposé au §4.3 :** « Le client affiche un retour explicite pendant le dépassement —
« Trop rapide — capture en pause » — via le composant de bandeau unique. Le calcul reste
exclusivement côté serveur ; le client reçoit un drapeau et se contente de l'afficher. »

**Coût :** un booléen dans la réponse serveur aux lots de positions. Aucun calcul déplacé côté
client, donc aucune ouverture anti-triche (§12.5).

**Ce que le cadrage perdrait :** rien. L'intention du §4.3 est explicitement de « ne pas policer les
modes de déplacement » ; un message qui explique sans bloquer sert cette intention plutôt qu'il ne
la contredit. Le seul risque est qu'un cycliste en descente voie brièvement le message — il en
comprendra la raison, ce qui vaut mieux que de ne rien comprendre.

**Répercussion faite dans `01-cadrage.md`** (§4.3 et journal §18.2). Le drapeau serveur
mentionné en §7.3 de ce document est donc acquis, et n'est plus un coût à signaler.

---

## 18. Journal des changements par rapport à l'inventaire

| Ancien inventaire | Cette spécification |
|---|---|
| Liste de composants sans états | Six états spécifiés par composant, y compris « sans objet » explicite |
| 6 boutons flottants + 3 indicateurs sur la carte | 2 contrôles permanents + 1 conditionnel (§7.0) |
| Compte à rebours du verrou flottant en permanence | Message réactif à deux lignes, partagé avec l'indicateur de vitesse (§7.3) |
| Trois panneaux séparés (Participants, Flux, Inviter) | Une feuille à **deux** onglets — le flux en est sorti le 13 août 2026 (§7.4) |
| Menu à deux boutons + deux feuilles (Créer, Rejoindre) | **Un seul écran Accueil** portant les deux blocs. Une page dense plutôt que trois pages minces (§5) — *13 août 2026* |
| Poignée de feuille repliée de 72 dp portant le classement | **Supprimée.** Un bouton d'action rond de 56 dp ouvre la feuille ; la carte gagne ~10 points de pourcentage, le classement passe à une tape (§7.4) — *13 août 2026* |
| Verrou de vol : « Vol impossible — encore 1:42 » | **Deux lignes qui expliquent** : « Cette tuile est à Alice. » / « Tu pourras la reprendre dans 1 min 12 s. » (§7.3) — *13 août 2026* |
| Paramètres sans donnée Google | **L'adresse du compte est affichée**, pour distinguer plusieurs comptes (§8) — *13 août 2026* |
| Deux modales d'entrée en partie, sécurité puis visibilité des zones | **Une seule, « Joue prudemment », une fois par compte.** La mention de visibilité quitte l'interface et devient une obligation portée par les CGU et la politique de confidentialité (§6.1) — *13 août 2026* |
| Modale Paramètres identique partout | **Contextuelle** : « Cette partie » (Quitter) en partie seulement, « Ce compte » (Déconnexion, Supprimer) au Menu seulement. Permissions dans les deux. Contrepartie obligatoire : lien web de suppression dans Informations (§8) — *13 août 2026* |
| Code de partie dans l'en-tête de la feuille **et** dans l'onglet Inviter | **Onglet Inviter seul.** L'en-tête disparaît : +48 dp de contenu, nom porté par `Semantics` (§7.4) — *13 août 2026* |
| « Quitter la partie » au pied de la feuille Partie | **Bloc « Cette partie » de la modale Paramètres**, avec libellés de section délimitant les portées (§7.4, §8) — *13 août 2026* |
| Flux d'activité en troisième onglet de la feuille | **Pile d'activité permanente en bas gauche de la carte** — 4 entrées, dégradé d'opacité, `IgnorePointer` sauf la ligne du bas, modale au tap. La feuille passe à deux onglets. C'est aussi le châssis du futur chat (§7.2.1, §7.2.2) — *13 août 2026* |
| « Curseur de durée à 8 paliers », sans spécification | **Curseur conservé**, mais rendu conforme : zone tactile de 48 dp autour d'une poignée de 22, ligne de 48 dp, aimantation stricte sur les huit valeurs, tap sur le rail, crans dessinés et valeur affichée en clair (§5.1) — *13 août 2026* |
| « Pastilles colorées » pour les autres joueurs sur la carte | Aucun marqueur d'autre joueur ; les pastilles sont des éléments de liste (§3.4) |
| Palette « 10 couleurs » sans valeurs | 10 valeurs hex validées, rapport du validateur reproduit (§3.1) |
| Emplacement réservé pour le QR code | Supprimé — la garantie d'ajout indolore est architecturale, pas graphique (§7.4) |
| Notification permanente : une ligne | Chapitre complet, avec le cas de la permission refusée (§10) |
| Score vivant : citation de l'exigence | Quatre décisions de rendu (§7.1) |
| 10 points « à trancher en phase design » | 10 tranchés + le trou du 50 km/h (§14) |
| Tableau des scores : « écran ou modale ? » | Feuille par-dessus le Menu, cohérent avec §8.3 (§9) |

## 18.1 Passe de cohérence du 23 août 2026

Issue d'un audit du document contre lui-même. **Aucune décision produit n'est rouverte** : ce sont
des contradictions internes, des trous, et trois points de conception que l'audit a fait remonter.

**Corrections — le document se contredisait :**

| Où | Ce qui était faux | Ce qui est écrit maintenant |
|---|---|---|
| §2.4 | La condition de priorité 6 était un **sous-ensemble** de celle de priorité 5 : sous une priorité stricte, **la ligne 6 ne pouvait jamais s'afficher** — avec elle le seul « Réessayer » de coupure longue | Les conditions portent leur borne de durée et sont mutuellement exclusives, plus une vérification opposable pour toute entrée future |
| §5 / §5.1 / §5.2 | Le § parent disait les deux actions **actives** hors ligne, ses deux sous-sections les disaient **désactivées** | Actives, avec échec explicite au tap et saisie conservée. C'est la règle du § parent, celle qui portait l'argument |
| §7.1 | Le budget carte du repli deux lignes était resté à 65-71 % → 61-67 %, chiffres d'avant la suppression de la poignée de 72 dp | 74-80 % → **70-76 %**, la valeur que le §2.2 annonce déjà |
| §7.1 | *« 2 j 04 h »* était rangé dans la tranche « 2 h à 48 h » alors qu'il vaut plus de 48 h — et c'est l'exemple retenu à quatre endroits du document | Une tranche **« 48 h à 7 j » en jours + heures** est ajoutée ; les exemples avaient raison |
| §8 vs §1.4, §7.4 | « Cette partie » était placé **en premier**, alors que §7.4 justifie son déplacement par « en fin de liste défilante » | Le bloc passe **en dernier**, à la même position que « Ce compte » |
| §13.2 | « Aucun indicateur avant 600 ms » contredisait ses trois applications, qui passent un bouton en indicateur au tap | La règle ne vaut que pour l'**attente subie** ; l'attente provoquée n'a aucun délai |
| §1.6 | `motion-base` donnait une durée unique alors que le § impose « la sortie dure 75 % de l'entrée » | **240 ms entrée / 180 ms sortie** |
| §1.2, §1.7 | Le code de partie s'affichait à 40 dp avec le `letterSpacing: 4` d'un jeton défini à 20 dp | Jeton `type-mono-display` distinct, et interlettrage exprimé en **`em`** |

**Ajouts — le document ne disait rien :**

| Où | Ce qui manquait |
|---|---|
| §1.5 | Pas de jeton `success`, et le vert utilisé en dur (`#007559`) **était la couleur joueur n° 5**. Résolu **sans créer de jeton** : état positif porté par le glyphe, `accent` là où une couleur est nécessaire, pastille de delta neutre dans les deux sens |
| §1.5 | Les sévérités `info` et `bloquant` n'avaient aucun rendu, alors que §2.4 fait porter la sévérité par le glyphe | Table de correspondance sévérité → glyphe → couleur, sur les jetons existants |
| §1.8 *(nouveau)* | **Aucune icône n'était définie nulle part.** Jeu retenu, règles d'emploi, inventaire des 16 usages |
| §5 | Le comportement au clavier de l'Accueil, devenu un écran de fond portant un champ de saisie |
| §5.3 | La course la plus fréquente — **ma** couleur prise, les autres libres — seul le cas « partie pleine » était traité |
| §7.2.2 | Les neuf types de journal étaient **tous à la troisième personne** : rien ne permettait de retrouver *qui* avait fait baisser son score. Deux types ajoutés |
| §7.4 | Le texte du message de partage, seul vecteur d'acquisition au MVP |
| §7.2.1 | La pile restait-elle annoncée au lecteur d'écran malgré `IgnorePointer` ? |

**Conception — trois points rouverts, et un quatrième refermé :**

| Point | Décision |
|---|---|
| **Le header** | L'arithmétique de largeur n'avait jamais été faite : ≈ 348 dp pour 360, **12 dp de marge**. La pastille de delta devient une **surimpression** qui ne consomme aucune largeur, et le seuil de repli descend de **1,3 à 1,1** |
| **La pile d'activité** | Le motif « châssis du futur chat » est **retiré** — c'est l'anticipation que le document refuse deux fois ailleurs. La comptabilité de surface est refaite honnêtement : la pile reprend un peu plus que la bande de 72 dp n'avait libéré, et deux limites concrètes font accepter l'échange |
| **Le contraste** | Tous les ratios valaient sur fond opaque, alors que le header (92 %) et les plaques (88 %) étaient translucides au-dessus d'aplats saturés. **Les surfaces portant du texte au-dessus de la carte deviennent opaques, le flou disparaît** — ce qui supprime au passage un coût de rendu permanent au-dessus de Mapbox |
| **La carte en mode sombre** | La carte suivait le mode clair dans les deux thèmes. `lightPreset: night` s'obtient par le canal de configuration déjà utilisé pour les libellés : la carte suit désormais le mode. Le rapport du §3.1 est à rejouer sur le fond sombre |

**Trois points examinés et laissés en l'état, volontairement :**

- **La fraîcheur de capture dans la liste des joueurs.** Une tuile fait ~65 m de côté ; le porteur
  juge que l'imprécision suffit et que la position d'un joueur n'en est pas déduite.
- **Le curseur de durée du §5.1.** Conservé tel quel, sans étape de confirmation supplémentaire.
- **L'opacité de 60 % hors ligne (§3.3).** Elle efface quatre couleurs joueur sur dix ; c'est
  **l'effet recherché** — l'inconfort doit être perçu et pousser à se reconnecter.
