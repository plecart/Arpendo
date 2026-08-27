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

---

## 18.2 Amendement du §1.8 du 26 août 2026 — le paquet d'icônes

Découvert en implémentant #34 (thème Dart des jetons), pas par un audit. **Aucune décision de
conception n'est rouverte** : le jeu reste Phosphor, la graisse reste `Regular`, l'inventaire des
15 usages est inchangé. Seul le *véhicule* change.

**Ce qui était faux, et pourquoi personne ne l'avait vu :**

| Ce qui était écrit | Ce qui est vrai |
|---|---|
| Le paquet est `phosphor_flutter` | `phosphor_flutter` 2.1.0 (mai 2024) **ne compile pas** avec Flutter 3.47 : `IconData` est passé `final class` en 3.43+, et le paquet fait `class PhosphorIconData extends IconData`. Le build échoue à `kernel_snapshot` |
| « tree-shaké à la compilation comme n'importe quelle police d'icônes » | La graisse employée l'est bien (488 636 → 1 620 octets). Les **cinq autres graisses** déclarées par le paquet ne le sont pas : **2,58 Mo** dans l'AAB, mesurés |

**Le piège de détection, qui vaut pour la suite.** `just lint`, `just test` et `just build` sont
tous passés au **vert** avec la dépendance cassée. `flutter analyze` n'analyse pas les sources d'un
paquet tiers, et le compilateur ne compile pas une bibliothèque qu'aucun chemin depuis `main()`
n'atteint : `icones.dart` n'était importé de nulle part. La casse serait sortie au premier écran
qui pose une icône (#43, #46). **Une table de constantes qui n'est référencée nulle part n'est pas
compilée** — d'où la garde ajoutée dans #34 : un test rend une icône de la table, ce qui suffit à
la rendre atteignable et à faire rougir la suite.

**Options examinées :**

| Option | Retenue ? |
|---|---|
| `phosphor_icons` ^3.0.1 (16 juillet 2026, MIT, seule dépendance `flutter`) | **Oui.** Successeur maintenu, qui documente et corrige explicitement cette rupture (`typedef PhosphorIconData = IconData`). Mêmes noms de classe et de membres — la migration est une ligne d'import. Les 15 glyphes du §1.8 y sont tous. Vérifié : build vert, tree-shaking effectif |
| `forui_phosphor` 0.26.1 | Non. Couplé au système de design *forui*, et porte encore une sous-classe d'`IconData` pour le duotone |
| Embarquer le sous-ensemble Phosphor tout de suite | Non — **repoussé, pas écarté**. C'est le point 7 du README, dont la motivation devient la mesure de 2,58 Mo au lieu de l'abandon supposé du paquet |
| Revenir aux `Icons.*` de Flutter | Non. Rouvrirait la décision de trait du §1.8, close, sans nécessité |

**§§ répercutés :** `02-specification-ux.md` §1.8 (nom du paquet, phrase de coût) ·
`README.md` « Ce qui reste ouvert » point 7. Le §1.8 n'est mentionné dans aucun document de rang 1,
donc aucune ligne au journal du cadrage. La ligne récapitulative « Jeu d'icônes | Phosphor
`Regular` » ne nommait aucun paquet et reste inchangée.

---

## 18.3 Amendement du §1.2 du 26 août 2026 — la phrase des graisses

Découvert en transcrivant l'échelle typographique dans le thème Dart (#34). **Aucune valeur ne
change** : le tableau du §1.2 fait autorité et n'est pas touché ; c'est la prose qui le décrivait
mal.

**Ce qui était faux :**

| Ce qui était écrit | Ce que dit le tableau du même § |
|---|---|
| « Graisse 400 par défaut, **réservée aux seuls** `type-display` et `type-title` pour monter à 700 et 600 » | **Quatre** jetons dépassent 400, pas deux : `type-headline` 600, `type-label` 500, `type-mono` et `type-mono-display` 500 |

**Pourquoi le tableau l'emporte, et pourquoi ce n'était pas un choix.** Le paragraphe fautif
s'ouvre sur « il ne touche pas à l'échelle ci-dessus, qui reste invariante » : il se subordonne
lui-même au tableau. La contradiction était donc interne et auto-résolue — le code de #34 a suivi
le tableau sans attendre l'amendement. Ce qui restait à corriger n'était pas une décision mais une
**phrase qui décrivait mal sa propre table**, et qu'un lecteur pressé aurait suivie à la place.

**Ce qui a été retenu :** reformuler la phrase pour qu'elle décrive le tableau, en conservant son
intention — le gras franc reste réservé aux deux plus gros jetons, la direction reste sobre.
L'option inverse (garder la phrase et ramener les quatre jetons à 400) aurait rouvert une décision
de conception close pour corriger une erreur de rédaction : disproportionné.

**§§ répercutés :** aucun. La phrase n'est citée nulle part ailleurs, et le tableau — seul objet
que la spec et le code partagent — est inchangé.

---

## 18.4 Amendement du §1.3 de l'identité du 27 août 2026 — la source des graisses

Suite directe du §18.3, découverte en fermant #60. **Aucune valeur ne change**, là non plus : le
tableau du §1.2 fait toujours autorité et n'est pas touché.

**Ce que le §18.3 avait manqué.** Il concluait « §§ répercutés : aucun. La phrase n'est citée nulle
part ailleurs ». C'était faux : la même affirmation vivait dans `03-identite-visuelle.md` §1.3,
sous la forme « graisse 400 partout sauf `type-display` et `type-title` ». Le §18.3 a donc amendé
le **miroir** (spec UX §1.2, rang 2) en laissant la **source** (identité §1.3, rang 3) affirmer
l'inverse pendant une journée.

C'est exactement le cas que `.claude/pipeline.config.md` décrit pour le rang 3 : « le § concerné
**et** son § miroir dans la spec UX — sinon les deux divergent ». La cascade avait été mesurée à
zéro alors qu'elle valait un, faute d'avoir cherché la phrase par son **sens** plutôt que par ses
mots : les deux formulations ne partagent aucune sous-chaîne commune.

**Ce qui a été retenu :** une seule et même formulation dans les deux §§, vérifiable contre le
tableau jeton par jeton — « graisse 400 par défaut, les autres jetons montant selon le tableau du
§1.2 sans dépasser 600 sauf `type-display` ». Elle est vraie des huit jetons (`display` 700 ;
`title` et `headline` 600 ; `label`, `mono` et `mono-display` 500 ; `body` et `caption` 400), là où
la rédaction du §18.3 laissait encore « 600 réservé aux deux plus gros » alors que `type-headline`
vaut 600.

**§§ répercutés :** `02-specification-ux.md` §1.2 et `03-identite-visuelle.md` §1.3, ensemble.
Rang 1 muet sur les graisses (le cadrage ne nomme que la famille Roboto), donc aucune ligne au
journal des changements du cadrage. Aucune issue ouverte ne cite ces phrases — recherche sur
« graisse », « type-headline », « type-label », « gras franc » : zéro. Le code n'est pas touché :
il a toujours suivi le tableau.

---

## 18.5 Passe de ton du 27 août 2026 — les textes de l'interface

Issue #29, PR #67. Le seul point de conception laissé ouvert par la phase d'identité (cadrage
§18.4, §19 point 4) : les textes de la spécification avaient été rédigés **avant** que le registre
soit arrêté (`03-identite-visuelle.md` §0.3 et §1.7), dans celui qui *annonce* la mauvaise nouvelle.
L'encadré qui portait la dette en tête du §0 est retiré ; un paragraphe **Ton** le remplace et
énonce la règle en vigueur.

**Ce qui a été appliqué, texte par texte.** Le registre du §1.7 de l'identité : phrases courtes,
verbes au présent, aucun point d'exclamation, aucune interjection, aucun superlatif, aucun emoji.
La mauvaise nouvelle dit **ce qui se passe** puis **ce qu'on peut faire** ; la bonne nouvelle reste
plate. Quatre règles de rédaction ont été fixées pour que le corpus soit cohérent — c'est le sens
du « tout ou rien » :

1. **Un cap de +30 % par texte**, mesuré en caractères et reporté dans la colonne Δ. C'est la
   tolérance que tout conteneur doit absorber (§0) ; une réécriture qui la consomme entièrement ne
   laisse rien à la locale allongée. Aucune ne la dépasse.
2. **Un vocabulaire commun.** La cause d'un échec se dit « Pas de réseau. » ou « Le serveur ne
   répond pas. » ; la conséquence d'une pause de capture, « tes pas ne comptent pas » ; un échec
   de chargement, « *X* n'est pas arrivé. » suivi de « Réessayer ». Un joueur qui a lu un message a
   lu les autres.
3. **Aucune forme genrée.** « Tu es seul dans la partie » et « Tu ne seras pas prévenu » supposent
   un joueur masculin ; l'app ne connaît pas le genre et les clés ARB de #38 figeront la forme.
   Les deux sont reformulés sans participe accordé.
4. **Les libellés d'action, les valeurs, les formats et les noms ne bougent pas** — ils n'ont pas
   de registre. Deux exceptions, pour interjection : « Oui, c'est mon pseudo » et « C'est bon, tu
   peux la reprendre ».

**Intouchés par consigne** : « Ta progression s'arrêtera si ton téléphone redémarre » (cadrage
§9.2), « aucune capture pour l'instant » (cadrage §7.5), « dernière capture il y a 2 h » (idem) et
l'avertissement de sécurité du §6.

**Quatre écarts relevés en passant, et ce qui en a été fait :**

| Écart | Traitement |
|---|---|
| L'encadré §0 affirmait que l'avertissement du §6 « reprend le cadrage §16 littéralement ». Le §16 du cadrage n'écrit aucun texte — il exige « avertissement de sécurité à l'onboarding + clause CGU » | Le texte reste intouché comme demandé ; la phrase du §6 devient « Le §16 du cadrage exige cet avertissement sans en écrire le texte ; il est arrêté ici » |
| La réécriture fixée par l'identité §1.7 pour la priorité 6 — « **Le réseau** ne répond plus. » — nomme une cause sur un bandeau qui vaut « quelle qu'en soit la cause », et recrée le piège que le cadrage §10.3 interdit : un serveur en panne lu comme une 4G défaillante, donc une app relancée et un service tué | Rang 1 l'emporte : « Coupure depuis plus de 5 min. Tes pas ne comptent pas pour l'instant. » — l'identité §1.7 est alignée |
| Le cadrage (rang 1) porte lui-même huit des textes à réécrire — §4.3, §4.4, §9.3, §10.1, §10.3 — alors que l'encadré n'en identifiait que deux comme « cités du cadrage ». L'encadré et l'identité prescrivent explicitement la réécriture de deux d'entre eux | **Arrêt `decisions-vs-doc`, question posée au porteur dans la PR #67.** Les neuf lignes marquées « en attente — Q1 » ci-dessous en dépendent |
| Le corps 1 de la modale de départ (§7.4), une fois réécrit, dit déjà « redeviennent libres » ; le corps 2 le répétait | Dépend du même arrêt |

**Inventaire.** 171 chaînes entre « » relues : 138 inchangées, 24 réécrites, 9 en attente.

| § | Avant | Après | Δ | Motif |
|---|---|---|---|---|
| §2.1 | « prends du terrain » | *inchangé* |  | accroche de l'identité (§1.5), pas un message |
| §2.1 | « Impossible de joindre le serveur. » | « Le serveur ne répond pas. » | -24 % | dit ce qui se passe ; « Réessayer » dit quoi faire |
| §2.1 | « Réessayer » | *inchangé* |  | libellé d'action |
| §2.4 p1 | « La localisation est nécessaire pour jouer. » | « Sans ta position, Arpendo ne sait pas où tu marches. » | +24 % | la règle devient sa conséquence pour le joueur ; même vocabulaire que l'amorce §12.3 |
| §2.4 p1 | « Réglages » | *inchangé* |  | libellé d'action |
| §2.4 p2 | « Android ne redemandera plus. Ouvre les réglages pour autoriser la localisation. » | *inchangé* |  | explique déjà : ce qui se passe, puis quoi faire |
| §2.4 p3 | « Tu es toujours dans la partie. Autorise la localisation pour reprendre la capture. » | *inchangé* |  | explique déjà |
| §2.4 p4 | « Serveur indisponible — capture en pause. Garde l'application ouverte, la reprise est automatique. » | **en attente — Q1** |  | cadrage §10.3 |
| §2.4 p5 | « Pas de connexion — capture en pause » | **en attente — Q1** |  | cadrage §10.3 |
| §2.4 p6 | « Capture en pause — tes déplacements ne comptent plus » | **en attente — Q1** |  | cadrage §10.1 |
| §2.4 p7 | « Trop rapide — capture en pause » | **en attente — Q1** |  | cadrage §4.3 |
| §2.4 p8 | « Cette tuile est à Alice. » | *inchangé* |  | explique déjà (cadrage §18.4) |
| §2.4 p8 | « Tu pourras la reprendre dans 1 min 12 s. » | *inchangé* |  | explique déjà ; le futur date un moment à venir (cadrage §18.4) |
| §2.4 p9 | « Connexion instable » | *inchangé* |  | constat court, rien n'est perdu, rien à faire (cadrage §10.1) |
| §2.4 p10 | « Ta progression s'arrêtera si ton téléphone redémarre » | *inchangé* |  | cité du cadrage §9.2 — garde-fou 1 |
| §2.4 p10 | « Masquer pour cette partie » | *inchangé* |  | libellé d'action |
| §2.4 p11 | « Tu ne seras pas prévenu si la capture s'arrête. » | **en attente — Q1** |  | cadrage §9.3 |
| §2.4 p12 | « Une nouvelle version est disponible. » | *inchangé* |  | information plate |
| §2.4 p12 | « Mettre à jour » | *inchangé* |  | libellé d'action |
| §2.4 p13 | « Hors ligne trop longtemps : 12 captures perdues. » | « La coupure a duré trop longtemps : 12 captures sont perdues. » | +25 % | cause puis conséquence, en phrase |
| §2.6 | « Annuler » | *inchangé* |  | libellé d'action |
| §4 | « Se connecter avec Google » | *inchangé* |  | libellé officiel Google |
| §4 | « Politique de confidentialité » | *inchangé* |  | libellé de lien |
| §4 | « CGU » | *inchangé* |  | libellé de lien |
| §4 | « Ce compte ne peut plus accéder au jeu. » | *inchangé* |  | constat, sans recours par décision (§12.6) |
| §4 | « Fermer » | *inchangé* |  | libellé d'action |
| §4.1 | « Choisis ton pseudo » | *inchangé* |  | titre |
| §4.1 | « Il sera visible par les autres joueurs. » | *inchangé* |  | information plate |
| §4.1 | « 7 / 16 » | *inchangé* |  | compteur |
| §4.1 | « Continuer » | *inchangé* |  | libellé d'action |
| §4.1 | « 3 à 16 caractères, lettres, chiffres, tiret et souligné. » | *inchangé* |  | aide de saisie |
| §4.1 | « Vérification… » | *inchangé* |  | état |
| §4.1 | « Caractère non autorisé : *é* » | « Pas de *é* dans un pseudo. » | -7 % | l'annonce devient une phrase |
| §4.1 | « Trop court : 3 caractères minimum. » | « Il faut au moins 3 caractères. » | -12 % | dit quoi faire |
| §4.1 | « Ce pseudo n'est pas autorisé. » | *inchangé* |  | sans détail par décision (le filtre ne se joue pas) |
| §4.1 | « *Alex* est déjà pris. » | *inchangé* |  | constat ; quoi faire est évident |
| §4.1 | « *Alex* est disponible. » | *inchangé* |  | bonne nouvelle factuelle — garde-fou 2 |
| §4.1 | « Vérification impossible. » | « Le serveur ne répond pas. » | +4 % | nomme la cause ; même phrase qu'au démarrage |
| §4.1 | « Ce pseudo sera définitif » | *inchangé* |  | titre |
| §4.1 | « Tu ne pourras plus jamais changer *Alex*. Vérifie l'orthographe. » | « Tu ne pourras plus changer *Alex*. Vérifie l'orthographe. » | -11 % | « jamais » dramatise ; la perte se constate |
| §4.1 | « Oui, c'est mon pseudo » | « Garder ce pseudo » | -24 % | interjection retirée ; l'action nomme ce qu'elle fait |
| §4.1 | « Modifier » | *inchangé* |  | libellé d'action |
| §5 | « Arpendo » | *inchangé* |  | nom |
| §5 | « ou » | *inchangé* |  | séparateur |
| §5 | « Conditions d'utilisation » | *inchangé* |  | libellé de lien |
| §5.1 | « Créer une partie » | *inchangé* |  | libellé |
| §5.1 | « La partie démarre tout de suite et se termine le 14 août à 18 h 42. Recharge de vol : 2 min. » | « La partie démarre tout de suite et se termine le 14 août à 18 h 42. Tu peux voler une tuile toutes les 2 min. » | +18 % | « Recharge de vol » est du jargon ; la règle du cadrage §4.2 dite au joueur |
| §5.1 | « Durée de la partie » | *inchangé* |  | libellé |
| §5.1 | « 30 min » | *inchangé* |  | étiquette |
| §5.1 | « 1 mois » | *inchangé* |  | étiquette |
| §5.1 | « 24 heures » | *inchangé* |  | valeur annoncée |
| §5.1 | « 24 h » | *inchangé* |  | valeur |
| §5.1 | « Pas de connexion — impossible de créer une partie. » | « Pas de réseau. La partie n'est pas créée. » | -18 % | cause puis conséquence ; le bouton reste actif |
| §5.2 | « Rejoindre une partie » | *inchangé* |  | libellé |
| §5.2 | « Rejoindre » | *inchangé* |  | libellé d'action |
| §5.2 | « Saisis le code à 6 caractères. » | *inchangé* |  | aide de saisie |
| §5.2 | « Ce code n'existe pas. » | *inchangé* |  | constat court, un des quatre échecs distincts |
| §5.2 | « Cette partie est terminée. » | *inchangé* |  | constat |
| §5.2 | « Cette partie est complète. » | « Cette partie a déjà 10 joueurs. » | +19 % | dit pourquoi |
| §5.2 | « Tu es déjà dans une partie. » | *inchangé* |  | constat |
| §5.2 | « Pas de connexion — impossible de rejoindre. » | « Pas de réseau. Le code n'est pas vérifié. » | -5 % | cause puis conséquence ; parallèle à §5.1 |
| §5.3 | « Impossible de charger les couleurs disponibles. » | « Les couleurs disponibles ne sont pas arrivées. » | -2 % | forme commune des échecs de chargement |
| §5.3 | « Choisis ta couleur » | *inchangé* |  | titre |
| §5.3 | « Entrer dans la partie » | *inchangé* |  | libellé d'action |
| §5.3 | « Cette couleur vient d'être prise. Choisis-en une autre. » | *inchangé* |  | explique déjà |
| §6 | « Joue prudemment » | *inchangé* |  | avertissement de sécurité — garde-fou 1 |
| §6 | « Arpendo se joue dans la rue. Regarde autour de toi, pas ton téléphone. Ne joue pas au volant. Certains lieux ne sont pas des terrains de jeu : respecte les propriétés privées, les établissements scolaires et les lieux de soin. » | *inchangé* |  | avertissement de sécurité — garde-fou 1 |
| §6 | « Lire les conditions d'utilisation » | *inchangé* |  | libellé de lien |
| §6 | « J'ai compris » | *inchangé* |  | libellé d'action |
| §6.1 / §7.4 | « Le classement se met à jour à chaque capture. Personne ne voit la position de personne. » | *inchangé* |  | information plate |
| §7.1 | « 124 hex · 12 400 pts » | *inchangé* |  | valeur |
| §7.1 | « ↑ +300 » | *inchangé* |  | valeur |
| §7.1 | « ↓ −200 » | *inchangé* |  | valeur |
| §7.1 | « Pendant ton absence : ↓ −4 hex » | *inchangé* |  | bilan factuel |
| §7.1 | « 27 j » | *inchangé* |  | format de timer |
| §7.1 | « 2 j 04 h » | *inchangé* |  | format de timer |
| §7.1 | « 18 h » | *inchangé* |  | format de timer |
| §7.1 | « 1 h 12 » | *inchangé* |  | format de timer |
| §7.1 | « 09:47 » | *inchangé* |  | format de timer |
| §7.1 | « Terminée » | *inchangé* |  | état |
| §7.1 | « — hex · — pts » | *inchangé* |  | état de chargement |
| §7.3 | « C'est bon, tu peux la reprendre. » | « Tu peux la reprendre. » | -34 % | interjection retirée ; bonne nouvelle plate |
| §7.4 | « 5 joueurs · fin dans 2 j 04 h » | *inchangé* |  | en-tête |
| §7.4 | « hex · pts » | *inchangé* |  | en-tête de colonne |
| §7.4 | « (toi) » | *inchangé* |  | marque |
| §7.4 | « dernière capture il y a 2 h » | *inchangé* |  | cité du cadrage §7.5 |
| §7.4 | « Tu es seul dans la partie. » | « Personne d'autre pour l'instant. » | +23 % | forme genrée (« seul ») neutralisée ; « Inviter » dit quoi faire |
| §7.4 | « Inviter » | *inchangé* |  | libellé d'action |
| §7.4 | « aucune capture pour l'instant » | *inchangé* |  | cité du cadrage §7.5 |
| §7.4 | « Impossible de charger les joueurs. » | « La liste des joueurs n'est pas arrivée. » | +15 % | forme commune des échecs de chargement |
| §7.4 | « Mis à jour il y a 6 min » | *inchangé* |  | mention de fraîcheur |
| §7.4 | « il y a 12 min » | *inchangé* |  | horodatage |
| §7.4 | « Hier 18 h 42 » | *inchangé* |  | horodatage |
| §7.4 | « près de toi » | *inchangé* |  | bande de distance |
| §7.4 | « dans ta région » | *inchangé* |  | bande de distance |
| §7.4 | « loin » | *inchangé* |  | bande de distance |
| §7.4 | « Chloé rejoint la partie. » | *inchangé* |  | entrée de flux, factuelle |
| §7.4 | « Bob quitte la partie. 137 tuiles sont libérées. » | *inchangé* |  | entrée de flux, factuelle |
| §7.4 | « La partie se termine dans 1 heure. » | *inchangé* |  | entrée de flux, factuelle |
| §7.4 | « La partie est terminée. » | *inchangé* |  | entrée de flux, factuelle |
| §7.4 | « Sur la dernière heure : Alice +23 tuiles, Bob +12, Chloé +4. » | *inchangé* |  | entrée de flux, factuelle |
| §7.4 | « Bob passe en tête. » | *inchangé* |  | bonne nouvelle plate — l'exemple du questionnaire |
| §7.4 | « Alice dépasse 250 tuiles. » | *inchangé* |  | entrée de flux, factuelle |
| §7.4 | « Alice a pris 5 tuiles à Bob dans la dernière heure. » | *inchangé* |  | entrée de flux, factuelle |
| §7.4 | « Chloé a capturé 30 tuiles en 20 minutes. » | *inchangé* |  | entrée de flux, factuelle |
| §7.4 | « Alice t'a pris 2 tuiles. » | *inchangé* |  | la perte se constate : qui, combien |
| §7.4 | « Tu as pris 3 tuiles à Alice. » | *inchangé* |  | bonne nouvelle plate |
| §7.4 | « Rien ne s'est encore passé. Le premier bilan arrive dans 5 minutes. » | « Rien à relever pour l'instant. Le premier bilan tombe dans 5 minutes. » | +3 % | réécriture fixée par l'identité §1.7 |
| §7.4 | « Impossible de charger la suite. » | « La suite n'est pas arrivée. » | -13 % | forme commune des échecs de chargement |
| §7.4 | « Activité » | *inchangé* |  | titre |
| §7.4 | « Copier le code » | *inchangé* |  | libellé d'action |
| §7.4 | « Partager » | *inchangé* |  | libellé d'action |
| §7.4 | « Donne ce code à tes amis pour qu'ils rejoignent la partie. » | *inchangé* |  | explique déjà |
| §7.4 | « Le code reste valide pendant toute la partie. » | *inchangé* |  | information plate |
| §7.4 | « Code copié » | *inchangé* |  | accusé de réception |
| §7.4 | « Rejoins ma partie sur Arpendo, le code est K7MQ4P. / Arpendo, c'est un jeu de territoire : tu colores les hexagones où tu marches. / https://play.google.com/… » | *inchangé* |  | message de partage : sans emoji, factuel |
| §7.4 | « Impossible de charger le code. » | « Le code n'est pas arrivé. » | -17 % | forme commune des échecs de chargement |
| §7.4 | « Quitter définitivement ? » | *inchangé* |  | titre |
| §7.4 | « Tu perds tes 1 247 hexagones et tes 124 700 points. Cette action est irréversible. » | **en attente — Q1** |  | cadrage §4.4 |
| §7.4 | « Tes hexagones redeviennent libres pour tous les joueurs. Tu peux rejoindre à nouveau, mais tu repartiras de zéro. » | **en attente — Q1** |  | dépend du corps 1 |
| §7.4 | « Écris **définitivement** pour confirmer » | *inchangé* |  | libellé de champ |
| §7.4 | « Quitter définitivement » | *inchangé* |  | libellé d'action |
| §7.4 | « Tu as quitté la partie. » | *inchangé* |  | constat |
| §8 | « compte Google · theo@gmail.com » | *inchangé* |  | valeur |
| §8 | « Ton pseudo est définitif. » | *inchangé* |  | information plate |
| §8 | « Permissions » | *inchangé* |  | libellé |
| §8 | « Historique des parties » | *inchangé* |  | libellé |
| §8 | « Supprimer mon compte depuis le web » | *inchangé* |  | libellé de lien |
| §8 | « Cette partie » | *inchangé* |  | libellé de section |
| §8 | « Quitter la partie » | *inchangé* |  | libellé d'action |
| §8 | « Ce compte » | *inchangé* |  | libellé de section |
| §8 | « Se déconnecter de Google » | *inchangé* |  | libellé d'action |
| §8 | « Supprimer mon compte » | *inchangé* |  | libellé d'action |
| §8.1 | « Tout est autorisé. » | *inchangé* |  | état |
| §8.1 | « Localisation en arrière-plan non autorisée » | *inchangé* |  | sous-titre d'état d'une ligne de réglage |
| §8.1 | « Notifications non autorisées » | *inchangé* |  | sous-titre d'état |
| §8.1 | « 2 autorisations manquantes » | *inchangé* |  | sous-titre d'état |
| §8.2 | « Joueur supprimé » | *inchangé* |  | libellé |
| §8.2 | « Aucune partie terminée pour l'instant. » | *inchangé* |  | constat daté |
| §8.2 | « Tes parties apparaîtront ici quand elles seront finies. » | « Tes parties apparaissent ici une fois terminées. » | -13 % | au présent |
| §8.2 | « Impossible de charger l'historique. » | « L'historique n'est pas arrivé. » | -14 % | forme commune des échecs de chargement |
| §8.2 | « abandonnée » | *inchangé* |  | mention |
| §8.3 | « Supprimer ton compte ? » | *inchangé* |  | titre |
| §8.3 | « Ton compte est désactivé immédiatement et toutes tes données sont effacées sous 30 jours. » | *inchangé* |  | constat, au présent |
| §8.3 | « Ton pseudo devient "Joueur supprimé" dans les classements. » | *inchangé* |  | conséquence factuelle |
| §8.3 | « Ta couleur est libérée. » | *inchangé* |  | conséquence factuelle |
| §8.3 | « Tes hexagones redeviennent libres. » | *inchangé* |  | conséquence factuelle |
| §8.3 | « Ton pseudo ne sera jamais réattribué. » | *inchangé* |  | conséquence factuelle — « jamais » est ici un fait, pas une emphase |
| §8.3 | « Écris **supprimer** pour confirmer » | *inchangé* |  | libellé de champ |
| §8.3 | « Supprimer définitivement » | *inchangé* |  | libellé d'action |
| §8.3 | « Ton compte a été supprimé. » | *inchangé* |  | constat |
| §9 | « Partie abandonnée » | *inchangé* |  | titre |
| §9 | « Tous les joueurs ont quitté la partie. » | *inchangé* |  | constat |
| §9 | « Les joueurs ayant quitté la partie n'apparaissent pas au classement. » | *inchangé* |  | information plate |
| §9 | « Cette partie s'est terminée sans joueur. » | *inchangé* |  | constat |
| §9 | « Impossible de charger le classement. » | « Le classement n'est pas arrivé. » | -14 % | forme commune des échecs de chargement |
| §10.1 | « Capture en cours » | *inchangé* |  | nom de canal Android |
| §10.2 | « 124 hex · 2 j 04 h restantes » | *inchangé* |  | valeur |
| §10.2 | « Capture en pause — hors ligne » | **en attente — Q1** |  | cadrage §10.3 |
| §10.2 | « Serveur indisponible — la reprise est automatique » | **en attente — Q1** |  | dérivé du cadrage §10.3 |
| §10.2 | « Localisation désactivée — capture arrêtée » | « Sans localisation, la capture est arrêtée. » | +2 % | cause puis conséquence, en phrase |
| §10.2 | « Partie terminée » | *inchangé* |  | état |
| §10.3 | « Arpendo t'avertit si la capture s'arrête, et quand la partie se termine. » | *inchangé* |  | amorce, explique déjà |
| §11.1 | « La partie se termine bientôt » | *inchangé* |  | titre de notification |
| §11.1 | « Plus qu'une heure. Tu es 3ᵉ avec 124 hex. » | *inchangé* |  | factuel |
| §11.1 | « Alice gagne avec 312 hex. Tu es 3ᵉ. » | *inchangé* |  | factuel |
| §11.2 | « Mise à jour nécessaire » | *inchangé* |  | titre |
| §11.2 | « Cette version d'Arpendo n'est plus compatible avec le serveur. Installe la dernière version pour continuer à jouer. » | *inchangé* |  | explique déjà : ce qui se passe, puis quoi faire |
| §11.2 | « Ta partie et ta progression sont conservées. » | *inchangé* |  | réassurance factuelle |
| §12.3 | « Arpendo a besoin de ta position pour colorer les hexagones où tu marches. » | *inchangé* |  | amorce, explique déjà |
| §12.3 | « Pour que la capture reprenne toute seule après un redémarrage de ton téléphone. » | « Avec cette autorisation, la capture reprend toute seule après un redémarrage de ton téléphone. » | +19 % | un fragment devient une phrase qui dit ce que donne l'autorisation |
