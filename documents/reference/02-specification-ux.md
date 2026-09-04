# Arpendo — Spécification UX

> **Ce document ne porte que l'état courant.** Aucune décision abandonnée, aucune option écartée,
> aucun historique de révision : ce qui est écrit ici est ce qu'il faut construire. Le raisonnement
> et les décisions antérieures vivent dans `../archive/journal-decisions-ux.md`, qui n'est pas
> normatif.
>
> **Portée :** MVP. Flutter + `mapbox_maps_flutter`, Android d'abord, français seul, 10 joueurs
> maximum, 2 écrans de fond + modales.
> **Source normative :** `01-cadrage.md`. Ce document **spécifie l'interface** de décisions déjà
> prises ; il n'en rouvre aucune.
> **Identité visuelle :** `03-identite-visuelle.md`. Ses valeurs sont **intégrées** ici — §1.2
> (typographie), §1.5 (couleurs de chrome), §1.6 (mouvement), §3.4.1 (marqueur 3D), §4 (marque à
> l'écran).

---

## 0. Comment lire ce document

Chaque composant est spécifié selon quatre rubriques, toujours dans cet ordre :

| Rubrique | Contenu |
|---|---|
| **Rôle** | À quoi il sert, et **le § du cadrage qui le justifie** |
| **États** | normal · vide · chargement · erreur · désactivé · hors ligne — les états non applicables sont écrits « sans objet », jamais omis |
| **Ergonomie** | Position à l'écran, **pourquoi cette position**, taille de cible |
| **Textes** | Le français exact |

**Ton.** Les textes suivent le registre arrêté dans `03-identite-visuelle.md` §1.7 : phrases
courtes, verbes au présent, aucun point d'exclamation, aucune interjection, aucun superlatif, aucun
emoji. **La mauvaise nouvelle s'explique** — ce qui se passe, puis ce qu'on peut faire ; **la bonne
nouvelle reste factuelle.** Les textes cités du cadrage — « Ta progression s'arrêtera si ton
téléphone redémarre » (cadrage §9.2), « aucune capture pour l'instant » (cadrage §7.5) — et
l'avertissement de sécurité du §6 ne bougent pas.

**Convention typographique.** Un texte entre « guillemets français » est **définitif** : il provient
du cadrage mot pour mot, ou il est arrêté ici. Il devient une clé de ressource i18n (§12.6 du
cadrage : aucune chaîne en dur). Un texte en *italique* est un exemple d'affichage dynamique.

**Tolérance de longueur.** Une seule locale est livrée, mais tout conteneur de texte doit absorber
**+30 % de longueur** sans casser sa mise en page (`flutter-setup-localization`). Aucun texte
n'est centré verticalement dans une hauteur fixe ; les boutons grandissent, ils ne tronquent pas.
Cette règle est vérifiable dès le MVP en dupliquant la locale `fr` en `fr-XA` avec des chaînes
allongées.

**Unités.** Toutes les dimensions sont en **dp** (density-independent pixels). Écran de référence
de conception : **360 × 800 dp** — la médiane du parc Android, et le cas le plus contraint.

---

## 1. Socle — tokens de conception

Architecture à trois couches (`design-system`) : primitive → sémantique → composant. **Toutes les
valeurs ci-dessous sont définitives.** Deux d'entre elles ne relèvent pas du goût et ne se
renégocient pas sans repasser un validateur : la **palette joueur** (§3.1), contrainte par l'accessibilité, et la **couleur d'accent**
(§1.5), contrainte par sa séparation d'avec cette palette.

### 1.1 Espacements

Base **4 dp**. Échelle utilisée, sans valeur intermédiaire :

| Token | dp | Emploi |
|---|---|---|
| `space-1` | 4 | Écart intra-composant (icône ↔ libellé) |
| `space-2` | 8 | **Écart minimal entre deux cibles tactiles** |
| `space-3` | 12 | Rembourrage interne d'une carte |
| `space-4` | 16 | **Marge d'écran standard** (gauche/droite partout) |
| `space-6` | 24 | Séparation entre blocs |
| `space-8` | 32 | Séparation entre sections d'une modale |
| `space-12` | 48 | Respiration avant une action destructive |

### 1.2 Typographie

Famille : **Roboto**, la police système Android. Décision **définitive** : la direction « Relevé »
porte son identité par la couleur et le trait, pas par la lettre. Coût d'APK **nul**, couverture française totale — `œ`, `Œ`,
`Æ`, guillemets français, capitales accentuées.

| Token | Taille / interligne | Graisse | Emploi |
|---|---|---|---|
| `type-display` | 32 / 38 | 700 | Score du header, chiffre du tableau des scores |
| `type-title` | 24 / 30 | 600 | Titre de modale |
| `type-headline` | 20 / 26 | 600 | Titre de section, nom d'écran |
| `type-body` | 16 / 24 | 400 | Texte courant, **taille plancher pour tout texte lisible** |
| `type-label` | 14 / 20 | 500 | Libellé de bouton, ligne de liste secondaire |
| `type-caption` | 12 / 16 | 400 | Horodatage, mention de fraîcheur, unité |
| `type-mono` | 20 / 26 | 500, monospace, `letterSpacing: 0,20 em` | **Saisie** du code de partie (§1.7) |
| `type-mono-display` | 40 / 48 | 500, monospace, `letterSpacing: 0,20 em` | **Affichage** du code dans l'onglet Inviter (§7.4) |

Aucun texte sous 12 dp. Le rendu doit suivre le réglage de taille de police du système jusqu'à
**200 %** sans troncature — c'est la raison de la tolérance +30 % du §0.

**Traitement propre à l'identité** — il ne touche pas à l'échelle ci-dessus, qui reste invariante :

- **Graisse 400 par défaut** : c'est celle du texte courant et de l'horodatage. Les six autres
  jetons montent selon le tableau ci-dessus, sans dépasser 600 sauf `type-display`. La direction
  est sobre ; le texte ne prend pas de poids pour exister.
- **Chiffres tabulaires** (`fontFeatures: [FontFeature.tabularFigures()]`) sur **le score du
  header, le timer, les scores de liste et le tableau des scores**. Sans eux, un score qui passe de
  12 400 à 12 300 fait danser toute la ligne — un défaut particulièrement visible sur une valeur
  qui se met à jour en continu.
- **Interlettrage `+0,01 em` sur `type-caption`** uniquement. Les petites tailles se referment au
  soleil ; c'est le seul endroit où l'espacement gagne de la lisibilité.
- Le **logotype est composé en Roboto w500**, capitale initiale, interlettrage `+0,02 em` — hors
  échelle : sa taille se fixe en **hauteur de capitale** (§4), jamais en corps. C'est la
  composition de l'actif `logo-arpendo.svg`, livré avec l'identité (§1.5 de `03-identite-visuelle.md`).

### 1.3 Rayons et élévations

| Token | Valeur | Emploi |
|---|---|---|
| `radius-sm` | 8 | Champ de saisie, pastille de couleur |
| `radius-md` | 16 | Carte, bandeau |
| `radius-lg` | 28 | Feuille modale (coins hauts uniquement) |
| `radius-full` | ∞ | Pastille de delta, FAB, pastille d'alerte |
| `elev-0` | 0 | Contenu à plat |
| `elev-1` | 1 dp | Puces de header, bandeau |
| `elev-3` | 3 dp | Bouton flottant sur la carte |
| `elev-6` | 6 dp | Feuille modale, modale de confirmation |

Sur la carte, l'élévation ne suffit pas : une ombre portée disparaît sur un fond de couleur
franche. **Tout élément flottant au-dessus de la carte porte en plus un contour de 1 dp** dans le
neutre sombre (§1.5), sans quoi un bouton blanc devient invisible sur un hexagone clair.

### 1.4 Cibles tactiles et zones du pouce

Règles dures (`mobile-design`, plateforme Android) :

- **Cible minimale : 48 × 48 dp.** Aucune exception, y compris pour une icône dessinée en 24 dp —
  la zone tactile est étendue autour du dessin.
- **Écart minimal entre deux cibles : 8 dp.**
- **FAB principal : 56 dp.**
- **Marge de bord : 16 dp minimum** — un contrôle collé au bord entre en conflit avec les gestes
  système de retour arrière (balayage depuis le bord, Android 10+).

Découpage vertical de l'écran de référence (360 × 800 dp), pouce d'une main :

| Bande | Hauteur | Accessibilité | Ce qu'on y met |
|---|---|---|---|
| **Haute** | 0 → 200 dp | Difficile, nécessite de rattraper le téléphone | **Information à lire, jamais à toucher**, à deux exceptions près, toutes deux rares et non urgentes. **(1)** L'**icône Paramètres de la barre de titre de l'Accueil** (§5) — la convention Android l'y place. **(2)** Les **actions du bandeau** (§2.4) : il occupe l'emplacement unique z 200 sous le header, donc dans cette bande, et sept de ses treize lignes portent un bouton. Elles ne peuvent pas descendre — les séparer de leur message les rendrait illisibles, et déplacer le bandeau rouvrirait le budget vertical du §2.2. La plus critique, « Réglages », est le **seul chemin de sortie** d'une permission refusée (cadrage §9.3, §12.2) : la rendre difficile à atteindre est le prix d'un message qu'on lit avant d'agir. **Hors ces deux cas, la bande haute de l'écran Jeu est inerte** — les puces de header ne portent aucune action (§7.1) |
| **Médiane** | 200 → 520 dp | Correcte | Carte, contenu de liste |
| **Basse** | 520 → 800 dp | **Zone du pouce** | Toutes les actions fréquentes : le bouton d'action « Partie », le bouton Recentrer |

Corollaire appliqué partout : **une action destructive n'est jamais dans la bande basse.**
« Quitter la partie » et « Supprimer le compte » sont volontairement placés en fin de liste
défilante, hors du chemin du pouce au repos.

### 1.5 Couleurs de chrome — définitives

Valeurs de la direction **« Relevé »**. Le raisonnement et l'intégralité des calculs de séparation
sont dans `03-identite-visuelle.md` ; ce paragraphe n'en porte que le résultat.

**Mode clair** — le défaut.

| Token sémantique | Valeur | Rôle | Contrôle |
|---|---|---|---|
| `surface` | `#FDFBF6` | Fond de modale, de feuille | — |
| `surface-dim` | `#F1EDE2` | Fond d'écran hors carte, fond de la carte masquée | §3.1 rejoué, voir la note |
| `on-surface` | `#1A1D18` | Texte principal | 16,47:1 sur `surface` |
| `on-surface-muted` | `#5C6157` | Texte secondaire, horodatage | 6,15:1 sur `surface` · 5,44:1 sur `surface-dim` |
| `outline` | `#C7C3B5` | Contours, séparateurs | — |
| `scrim` | `#1A1D18` à 40 % | Voile derrière une modale | — |
| `accent` | **`#123D1E`** | Action principale | blanc dessus 12,27:1 · **ΔE 18,3** de la couleur joueur la plus proche |
| `accent-pressed` | `#052D11` | État pressé | ΔE 24,2 |
| `accent-light` | `#E8EFE9` | Fond teinté (sélection, encart) | `on-surface` dessus 14,56:1 · ΔE 20,8 |
| `danger` | `#B3261E` | Action destructive, erreur bloquante | 6,32:1 sur `surface` — voir la règle ci-dessous |
| `warning` | `#7A4F00` | Avertissement non bloquant | 6,89:1 sur `surface` |

> **Il n'existe volontairement aucun jeton `success`.** Le §16 établit qu'aucune teinte au-dessus de
> L 0,40 n'est à ΔE ≥ 15 des dix couleurs joueur : **tout vert de succès en mode clair serait donc
> un vert sombre**, c'est-à-dire un second vert sombre à côté d'`accent`, que rien ne distinguerait
> de lui. Un jeton de plus, une validation de plus, et deux couleurs confondues.
>
> **Ce qui remplace le jeton, en deux règles :**
>
> 1. **Un état positif est porté par le glyphe et le texte, jamais par une couleur propre.** Là où
>    une couleur est nécessaire — le ✓ « pseudo disponible » du §4.1 — c'est **`accent`**, déjà
>    validé à ΔE 18,3 des dix et à 12,27:1 sur `surface`.
> 2. **La pastille de delta du §7.1 est neutre dans les deux sens** : fond `surface-dim`, texte
>    `on-surface`, direction portée par la flèche et le signe seuls. C'est l'application littérale
>    de la règle du §7.1 — « hausse et baisse ont exactement le même traitement » — que colorer la
>    hausse en vert et la baisse en `warning` contredisait.

**Les trois sévérités du bandeau (§2.4) ne créent aucun jeton non plus.** Elles se lisent à la
**forme du glyphe** (§1.8), la couleur n'étant qu'un renfort pris dans les jetons existants :

| `severite` | Glyphe | Couleur du glyphe | Couleur du texte |
|---|---|---|---|
| `info` | cercle « i » | `on-surface-muted` | `on-surface` |
| `avertissement` | triangle « ! » | `warning` | `on-surface` |
| `bloquant` | octogone « ! » | `danger` | `on-surface` |

Trois silhouettes distinctes — cercle, triangle, octogone — lisibles sans couleur et sans texte.

**Mode sombre** — disponible, **jamais imposé** : il suit le réglage système et rien d'autre.

| Token sémantique | Valeur | Contrôle |
|---|---|---|
| `surface` | `#1A1E1A` | — |
| `surface-dim` | `#101310` | — |
| `on-surface` | `#EDEAE0` | 14,02:1 sur `surface` |
| `on-surface-muted` | `#9CA096` | 6,33:1 sur `surface` |
| `outline` | `#3A403A` | — |
| `scrim` | `#000000` à **55 %** | un voile de 40 % ne sépare rien sur fond sombre |
| `accent` | **`#C9F7BE`** | 15,62:1 sur `surface-dim` · **ΔE 19,4** |
| `accent-pressed` | `#D2F8C8` | ΔE 20,2 |
| `accent-light` | `#23331F` | ΔE 21,0 |
| `danger` | `#F2B8B5` | 9,88:1 sur `surface` |
| `warning` | `#F5C77E` | 10,73:1 sur `surface` |

**Comment ces contrastes se mesurent.** Tous les ratios des deux tableaux ci-dessus valent sur un fond **opaque**. Un texte posé sur une surface translucide
au-dessus de la carte ne se mesure pas contre `surface` mais contre **le fond composité**, et le
pire fond possible est l'une des dix couleurs joueur (§3.1) — un aplat de magenta `#EB31A5` ou de
vert pomme `#97C425` sous une plaque à 88 %.

**Conséquence, et c'est une règle dure : toute surface qui porte du texte au-dessus de la carte est
opaque.** Le header (§7.1) et les plaques de la pile d'activité (§7.2.1) sont en `surface` plein,
avec le contour de 1 dp du §1.3. **Aucun flou, nulle part** — un `BackdropFilter` au-dessus d'une
surface Mapbox qui se repeint en continu est un coût de rendu permanent que le §3.3 refuse déjà
ailleurs (« effondre le rendu sur un téléphone bas de gamme »), et il ne rachète rien puisque le
contraste sous-jacent reste incalculable. L'immersion est portée par le §2.3 — la carte court sous
l'encoche et occupe tout le reste — pas par un chrome semi-transparent.

**Trois règles qui accompagnent ces valeurs et ne se déduisent pas du tableau.**

1. **L'état pressé s'inverse selon le mode.** En clair, `accent-pressed` **fonce** ; en sombre, il
   **éclaircit**. Ce n'est pas une préférence : foncer un accent pâle en mode sombre le fait
   retomber dans la bande de clarté des couleurs joueur — mesuré à ΔE 11 à 12, sous le plancher
   de 15. La méthode est celle des *state layers* de Material 3, appliquée ici par nécessité.
2. **La carte suit le mode.** Le style Mapbox Standard expose un `lightPreset` (`dawn` · `day` · `dusk` ·
   `night`) sur l'import de style, **par le même appel de configuration que les libellés du §3.2**.
   Le coût est donc nul : une propriété de plus à poser, pas un style à maintenir. En mode sombre,
   `lightPreset: night` ; en mode clair, `day`. Détail et repli en §3.2.

   **L'accent de mode sombre garde néanmoins son seuil de ΔE 15.** La couche hexagones n'est pas
   affectée par le `lightPreset` — elle porte les couleurs joueur, pleines, dans les deux modes.
   Un bouton « Recentrer » flotte toujours au-dessus d'aplats colorés, quel que soit le fond
   dessous. Ce qui change est le fond neutre, pas les territoires.

   **Ce que ça oblige à revalider, et qui est ouvert :** le rapport du validateur du §3.1 a été
   calculé contre `#F1EDE2`, un fond **clair**. Sur un fond `night`, les quatre couleurs en `WARN`
   de contraste cessent de l'être — ce sont les plus claires — et **ce sont les trois plus sombres
   (`#BD3216`, `#007559`, `#773B95`) qui passent sous 3:1**. Le contour d'hexagone du §3.3 reste le
   relief qui traite le cas, exactement comme en mode clair, mais **le rapport doit être rejoué sur
   le fond sombre réel** avant la livraison du mode sombre. C'est inscrit au §15.2.
3. **`danger` et `warning` ne servent jamais de couleur de remplissage sur la couche carte.**
   `#B3261E` est à **ΔE 3,1** du brique joueur `#BD3216` — pratiquement la même couleur. La
   collision est sans conséquence parce que ces deux jetons sont exclusivement des couleurs de
   texte et d'icône sur `surface`, dans des feuilles et des modales, jamais côte à côte avec un
   territoire. Elle n'est pas corrigeable : tout rouge de danger est proche d'un rouge sombre, et
   le brique joueur *est* un rouge sombre. C'est donc la règle d'emploi qui tient lieu de
   correction, et elle est dure.

**Les trois surfaces claires ne se distinguent pas entre elles, et c'est assumé.**
`surface` `#FDFBF6`, `surface-dim` `#F1EDE2` et `accent-light` `#E8EFE9` sont trois blancs cassés.
Le document mesure des ΔE partout — palette joueur, accent, fond de carte — mais aucun **entre ses
propres surfaces**, et dehors, au soleil, l'écart entre deux d'entre elles est proche de rien.

**Ce n'est pas un défaut tant qu'aucune information ne repose sur cet écart.** La règle qui le
garantit :

> **Une surface ne porte jamais un état à elle seule.** Un fond `accent-light` marque une sélection
> **en plus** d'un second signal non chromatique — contour de 1 dp en `accent`, glyphe, ou graisse.
> C'est la règle « jamais la couleur seule » du §2.4, étendue aux fonds. Un joueur qui ne verrait
> pas la teinte doit voir l'état.

Les seuls emplois de `accent-light` au MVP sont l'encart d'information du §5.1 et le fond de la
pastille de delta écarté au §7.1 — aucun ne porte d'état seul. Le jour où une sélection
persistante en aura besoin, c'est cette règle qui s'applique, pas une nouvelle couleur.

> **Note de méthode.** L'accent n'appartient pas à la même famille que les couleurs joueur et n'est
> pas soumis aux mêmes contrôles. Passé au validateur du skill `dataviz` **avec** les dix, il
> échoue volontairement les contrôles « bande de clarté » et « plancher de chroma » — ceux qui
> vérifient qu'une couleur est un slot de série de données. C'est précisément le fait d'être hors
> de cette bande qui le rend non confondable. Les deux contrôles qui gouvernent la confusabilité,
> `CVD separation` et `Normal-vision floor`, passent tous les deux.

### 1.6 Durées et courbes

| Token | Durée | Emploi |
|---|---|---|
| `motion-press` | **120 ms entrée / 90 ms sortie** | Retour d'appui sur toute cible tactile |
| `motion-fast` | 120 ms | Apparition d'une pastille |
| `motion-base` | **240 ms entrée / 180 ms sortie** | Ouverture/fermeture de feuille, bandeau |
| `motion-map` | 300 ms | Transition de couleur d'un hexagone capturé |
| `motion-camera` | 600 ms | Recentrage, glissement vers la tuile d'un joueur |
| `motion-stagger` | **30 ms par ligne, 8 lignes maximum** | Arrivée d'une liste (§7.4) |

**Deux courbes, pas une.** `Curves.easeOutCubic` à **l'entrée**, `Curves.easeInCubic` à la
**sortie**, et **la sortie dure 75 % de l'entrée**. C'est ce qui fait qu'une interface paraît vive :
un élément qui part aussi lentement qu'il arrive donne l'impression que l'application réfléchit.
La règle remplace la courbe unique retenue initialement.

**Le retour d'appui — `motion-press`.** Échelle **0,98** plus le passage de la surface à son
**état pressé** — `accent-pressed` (§1.5) sur une surface d'accent, qui **fonce en clair et
éclaircit en sombre** ; state layer Material par défaut ailleurs.
**Aucun changement d'élévation, aucune ombre, aucun enfoncement visible** : l'identité
retenue exclut le relief. Un composant qui réclamerait vraiment une profondeur d'appui ne dépasse
pas **1 dp**.

Toutes les durées passent à **0 ms** si `MediaQuery.disableAnimations` est vrai (réglage système
d'accessibilité). Une animation ne porte jamais seule une information — chaque transition
ci-dessous a un état final lisible à l'arrêt.

**Aucune exception, hormis celle nommée ci-dessous.** Le réglage désactive les animations, il
les désactive toutes — y compris le
vol de caméra du §7.4, qui devient un saut instantané, et la transition d'élément partagé qui
l'accompagne. Un joueur qui a demandé zéro mouvement obtient zéro mouvement ; lui en concéder
« juste un peu » quelque part, c'est ne pas respecter le réglage tout en compliquant le code.

**Une seule exception, nommée : l'indicateur de progression indéterminé** (§13.2). Il anime en
continu, réglage compris — c'est un **état**, pas une transition : il n'a pas d'état final, sa
présence est l'information, et figé il serait indiscernable d'un gel de l'application. Il reste
rendu — jamais retiré — sous le réglage, et le délai qui borne son apparition (§13.2) borne déjà
le mouvement inutile. Toute nouvelle exception repasse par l'amendement de ce §, jamais par
analogie avec celle-ci.

**Le principe qui gouverne les formes d'entrée.** Un élément entre **par l'endroit où il va vivre**.
Une feuille ancrée en bas glisse depuis le bas ; une modale centrée grossit sur place, de 96 % à
100 %, avec le fondu de son voile. L'inverse — une modale centrée qui glisse, une feuille qui
grossit — produit l'impression d'une application mal réglée, et c'est le défaut le plus courant des
transitions inventées composant par composant.

### 1.7 Contrainte typographique du code de partie

Le code écarte **toutes les paires de glyphes confondables**, pas seulement `0`/`O` et `1`/`I`.
L'alphabet réel est de **28 caractères** : `ACDEFHJKLMNPQRTUVWXY23456789`.

| Écarté | Se confond avec | Motif |
|---|---|---|
| `O` · `I` | `0` · `1` | Exigence du cadrage §6 |
| `0` · `1` | `O` · `I` | Idem — les deux membres de la paire partent |
| **`S`** · **`B`** · **`Z`** · **`G`** | `5` · `8` · `2` · `6` | Même raison, une paire plus loin. **Le chiffre est gardé, la lettre part** |

**Pourquoi aller jusque-là.** Au MVP il n'y a ni QR code ni lien profond (§6) : le code se
transmet **à l'oral ou écrit à la main**. Un `S` lu pour un `5` produit un « Ce code n'existe
pas. » (§5.2) que personne ne sait diagnostiquer, et le joueur retape le même code indéfiniment.
Une lettre écartée coûte des combinaisons ; un code illisible coûte un joueur.

**Le coût est nul à cette échelle** : 28⁶ = **481 millions** de codes, pour un plafond de 10 joueurs
par partie. La règle de génération et la vérification côté serveur portent le même alphabet — un
code généré hors de cet alphabet serait insaisissable, puisque le champ le filtre à la frappe.

- Saisie en `type-mono`, affichage dans l'onglet Inviter en `type-mono-display`, **majuscules
  forcées** dans les deux cas.
- **L'interlettrage est exprimé en `em`, jamais en dp** (`0,20 em`). Un `letterSpacing: 4` absolu
  vaut un cinquième de la chasse à 20 dp et un dixième à 40 dp : le même jeton produirait deux
  respirations différentes selon l'endroit, ce qui est exactement ce qu'une échelle typographique
  sert à empêcher.
- Le champ **filtre à la frappe** : tout caractère hors alphabet est ignoré silencieusement. Ne pas
  afficher d'erreur pour un caractère qu'on refuse déjà.
- **Un seul champ**, pas six cases. Six cases coûtent un composant de plus, cassent le
  collage depuis le presse-papiers et n'apportent rien qu'un `letterSpacing` ne donne.

### 1.8 Icônes — jeu retenu et inventaire

Le §2.4 fait porter la sévérité d'un bandeau par le **glyphe** et non par la couleur : sans jeu
d'icônes nommé, cette règle n'est pas applicable.

**Jeu retenu : Phosphor, graisse `Regular`** (`phosphor_icons`, licence MIT).

Pourquoi celui-là plutôt que les `Icons.*` fournis par Flutter : l'identité « Relevé » est portée
**par le trait** — contour d'hexagone de 1 dp (§3.3), *backface hull* du marqueur (§3.4.1), contour
de pastille de 1 dp (§3.4). Phosphor est un jeu à trait uniforme dont la graisse se règle, donc il
parle la même langue que le reste de l'interface. Les Material Icons ont un trait plus épais et des
raccords arrondis qui jurent avec un fond de carte topographique. Le coût est un paquet : la
graisse employée est tree-shakée à la compilation, mais les cinq autres graisses que le paquet
déclare restent embarquées — **2,58 Mo**, qu'un sous-ensemble embarqué supprimerait.

**Règles d'emploi.** Dessin à **24 dp**, zone tactile à **48 dp** (§1.4). Couleur héritée du
contexte, jamais posée en dur. Une icône ne remplace jamais un libellé sur une action nommée ; elle
l'accompagne, ou elle est seule là où la convention Android l'autorise (Paramètres, Recentrer).

| Usage | Glyphe Phosphor | § |
|---|---|---|
| Bandeau — sévérité `info` | `Info` (cercle) | 2.4 |
| Bandeau — sévérité `avertissement` | `Warning` (triangle) | 2.4 |
| Bandeau — sévérité `bloquant` | `WarningOctagon` (octogone) | 2.4 |
| Paramètres | `Gear` | 7.4, 5 |
| Recentrer | `CrosshairSimple` | 7.2 |
| Bouton d'action « Partie » | `UsersThree` | 7.4 |
| Delta à la hausse / à la baisse | `ArrowUp` / `ArrowDown` | 7.1 |
| Pseudo — disponible / invalide | `CheckCircle` / `XCircle` | 4.1 |
| Copier le code | `Copy` | 7.4 |
| Partager | `ShareNetwork` | 7.4 |
| Ligne « Permissions » | `ShieldCheck` | 8.1 |
| Ligne « Historique des parties » | `ClockCounterClockwise` | 8.2 |
| « Se déconnecter de Google » | `SignOut` | 8 |
| Notification permanente (statut Android) | **silhouette d'hexagone monochrome**, ressource propre — `documents/assets/signe-arpendo.svg` | 10.1 |

**Les trois glyphes de sévérité sont non substituables.** Cercle, triangle et octogone sont trois
**silhouettes** différentes, donc lisibles en niveaux de gris, à petite taille et pour un daltonien.
Remplacer l'un des trois par une variante de même contour annulerait la règle du §2.4.

**Pas de jeu d'icônes secondaire.** Une seule famille, une seule graisse. Les seuls dessins hors
Phosphor sont ceux de l'identité — le signe, l'icône d'app, la silhouette de notification —
livrés avec `03-identite-visuelle.md` ; le logotype, lui, est du texte Roboto (§1.2).

---

## 2. Architecture d'écran

### 2.1 Les deux écrans de fond et le routage

| Écran | Condition d'affichage |
|---|---|
| **Connexion** | Aucune session valide |
| **Menu** | Session valide **et** aucune partie active (§8.3) |
| **Jeu** | Session valide **et** une partie active (§8.3) |

Le Menu et le Jeu **ne coexistent jamais**. Tout le reste — création, participation, paramètres,
participants, flux, invitation, scores, confirmations — s'ouvre **par-dessus**.

**Séquence de démarrage**, dans cet ordre exact :

1. Contrôle de version (§11) → écran bloquant si version minimale non atteinte, **avant tout appel
   authentifié**. Un client obsolète ne doit pas taper une API qu'il ne comprend plus.
2. Session → Connexion, ou suite.
3. Requête « ai-je une partie active ? » → Jeu, ou Menu.
4. Évaluation des permissions (§13), **à chaque passage au premier plan**, pas seulement ici.

**Pendant les étapes 2 à 3**, l'écran affiché est un **écran d'attente neutre** : le bloc de
marque du §4 — signe, logotype, accroche « prends du terrain » — et **rien d'autre**. **Aucun
indicateur de progression** : le bloc affiché est déjà le signe que l'application démarre, et
l'attente est **bornée par le délai du client HTTP**, 10 s par tentative — l'écran ne peut pas
rester statique plus longtemps avant de basculer vers l'étape suivante ou vers l'échec. C'est
cette borne qui rend l'absence d'indicateur acceptable : un flux qui allongerait l'attente
au-delà (téléchargement, migration locale) rouvre la question.

**Le bloc de marque ne bouge pas.** Sa position est la même dans les trois états — attente,
échec, prêt — et ce qui apparaît sous lui prend sa place **sans le déplacer** : un logo qui
remonte à chaque changement d'état se lit comme une instabilité de l'application. Il est
**centré verticalement**, et non en bande haute comme au §4 et au §5, parce que cet écran n'a ni
action permanente ni contenu à dégager sous lui.

Serveur injoignable à l'étape 3 : « Le serveur ne répond pas. » + bouton « Réessayer » (réseau absent :
bandeau priorité 5).
Ne jamais router vers le Menu par défaut : un joueur dont la partie est en cours verrait
« Créer une partie » et croirait sa partie perdue.

### 2.2 Pile de calques — le contrat de mise en page

C'est le contrat que tout composant respecte. Il résout le conflit signalé dans l'ancien
document entre header, bandeaux d'état et bandeau de mise à jour.

```
┌─ z 500 · Écran bloquant plein écran (mise à jour obligatoire)
├─ z 400 · Modale de confirmation + voile
├─ z 300 · Feuille modale (Partie, Paramètres) + voile
├─ z 200 · Bandeau — EMPLACEMENT UNIQUE, un seul à la fois (§2.4)
├─ z 100 · Puces de header (écran Jeu, §7.1) / barre de titre (autres écrans)
├─ z  50 · Contrôles flottants sur la carte : bouton d'action « Partie » et Recentrer
├─ z  40 · Pile d'activité (§7.2.1) — sous les contrôles, et non interactive sauf sa ligne du bas
└─ z   0 · Carte Mapbox
```

**Budget vertical sur 360 × 800 dp, écran Jeu :**

| Élément | Hauteur retirée à la carte |
|---|---|
| Encoche / barre d'état (safe area haute) | 24–48 |
| **Puces de header** (§7.1) | **0** — elles flottent, la carte court dessous |
| Bandeau, s'il y en a un | **56 à 136** selon son contenu (§2.4) |
| Barre de gestes (safe area basse) | 24–48 |
| **Carte réellement visible** | **≈ 648 à 696 dp (81 à 87 %)** avec un bandeau d'une ligne sans action ; **≈ 568 à 616 dp (71 à 77 %)** dans le cas le plus chargé — deux lignes et une action |

**Deux surfaces occultent la carte sans la réduire, et il faut les compter à part** — le
pourcentage ci-dessus ne les déduit pas, exactement comme au §7.2.1 :

| Surface | Occultation |
|---|---|
| Puces de header (§7.1) | ≈ **300 × 40 = 12 000 dp²**, en haut |
| Pile d'activité (§7.2.1) | ≈ **240 × 120 = 28 800 dp²**, en bas à gauche |

C'est ce budget qui impose la règle du §2.4 : **empiler trois bandeaux ramènerait la carte sous
60 % de l'écran**, et la carte est le jeu.

### 2.3 Safe areas

- `SafeArea(top: true, bottom: true)` enveloppe **tout sauf la carte**. La carte occupe l'écran
  entier, y compris sous l'encoche — c'est ce qui donne l'impression d'immersion, et rien
  d'interactif n'y vit.
- Les contrôles flottants sont positionnés **par rapport à la safe area**, jamais par rapport au
  bord physique.
- Le rembourrage bas de toute feuille modale ajoute `MediaQuery.viewInsets.bottom` (clavier) **et**
  `MediaQuery.padding.bottom` (barre de gestes). Un bouton « Confirmer » sous le clavier est le
  défaut le plus fréquent des feuilles Flutter.

### 2.4 Le composant Bandeau — unique, paramétré

**Rôle.** Porter tout message d'état persistant : permissions (§9.3), réseau (§10), explication
d'action sans effet (§4.2 et §4.3), mise à jour recommandée (§14.1). Le cadrage impose
explicitement **un seul composant** (§9.3, dernière puce) ; ce document l'étend aux trois autres
familles, parce qu'elles ont la même anatomie et le même emplacement.

**Anatomie.** Largeur pleine moins `space-4` de chaque côté, `radius-md`, `elev-1`, rembourrage
interne `space-4`. Icône 24 dp à gauche, **`space-3`** d'écart — et non `space-1`, qui vaut pour une
icône accolée à son libellé dans un même contrôle (§1.1), là où l'icône et le message du bandeau
sont deux éléments distincts —, puis le texte `type-body` ; **zéro à deux actions sur une seconde
rangée**, alignées à droite, séparées du message par `space-2`. Les actions sont des boutons texte
de **48 × 48 dp minimum** (§1.4, « aucune exception »).

**La hauteur est un résultat, jamais une consigne** (§0 : les conteneurs grandissent, ils ne
tronquent pas). Elle vaut `space-4` × 2 plus la hauteur du contenu, où une ligne de `type-body`
compte 24 dp (§1.2) et une rangée d'actions 48 + `space-2` (§1.4). D'où, pour les cas courants :

| Contenu | Hauteur |
|---|---|
| une ligne, aucune action | **56 dp** |
| deux lignes, aucune action | **80 dp** |
| une ligne, avec action(s) | **112 dp** |
| deux lignes, avec action(s) | **136 dp** |

Ce sont des **illustrations de la règle, pas une énumération** : un message plus long continue de
grandir de 24 dp par ligne, et les tests mesurent, ils ne recopient pas.

**Pourquoi les actions ne partagent pas la rangée du message.** Sur l'écran de référence de
360 dp, il reste 260 dp une fois retirés les marges, le rembourrage, l'icône et son écart. Les
deux actions des priorités 10 et 11 — « Réglages » et « Masquer pour cette partie » — les
consomment à elles seules. Le message garde donc toute la largeur, ce qui le rend insensible à la
longueur des libellés comme à la tolérance de +30 % du §0.

**Paramètres du composant :**

| Paramètre | Valeurs |
|---|---|
| `severite` | `info` · `avertissement` · `bloquant` |
| *(icône)* | **dérivée de `severite`**, pas un paramètre : cercle · triangle · octogone, 24 dp — la sévérité se porte par la **forme**, **jamais la couleur seule** |
| `texte` | chaîne i18n |
| `actions` | 0 à 2 boutons texte |
| `bloquant` | masque la carte et coupe les interactions de jeu |

**Règle d'unicité et priorité.** **Un seul bandeau est affiché à la fois.** Quand plusieurs
conditions sont vraies, la plus prioritaire gagne ; les autres sont muettes jusqu'à résolution.
Justification : le budget vertical du §2.2, et le fait qu'un joueur ne peut de toute façon
traiter qu'un problème à la fois — celui d'en haut est toujours la cause des suivants.

| Prio | Condition | Sévérité | Texte | Actions |
|---|---|---|---|---|
| 1 | Localisation de base refusée | bloquant | « Sans ta position, Arpendo ne sait pas où tu marches. » | « Réglages » |
| 2 | Localisation de base refusée, **après 2 refus** | bloquant | « Android ne redemandera plus. Ouvre les réglages pour autoriser la localisation. » | « Réglages » |
| 3 | Permission retirée **en cours de partie** | bloquant | « Tu es toujours dans la partie. Autorise la localisation pour reprendre la capture. » | « Réglages » |
| 4 | Serveur injoignable, réseau présent, **coupure < 5 min** | avertissement | « Le serveur ne répond pas. Garde l'application ouverte, la reprise est automatique. » | — |
| 5 | Réseau absent, **coupure < 5 min** | avertissement | « Pas de réseau. La reprise est automatique. » | — |
| 6 | Coupure **≥ 5 min**, quelle qu'en soit la cause | avertissement | « Coupure de plus de 5 min. Tes pas ne comptent pas pour l'instant. » | « Réessayer » *(après ~30 s de plus)* |
| 7 | Vitesse au-dessus du plafond | avertissement | « Trop vite : tes pas ne comptent pas. » | — |
| 8 | Verrou de vol actif, vol tenté | info | *« Cette tuile est à Alice. »* + *« Tu pourras la reprendre dans 1 min 12 s. »* | — |
| 9 | Connexion instable, **aucune coupure en cours** | info | « Connexion instable » | — |
| 10 | Arrière-plan refusé | avertissement | « Ta progression s'arrêtera si ton téléphone redémarre » | « Réglages » · « Masquer pour cette partie » |
| 11 | Notifications refusées | avertissement | « Arpendo ne peut pas t'avertir si la capture s'arrête. » | « Réglages » · « Masquer pour cette partie » |
| 12 | Mise à jour recommandée | info | « Une nouvelle version est disponible. » | « Mettre à jour » · « Fermer » |
| 13 | Captures perdues, au retour au premier plan | info | *« La coupure a duré trop longtemps : 12 captures sont perdues. »* | — *(disparaît seule après 6 s)* |

Notes de comportement :

- **Les conditions sont mutuellement exclusives**, et elles doivent le rester. Les entrées 4 et 5
  disent la **cause** pendant les cinq premières minutes de coupure ; l'entrée 6 dit la
  **conséquence** au-delà et prend la main sur les deux ; l'entrée 9 ne vaut que hors coupure.
- **Vérification opposable pour toute entrée ajoutée plus tard :** aucune condition ne doit pouvoir
  être vraie en même temps qu'une condition **plus prioritaire**, sauf le couple 1/2 ci-dessous qui
  est une exception écrite. Une condition qui est un sous-ensemble d'une condition mieux placée ne
  s'affiche jamais.
- **Priorité 2** : le texte change après le second refus, sinon le bouton « Réglages » semble ne
  rien faire (§9.3). C'est le seul couple d'entrées qui partage une condition logique, et
  l'exception est délibérée.
- **Priorités 7 et 8** : voir §7.3, elles sont transitoires et pilotées par l'événement.
- **Priorité 10 et 11** : « Masquer pour cette partie » est **par partie, jamais définitif**
  (§9.3). À la partie suivante, l'avertissement revient une fois.
- **Priorité 13** : c'est le seul bandeau à disparition automatique. Il n'a pas d'action possible.
- **Réévaluation** : les conditions 1, 2, 3, 10 et 11 sont recalculées **à chaque reprise du
  premier plan**. Android ne notifie aucun changement de permission ; sans cela le joueur autorise,
  revient, voit toujours le bandeau et conclut que l'app est cassée (§9.3).

**États du composant** — normal : affiché. Vide : aucun bandeau, la carte occupe la place libérée
avec une transition `motion-base` (jamais un saut). Chargement : sans objet. Erreur : sans objet,
le bandeau *est* l'affichage d'erreur. Désactivé : sans objet. Hors ligne : c'est son cas d'usage
principal.

### 2.5 La feuille modale — composant unique

**Rôle.** Support de tout contenu secondaire ouvert par-dessus un écran de fond : Partie (§7.4),
Paramètres (§8), Créer, Rejoindre, Choix de couleur, Tableau des scores.

**Anatomie.** Feuille glissante ancrée en bas, `radius-lg` sur les coins hauts, `elev-6`, voile
`scrim` derrière. Poignée de 32 × 4 dp centrée en haut, zone de saisie du geste de **48 dp de
haut**. **Deux points d'ancrage** : **mi-hauteur** (55 %) et **pleine** (92 % — jamais 100 %, la
bande de carte restante rappelle qu'on est au-dessus du jeu et donne une zone de fermeture au tap).
**Il n'existe pas d'ancrage replié** : une feuille est ouverte ou fermée, elle ne stationne jamais
en bas de l'écran.

**La barre de titre est optionnelle, feuille par feuille.** Les feuilles ouvertes depuis une action
nommée — « Créer une partie », « Rejoindre une partie », « Choisis ta couleur », le tableau des
scores — **portent leur titre**, parce que le joueur y arrive par un bouton et doit retrouver ce
qu'il a demandé. La feuille **Partie** (§7.4) n'en a pas : ses onglets se nomment eux-mêmes et son
nom accessible passe par `Semantics`. Une barre qui ne ferait que répéter le nom du composant coûte
48 dp de contenu pour zéro information.

**Fermeture** : glissement vers le bas, tap sur le voile, bouton retour Android. Les trois doivent
fonctionner. Une feuille qui ignore le bouton retour matériel est un défaut Android classique.

**Pourquoi une feuille et non une modale plein écran** — décision du §15, point 2. Détail et
justification en §7.4.

### 2.6 La modale de confirmation — composant unique

**Rôle.** Toute action irréversible : départ définitif (§4.4), suppression de compte (§12.2),
confirmation du pseudo (§5.1).

**Anatomie.** Boîte centrée, largeur `min(320 dp, écran − 2×space-4)`, `radius-md`, `elev-6`.
Titre `type-title`, corps `type-body`, actions **empilées verticalement** — jamais côte à côte :
deux boutons côte à côte de 48 dp sur 360 dp de large produisent des cibles étroites, et
l'alignement horizontal met l'action destructive à un pouce de l'annulation.

Ordre imposé, du haut vers le bas : **action destructive**, puis `space-12`, puis **« Annuler »**.
L'annulation est en bas parce qu'elle est dans la zone du pouce — c'est l'action qu'on veut rendre
facile.

**Paramètre `saisieRequise`** : quand il vaut vrai, l'action destructive reste **désactivée** tant
que le champ ne contient pas le mot attendu (§4.4). Le mot attendu est comparé sans tenir compte
de la casse ni des accents.

---

## 3. Palette joueur et rendu de la carte

### 3.1 Palette joueur — 10 couleurs, valeurs définitives

**Rôle.** Identifier un joueur sur la carte, dans la liste, dans le flux et dans le classement.
Justifie le plafond de 10 joueurs (§5.2).

La contrainte du cadrage est dure : distinguables sur une carte, **pour un daltonien** (8 % des
hommes). Les valeurs ci-dessous ne sont pas un choix esthétique, ce sont le résultat d'une
optimisation sous contrainte, **vérifiée par le validateur du skill `dataviz` en mode
`--pairs all`** — le mode explicitement destiné aux cartes, où **n'importe quelles deux couleurs
peuvent se toucher**, donc les 45 paires sont contrôlées et pas seulement les paires voisines.

| `color_id` | Nom (interne) | Hex | OKLCH (L, C) |
|---|---|---|---|
| 1 | rouge clair | `#E9878A` | 0.729 · 0.120 |
| 2 | brique | `#BD3216` | 0.529 · 0.180 |
| 3 | ocre | `#A6841D` | 0.629 · 0.120 |
| 4 | vert pomme | `#97C425` | 0.761 · 0.181 |
| 5 | émeraude | `#007559` | 0.500 · 0.100 |
| 6 | cyan | `#56C4CA` | 0.759 · 0.100 |
| 7 | bleu | `#3B6DF4` | 0.580 · 0.210 |
| 8 | lilas | `#BE85F9` | 0.720 · 0.171 |
| 9 | prune | `#773B95` | 0.470 · 0.149 |
| 10 | magenta | `#EB31A5` | 0.641 · 0.240 |

Rapport du validateur, fond de carte `#F2F0EB` *(valeur de `surface-dim` au moment de cette
mesure ; voir la note de revalidation après le rapport)* :

```
[PASS] Bande de clarté        les 10 dans L 0.43–0.77
[PASS] Plancher de chroma     les 10 >= 0.1
[PASS] Séparation daltonisme  pire paire (45) ΔE 9.1  — cible >= 8
[PASS] Plancher vision norm.  pire paire (45) ΔE 17.1 — plancher >= 15
[WARN] Contraste vs fond      4 couleurs sous 3:1 -> relief obligatoire
```

> **Séparation de l'accent.** Le même contrôle, rejoué avec `accent` `#123D1E` ajouté aux dix,
> laisse la pire paire inchangée à ΔE 17,1 : **l'accent est donc à plus de 17,1 de chacune des dix
> couleurs joueur.**

Deux conséquences portées dans le rendu :

- **Le `WARN` de contraste est traité par le contour d'hexagone** (§3.3). Quatre couleurs
  (`#E9878A`, `#97C425`, `#56C4CA`, `#BE85F9`) ne se détachent pas assez du fond clair : sans
  contour, une tuile capturée dans ces teintes ne se distingue pas d'une tuile neutre. Le contour
  est le « relief » que la méthode exige, et il sert deux fois — il marque aussi la limite entre
  deux territoires de teintes proches.
- **Niveaux de gris : la couleur ne suffit pas, et c'est normal.** Les clartés vont de 0.470 à
  0.761, avec des paires écartées de **0.002** (vert pomme / cyan) et **0.009** (rouge clair /
  lilas). En niveaux de gris ces paires sont indiscernables. La lisibilité en gris réclamée au
  §5.2 **est apportée par les motifs `pattern_id`**, pas par la palette — le cadrage a raison sur
  ce point, et ce chiffre est la preuve qu'il n'existe pas de palette de 10 qui s'en dispense.

**Attribution.** `color_id` est fixe pour toute la durée de la participation. La couleur suit
l'entité, jamais son rang au classement : un changement de classement ne repeint jamais la carte.
Une couleur libérée par un départ (§4.4) redevient disponible.

**Ordre d'affichage dans le sélecteur** : l'ordre du tableau, invariable. Un ordre qui change
entre deux parties empêche le joueur d'avoir « sa » couleur.

### 3.2 Style du fond de carte

**Rôle.** Support du jeu. Style minimaliste sans texte, façon Pokémon Go (§7.2).

**Décision :** **Mapbox Standard**, avec les libellés désactivés par configuration de style
(`showPlaceLabels`, `showRoadLabels`, `showPointOfInterestLabels`, `showTransitLabels` à faux),
et la couche hexagones insérée dans le **slot `bottom`**.

**Le mode sombre passe par le même canal.** Le style Standard expose
`lightPreset`, propriété de configuration de l'import de style au même titre que les quatre
`show*Labels` ci-dessus. Le client la pose à **`night`** quand le système est en mode sombre, à
**`day`** sinon, et la remet à jour au changement de mode sans recharger le style. Le coût est
d'une propriété, pas d'un style à maintenir.

**Repli si `lightPreset` n'est pas exposé côté Flutter** (à vérifier, §15.2) : le mode sombre
n'habille que le chrome et la carte reste en `day`, exactement le comportement d'origine. Dégradé,
jamais bloquant.

**La couche hexagones ne suit pas le preset.** Elle porte les couleurs joueur, à opacité pleine,
identiques dans les deux modes (§3.1) — un territoire ne change pas de propriétaire parce qu'il
fait nuit. Seuls le fond, les routes et l'eau s'assombrissent.

Pourquoi pas un style personnalisé : il faudrait le maintenir. Pourquoi le slot plutôt qu'un
identifiant de calque : le cadrage prévoit en §7.2 un identifiant de couche d'insertion en
configuration, avec un repli si introuvable. **Un slot répond mieux au même besoin** — c'est un
point d'ancrage nommé et stable, garanti par Mapbox à travers les mises à jour du style, là où un
identifiant de calque interne peut disparaître silencieusement. Le repli prévu par le cadrage
reste pertinent et devient : si le slot est refusé, insertion en haut de pile, et les routes
passent alors sous les hexagones — dégradé mais jouable.

Hiérarchie visuelle voulue (`mapbox-cartography`) :

| Rang | Élément | Traitement |
|---|---|---|
| 1 | Hexagones joueurs | Couleur franche, opaque |
| 2 | Marqueur du joueur | Le seul élément en volume |
| 3 | Routes et chemins | Formes uniquement, gris neutre, **au-dessus** des hexagones |
| 4 | Eau | Bleu-gris désaturé, **jamais une teinte de la palette joueur** |
| 5 | Bâti, usage du sol | Très faible contraste, quasi absent |

Contrainte de style à vérifier au réglage : **aucune couleur du fond de carte ne doit tomber à
moins de ΔE 15 d'une couleur joueur**. C'est le même plancher que le §3.1, appliqué au fond. La
couleur de l'eau est le risque principal, face au cyan `#56C4CA` et au bleu `#3B6DF4`.

**Cette vérification est à faire sur les deux presets.** `day` et `night` produisent deux fonds
différents, donc deux jeux de distances aux dix couleurs joueur. Le preset `night` déplace le
risque : l'eau sombre s'éloigne du cyan et du bleu, mais le fond de terre s'approche de l'émeraude
`#007559` et de la prune `#773B95`.

**États.** Normal : tel que décrit. Chargement : les tuiles Mapbox arrivent progressivement, comportement natif, rien à spécifier. Hors ligne : les tuiles en cache s'affichent, les zones non mises en cache restent au fond `surface-dim` — **la carte reste navigable, jamais bloquée** (§10.2). Erreur (jeton invalide, quota dépassé) : fond `surface-dim` + bandeau priorité 4. Vide, désactivé : sans objet.

### 3.3 La couche hexagones

**Rôle.** Le territoire. C'est l'élément central du jeu (§4.1, §7.1, §7.2).

**Implémentation retenue :** `GeoJsonSource` + `FillLayer` + `LineLayer` de contour, **pas des
annotations**. Les annotations passent chaque entité par un gestionnaire, ce qui ne tient pas à
l'échelle d'un viewport d'hexagones (`mapbox-flutter-patterns`). La couleur est pilotée par
expression, sur une propriété de l'entité :

```
fill-color: ['match', ['get', 'color_id'],
              1, '#E9878A', 2, '#BD3216', ... 10, '#EB31A5',
              '#C7C3B5']          // défaut : `outline` (§1.5), pour une donnée manquante
```

Une seule expression, une seule table de couleurs, alimentée par la même source que le reste de
l'interface — les pastilles de la liste des joueurs lisent la même table (DRY).

**Le contour.** `LineLayer` distinct, largeur **1 dp**, couleur `on-surface` `#1A1D18` à **25 %**
— une seule source de vérité, celle du §1.5 — sur les
mêmes entités. C'est le « relief » exigé par le §3.1. Il n'est **pas** dessiné entre deux tuiles
du même propriétaire — le territoire d'un joueur se lit comme une masse, pas comme un quadrillage.

**Les quatre états visuels :**

| État | Rendu | Origine |
|---|---|---|
| **Normal** | Remplissage opaque (`fill-opacity: 1`), contour 25 % | §7.2 |
| **Dézoomé** | Cellules parentes agrégées — voir ci-dessous | §7.1 |
| **Hors ligne > 5 min** | `fill-opacity: 0.6` **sur la couche hexagones seule**. Le fond de carte, les routes et le contour restent inchangés | §10 |
| **Carte masquée** | La couche n'existe pas — aucun widget Mapbox n'est instancié. Voir §13 | §9.3 |

L'opacité est **réservée au signal hors ligne**. Aucun autre état ne doit l'utiliser, sinon les
deux deviennent illisibles ensemble. C'est ce qui commande la décision d'agrégation ci-dessous.
Jamais de désaturation : deux joueurs aux teintes voisines deviendraient indistinguables, et c'est
précisément pendant une coupure qu'on regarde la carte (§10.2).

**Agrégation par cellules parentes au dézoom (§7.1) — décision.**

| Zoom | Résolution affichée | Source |
|---|---|---|
| ≥ 13 | H3 res. 10 — la tuile réelle | Requête viewport |
| 9 à 12 | **H3 res. 7** — la colonne parente dénormalisée (§13.6) | Requête viewport agrégée |
| < 9 | H3 res. 5 | Requête viewport agrégée |

Règle de rendu d'une cellule parente, en deux lignes et pas une de plus :

1. **Couleur du propriétaire majoritaire** parmi les enfants possédés. Égalité : le plus petit
   `color_id`, pour que le rendu soit déterministe et identique chez tous les joueurs.
2. **Neutre si moins de 5 % des enfants sont possédés.** Sans ce seuil, 3 tuiles sur 343 peignent
   une zone de 35 km² et la carte du monde devient un damier mensonger.

Alternatives écartées, et pourquoi : moduler l'opacité selon le taux de couverture entrerait en
collision avec le signal hors ligne ; mélanger les couleurs des propriétaires produirait des
teintes hors palette, donc non validées pour le daltonisme, et souvent proches d'une couleur
joueur existante.

**Animation de capture (§4.1) — décision.**

- **Remplissage radial de 300 ms** (`motion-map`) depuis le neutre — ou depuis la couleur de
  l'ancien propriétaire — vers la couleur du joueur. **Le remplissage part du point de contact du
  marqueur**, pas du centre de la tuile, et **ce n'est pas un fondu uniforme** : la couleur se
  répand depuis les pieds du joueur jusqu'aux six côtés. C'est mécaniquement vrai — la couleur
  vient de lui — et c'est ce qui distingue une capture d'un simple changement d'état.
  *Implémentation : voir le repli du §15.2 si `fill-color-transition` n'est pas exposé côté
  Flutter ; une couche éphémère animée depuis Dart rend le radial aussi bien, voire mieux.*
- **Pulsation du contour** : la largeur du contour de la seule tuile capturée passe de 1 à 3 dp
  puis revient, en 400 ms. Elle attire l'œil sans déplacer la caméra.
- **Un retour haptique léger** (`HapticFeedback.lightImpact`). C'est le seul retour perçu quand le
  téléphone est en poche et l'écran allumé dans la même seconde.
- **Jamais sur un lot.** À la reprise du réseau, ou au rejeu d'un trajet, plusieurs dizaines de
  tuiles changent d'état d'un coup : elles apparaissent **sans animation**. On n'anime que la tuile
  courante, celle sur laquelle le joueur se trouve. Animer un lot produit un feu d'artifice
  illisible et effondre le rendu sur un téléphone bas de gamme.

**États de la couche.** Vide : une partie neuve n'a aucune tuile — la couche existe, la source est
un `FeatureCollection` vide, et la carte est simplement celle du monde. Aucun message ; le vide est
l'état de départ normal et il est explicite par lui-même. Chargement : voir §14. Erreur de
chargement du viewport : la couche conserve les dernières données connues et le bandeau réseau
prend le relais — ne jamais vider la couche sur une erreur, on effacerait un territoire qui existe.

### 3.4 Marqueur du joueur et pastilles des autres

**Rôle.** Situer le joueur ; situer les autres uniquement via leur territoire (§5.2, §7.5).

- **Le joueur** : `LocationPuck3D`, modèle glTF, orienté selon le cap (§7.4). C'est le seul
  élément en volume de toute l'interface — c'est ce qui en fait un jeu et pas une carte.
  **Spécification complète du modèle en §3.4.1.**
- **Les autres joueurs** : **il n'y a pas de pastille de position.** Le cadrage est net : aucune
  position n'est jamais diffusée (§7.5). Les **pastilles colorées** représentent un joueur **dans
  les listes** (participants, flux, classement) : une pastille de 16 dp remplie de sa couleur, avec
  un contour de 1 dp à 25 %. **Aucun marqueur d'autre joueur n'apparaît sur la carte.**
- **Repli** : si le magnétomètre est absent ou incalibré, retour au nord sans casser le
  verrouillage (§7.4). Aucun message — c'est une dégradation que le joueur n'a pas à comprendre.

#### 3.4.1 Le modèle du marqueur — spécification

Le rendu SVG de référence est dans `03-identite-visuelle.md` §1.6.

**Silhouette.** Une **capsule verticale posée sur sa pointe arrondie**, proportions **1 : 1,7**
(largeur : hauteur). Aucun membre, aucun visage, aucune articulation — **rien à animer, donc rien
qui puisse mal s'animer**. Elle **flotte** à 0,25 fois sa hauteur au-dessus du sol et respire d'un
mouvement vertical de ±3 % sur un cycle de 2,4 s. Le flottement remplace la marche : c'est ce qui
permet de suivre les coordonnées GPS sans jamais avoir à poser un pied.

**Budget et matériau.**

| Aspect | Valeur |
|---|---|
| Triangles | **320 à 400**, une seule mesh fermée |
| Matériau | `KHR_materials_unlit` — aplat pur, aucun spéculaire, aucune normal map |
| Contour | *backface hull* : copie de la mesh à **+3 % d'échelle**, normales inversées, `#1A1D18` |
| Ombre portée | **aucune** |
| Disque de contact | ellipse aplatie `#1A1D18` à **18 %**, **sans flou**, ⌀ 20 px à l'écran |

Le contour par *backface hull* est indépendant de l'éclairage de la scène : c'est ce qui donne le
trait dessiné de la direction, et c'est ce qui rend le marqueur lisible sur n'importe quel fond.
Il double le nombre de triangles rendus — indolore à ce budget, à surveiller si le modèle
se complexifie.

**Répartition de la couleur joueur.**

| Zone | Traitement | Part |
|---|---|---|
| Coque haute | `surface` `#FDFBF6` | ~55 % |
| **Bandeau bas** | **couleur du joueur, aplat pur** | ~45 % |

**Pourquoi pas une teinte intégrale.** Le joueur se tient presque toujours **sur sa propre tuile,
donc sur sa propre couleur**. Un marqueur entièrement teinté disparaîtrait dans son propre
territoire à l'instant précis où on le regarde. La coque claire est l'invariant : elle est plus
claire que les dix couleurs joueur (L 0,98 contre 0,470–0,761), donc le contraste de clarté
fonctionne même sur la tuile de même teinte. La couleur est placée **en bas**, là où elle touche
visuellement la tuile.

**Lisibilité à 40 px** — trois mécanismes, tous indépendants de la teinte : la coque claire (rupture
de valeur garantie), le contour sombre continu (même principe que le contour d'hexagone du §3.3), et
le disque de contact (seconde rupture, et ancrage au sol). À 40 px, la silhouette occupe 24 × 40 px
et se distingue **à la forme avant même la couleur**.

**Teinture.** Le modèle est teinté **par instance**, par remplacement de la couleur de base du
matériau du bandeau. Cela lève par avance le risque signalé en §15.2 (« si le modèle n'est pas
teintable, il faut 10 fichiers glTF ») : un seul fichier suffit, et le repli à 10 fichiers reste
disponible si le SDK refuse la teinture d'instance.

**Point d'ancrage pour la personnalisation post-MVP.** Le sommet de la capsule est **plat sur 6 px
de diamètre** — imperceptible à l'œil, mais c'est une surface d'appui. Un accessoire futur
(chapeau, casque) s'y fixe par un nœud nommé **`socket_top`** dans le glTF, sans retoucher la mesh
de base. Le prévoir maintenant coûte une face ; le rétrofitter coûterait le modèle entier.
**Rien d'autre n'est livré au MVP** — aucun accessoire, aucun sélecteur.

---

## 4. Écran Connexion

**Rôle.** Authentifier via Google SSO uniquement, puis, à la première connexion, faire choisir le
pseudo définitif (§12.1, §5.1).

**Contenu et ergonomie.**

| Élément | Position | Taille |
|---|---|---|
| **Signe** — courbes de niveau refermées sur un hexagone | Centré, tiers haut | 96 dp de côté |
| **Logotype « Arpendo »** | Sous le signe, `space-3` d'écart | hauteur de capitale 24 dp |
| Accroche « prends du terrain » | Sous le nom, `space-2` d'écart, `type-body`, `on-surface-muted` | — |
| Bouton **« Se connecter avec Google »** | **Bande basse**, marge 16 dp, pleine largeur | 56 dp de haut |
| Lien « Politique de confidentialité » · « CGU » | Sous le bouton, `type-caption` | 48 dp de haut chacun |

Le bouton d'authentification est en bande basse parce que c'est la seule action de l'écran et
qu'elle est fréquente à la réinstallation. Les liens juridiques sont obligatoires (§13.12) et
volontairement discrets.

**Hiérarchie de la marque.** Le signe domine, le nom suit,
l'accroche est **discrète et subordonnée** : elle est en `type-body` et en `on-surface-muted`,
jamais à la taille du nom, jamais au-dessus de lui. Ce même bloc — signe, nom, accroche — sert
à l'identique sur l'**écran d'attente du démarrage** (§2.1) et sur l'**écran Accueil** (§5), pour que
les trois écrans sans carte partagent une seule composition. Les ressources SVG du signe et du
logotype sont livrées avec `03-identite-visuelle.md` §1.5.

**États du bouton de connexion.**

| État | Rendu |
|---|---|
| Normal | Bouton officiel Google, libellé « Se connecter avec Google » |
| Chargement | Libellé remplacé par un indicateur, bouton **désactivé**, le reste de l'écran reste actif |
| Erreur — annulation par l'utilisateur | Retour au normal, **aucun message** : il a annulé, il le sait |
| Erreur — réseau | Bandeau priorité 5, bouton réactivé |
| Erreur — refus serveur (compte `banned`, §12.6) | Modale : « Ce compte ne peut plus accéder au jeu. » + « Fermer ». Aucun détail, aucun recours dans l'app |
| Hors ligne | Bouton désactivé + bandeau priorité 5. Tenter une authentification hors ligne échoue toujours |
| Vide, désactivé | Sans objet |

### 4.1 Choix du pseudo — première connexion uniquement

**Rôle.** Le pseudo est unique mondialement et **définitivement immuable** (§5.1). Les garde-fous
sont exigés par le cadrage, pas optionnels.

**Ergonomie.** Écran plein (pas une modale) : c'est une étape du parcours d'inscription, pas une
digression, et le clavier occupera la moitié de l'écran. Champ en bande médiane haute pour rester
visible clavier ouvert ; bouton d'action collé au-dessus du clavier.

| Élément | Spécification |
|---|---|
| Titre | « Choisis ton pseudo » — `type-title` |
| Sous-titre | « Il sera visible par les autres joueurs. » — `type-body`, `on-surface-muted` |
| Champ | 56 dp de haut, `radius-sm`, autofocus, `textCapitalization: none` |
| Compteur | *« 7 / 16 »* aligné à droite sous le champ, `type-caption` |
| Bouton | « Continuer » — 56 dp, pleine largeur, désactivé tant que le pseudo n'est pas valide **et** disponible |

**États du champ**, tous distincts visuellement **et** textuellement :

| État | Icône | Message |
|---|---|---|
| Vide (départ) | — | « 3 à 16 caractères, lettres, chiffres, tiret et souligné. » |
| Saisie en cours (< 400 ms d'inactivité) | — | Message d'aide maintenu |
| Vérification | indicateur | « Vérification… » |
| Format invalide | ✕ `danger` | « Pas de *é* dans un pseudo. » / « Il faut au moins 3 caractères. » |
| Refusé par le filtre | ✕ `danger` | « Ce pseudo n'est pas autorisé. » — **jamais de détail**, sinon le filtre devient un jeu |
| Déjà pris | ✕ `danger` | « *Alex* est déjà pris. » |
| Disponible | ✓ `accent` | « *Alex* est disponible. » — `accent`, jamais `#007559` : c'est la couleur joueur n° 5 (§1.5) |
| Erreur réseau | ⚠ `warning` | « Le serveur ne répond pas. » + « Réessayer » |
| Hors ligne | ⚠ | Bouton « Continuer » désactivé — on ne peut pas réserver un pseudo unique hors ligne |

La vérification de disponibilité (§5.1) est déclenchée **400 ms après la dernière frappe**, jamais
à chaque caractère.

**Confirmation.** Modale de confirmation (§2.6), `saisieRequise: false` :

> **Titre** — « Ce pseudo sera définitif »
> **Corps** — « Tu ne pourras plus changer *Alex*. Vérifie l'orthographe. »
> **Action** — « Garder ce pseudo »
> **Annuler** — « Modifier »

C'est le garde-fou exigé au §5.1 : sans lui, une faute de frappe est irréparable autrement que par
suppression de compte.

---

## 5. Écran Accueil

> **Un seul écran, deux blocs.** Créer et Rejoindre ne sont pas deux feuilles : ce sont **deux
> blocs de cet écran**, spécifiés en §5.1 et §5.2. Le minimalisme visé porte sur le **nombre de
> pages**, pas sur la densité d'une page.

**Rôle.** Rejoindre une partie existante ou en créer une. Visible uniquement si aucune partie
n'est active (§8.3).

**Ergonomie**, de haut en bas :

| Élément | Position | Taille de cible |
|---|---|---|
| Icône **Paramètres** | Haut à droite, dans la barre de titre | 48 dp |
| Signe + **« Arpendo »** + accroche « prends du terrain » | Centré, bande haute — même composition qu'au §4 | — |
| **Bloc « Rejoindre »** — champ code + bouton | Bande médiane (§5.2) | 56 dp |
| Séparateur **« ou »** | Filet horizontal avec le mot centré | — |
| **Bloc « Créer »** — sélecteur de durée + bouton | Bande basse (§5.1) | 56 dp |

**Rejoindre est au-dessus de Créer**, et c'est délibéré : le bloc « Créer » porte un curseur et son
encart d'information, donc il est plus haut ; le mettre en bas met **les deux boutons d'action dans
la zone du pouce**, là où l'ordre inverse repousserait « Rejoindre » hors d'atteinte.

**Le comportement au clavier.** L'Accueil est un **écran de fond** qui porte un champ de saisie en
bande médiane, avec un curseur et un bouton d'action en dessous. Ce n'est pas une feuille modale,
donc la règle `viewInsets.bottom` du §2.3 ne suffit pas — et un clavier Android occupe environ
300 dp sur les 800 de l'écran de référence.

**Règle retenue : le contenu défile, il ne se réorganise pas.**

| Aspect | Décision |
|---|---|
| Structure | Colonne unique dans un défilement, avec `resizeToAvoidBottomInset: true` |
| À l'ouverture du clavier | Le bloc **Rejoindre** est amené en vue, champ **et** bouton visibles ensemble — un champ visible dont le bouton ne l'est pas est le défaut du §2.3 |
| Rembourrage bas | `MediaQuery.viewInsets.bottom` **et** `MediaQuery.padding.bottom`, comme au §2.3 |
| Le bloc marque (signe, nom, accroche) | **Défile hors de l'écran.** Il est décoratif ; lui garder sa place volerait celle du champ |
| Le bloc **Créer** | Reste en place dans le flux, atteignable par défilement clavier ouvert. **Il ne remonte pas** au-dessus du clavier : deux actions concurrentes à portée du pouce pendant une saisie, c'est une erreur de tap |
| À la fermeture du clavier | Retour à la disposition de repos, sans saut : `motion-base` |

**Pourquoi pas la solution du §4.1** (champ en bande médiane haute, bouton collé au-dessus du
clavier) : l'écran pseudo ne porte **qu'une** action, donc coller son bouton au clavier est sans
ambiguïté. L'Accueil en porte **deux**, dont une irréversible ; les coller ensemble au-dessus du
clavier les met à un pouce l'une de l'autre.

**Aucun lien juridique sur cet écran.** « Politique de confidentialité » et « Conditions
d'utilisation » vivent sur l'écran Connexion (§4) et dans la modale Paramètres (§8) — deux endroits
suffisent, et l'Accueil est déjà dense.

**États de l'écran.** Normal : ci-dessus. Vide, désactivé : sans objet. Chargement : sans objet, on
n'arrive ici qu'après avoir su qu'aucune partie n'est active. Erreur / hors ligne : les deux
actions restent **actives** ; l'échec se manifeste au moment de l'action, avec un message précis,
plutôt que par deux boutons grisés sans explication.

> **Aucun des deux boutons n'est jamais grisé pour cause de réseau.** Un bouton désactivé n'apprend
> rien : il laisse le joueur chercher ce qu'il a mal fait. L'échec se dit au moment de l'action,
> avec son motif. Les états de §5.1 et §5.2 appliquent cette règle.

### 5.1 Bloc « Créer une partie »

**Rôle.** Choisir la durée, qui fige tout le reste : `ends_at`, le verrou de vol, la fréquence des
bilans du flux (§8.2, §4.2, §11.5).

**Contenu.**

- Intitulé de bloc « Créer une partie ».
- **Sélecteur de durée à 8 paliers fixes** — voir ci-dessous.
- Encart d'information, `type-caption`, qui se met à jour avec la durée :
  *« La partie démarre tout de suite et se termine le 14 août à 18 h 42. Tu peux voler une tuile toutes les 2 min. »*
  Cet encart est ce qui rend intelligible une décision que le joueur ne peut plus modifier ensuite.
- Bouton « Créer une partie » — 56 dp, pleine largeur, bas de bloc.

**Le sélecteur de durée — un curseur à huit crans.**

**Ce qu'un curseur doit compenser ici.** Les huit valeurs — 30 min / 1 h / 2 h / 4 h / 24 h / 48 h /
1 semaine / 1 mois — sont **discrètes et non linéaires** : entre deux crans, l'écart va de trente
minutes à vingt-deux jours. Un rail continu suggère un continuum qui n'existe pas, et huit crans
sur 328 dp donnent des zones d'environ 47 dp, donc un geste de glissement peu précis. Quatre règles
rendent le curseur aussi sûr qu'une grille de puces :

| Règle | Valeur |
|---|---|
| **Zone tactile de la poignée** | **48 × 48 dp**, quelle que soit la taille dessinée. La poignée visible fait 22 dp ; sa zone de saisie est étendue autour du dessin, ce que le §1.4 autorise explicitement |
| **Hauteur de la ligne du curseur** | **48 dp au minimum**, rail compris. C'est la ligne entière qui est saisissable, pas seulement la poignée |
| **Aimantation stricte** | Le curseur **ne prend que les huit valeurs**. Aucune position intermédiaire n'existe, ni pendant le glissement ni après le relâchement |
| **Tap sur le rail** | Un tap n'importe où sur le rail saute au cran le plus proche. C'est ce qui rend les huit valeurs atteignables **sans glisser**, et donc ce qui remplace vraiment la grille |

**Trois éléments de lecture, non négociables** — sans eux le curseur redevient un objet imprécis :

1. **Les huit crans sont dessinés** sur le rail, en `outline`, celui qui est sélectionné en
   `accent`. C'est ce qui dit que les valeurs sont discrètes.
2. **La valeur courante est affichée en clair**, en `type-body` graisse 500, au-dessus du rail et
   alignée à droite du libellé « Durée de la partie ». **C'est elle qui porte l'information, pas la
   position de la poignée.**
3. **Les deux extrémités sont étiquetées** — « 30 min » à gauche, « 1 mois » à droite, en
   `type-caption`, `on-surface-muted`. Elles donnent l'amplitude sans encombrer.

**Accessibilité.** Le composant expose une sémantique de curseur **à valeurs discrètes**, avec la
valeur courante annoncée sous forme de texte (« 24 heures »), pas d'index. Les huit valeurs sont
atteignables au clavier et aux services d'accessibilité.

**Le risque résiduel, assumé.** Glisser d'un cran à l'autre reste moins précis que taper une puce,
et l'écart entre « 48 h » et « 1 semaine » est de cinq jours. **C'est l'affichage en clair de la
valeur courante qui rattrape ce risque** : le joueur lit ce qu'il a choisi avant de valider, et
l'encart d'information ci-dessus lui donne la date de fin en toutes lettres.

**États.** Normal : un palier présélectionné — **« 24 h »**, la valeur médiane et le cas d'usage
décrit au §2 du cadrage (des joueurs à distance qui ne se croisent pas). Chargement : après le tap
sur « Créer une partie », le bouton passe en indicateur et l'écran reste en place — on ne quitte
pas un écran sur une action non confirmée. Erreur réseau : bandeau, bouton réactivé.
Hors ligne : le bouton **reste actif** ; au tap, il passe en indicateur, échoue, et le message
« Pas de réseau. La partie n'est pas créée. » s'affiche sous le bouton, qui redevient
actif. La durée choisie est conservée. Vide : sans objet.

### 5.2 Bloc « Rejoindre une partie »

**Contenu.** Intitulé de bloc « Rejoindre une partie » · champ code (§1.7) · bouton « Rejoindre ».

**Le champ code est le premier élément tappable de l'écran.** Un joueur qui arrive avec un code
n'a rien à chercher.

**États du champ.**

| État | Message |
|---|---|
| Vide | « Saisis le code à 6 caractères. » |
| Incomplet | Bouton désactivé, aucun message — inutile de gronder quelqu'un qui est en train de taper |
| Complet | Bouton actif |
| Vérification | Bouton en indicateur |
| Code inconnu | « Ce code n'existe pas. » |
| Partie terminée | « Cette partie est terminée. » |
| Partie complète (10 joueurs) | « Cette partie a déjà 10 joueurs. » |
| Déjà dans une partie | « Tu es déjà dans une partie. » — cas de course : ne peut se produire que sur deux appareils |
| Erreur réseau | Bandeau priorité 4, bouton réactivé |
| Hors ligne | Bouton **actif**. Au tap : indicateur, échec, puis « Pas de réseau. Le code n'est pas vérifié. » sous le champ. Le code saisi est conservé |

Quatre messages d'échec distincts, pas un seul générique. Un code refusé sans motif conduit le
joueur à le retaper indéfiniment.

### 5.3 Choix de la couleur

**Rôle.** Étape commune à la création et à la participation (§5.2). La couleur se choisit au
moment d'entrer dans une partie, pas à la création du compte.

**Ergonomie.** Grille **5 colonnes × 2 lignes**, pastilles de **56 dp** avec `space-2` d'écart —
la largeur consommée est de 5×56 + 4×8 = 312 dp, ce qui tient dans 360 dp avec les marges. La
grille est en bande basse ; le bouton de validation sous elle.

**États d'une pastille.**

| État | Rendu |
|---|---|
| Disponible | Disque plein, contour 1 dp à 25 % |
| **Sélectionnée** | Contour 3 dp `on-surface` **+ coche** au centre — jamais la couleur seule |
| **Prise** | Disque à 30 % d'opacité, **barré d'une diagonale**, non tappable, `Semantics(enabled: false)` |
| Chargement | Grille en squelette pendant la lecture des couleurs libres |
| Erreur | « Les couleurs disponibles ne sont pas arrivées. » + « Réessayer » |

**Aperçu.** Au-dessus de la grille, un aperçu de **96 dp** montrant un petit fragment de carte avec
trois hexagones dans la couleur choisie. Il montre ce que le joueur va réellement voir, ce qu'une
pastille isolée ne fait pas — deux couleurs proches se distinguent mieux en aplat qu'en disque.

**Textes.** Titre « Choisis ta couleur » · bouton « Entrer dans la partie ».

**Deux cas de course, et ce sont deux cas distincts.** Le serveur est autoritaire, le client ne
réserve rien : entre l'affichage de la grille et la validation, l'état peut avoir changé.

| Ce qui a changé | Ce qui s'affiche | Où l'on se retrouve |
|---|---|---|
| **Ma couleur a été prise, d'autres restent libres** — le cas courant, deux joueurs qui rejoignent depuis le même canapé | La pastille concernée bascule en état **Prise** avec sa transition `motion-fast`, un message en ligne sous la grille : *« Cette couleur vient d'être prise. Choisis-en une autre. »*, et le bouton « Entrer dans la partie » redevient **inactif** | **La feuille reste ouverte**, la grille est rafraîchie, aucune sélection n'est faite à ma place |
| **Toutes les couleurs sont prises** — la partie est pleine, donc à 10 joueurs | « Cette partie a déjà 10 joueurs. » | La feuille **se ferme**, retour à l'Accueil |

**Aucune couleur n'est présélectionnée à ma place** dans le premier cas. Choisir pour le joueur
au moment où on lui retire son choix est la manière la plus sûre de lui faire valider une couleur
qu'il n'a pas voulue — et `color_id` est fixe pour toute la partie (§3.1).

**La grille est rafraîchie à l'ouverture de la feuille et au retour au premier plan**, jamais en
souscription continue : une pastille qui s'éteint sous le doigt au moment du tap est pire que
l'échec à la validation.

---

## 6. Entrée en partie — l'avertissement de sécurité

**Rôle.** Avertir sur la conduite dans la rue avant que le joueur s'engage. Il précède le choix de
la couleur.

**Ordre retenu — décision (§15, point 10).** Modale d'entrée → choix de la couleur → carte. On
consent **avant** de s'engager : une fois la couleur choisie, le joueur se considère dans la partie,
et un avertissement qui arriverait après serait lu comme une formalité à balayer.

**Forme.** **Une feuille modale** (§2.5) en pleine hauteur, pas un écran. Elle appartient au
parcours d'entrée en partie, qui se déroule par-dessus l'Accueil.

> **Titre** — « Joue prudemment »
>
> **Corps** — « Arpendo se joue dans la rue. Regarde autour de toi, pas ton téléphone. Ne joue pas
> au volant. Certains lieux ne sont pas des terrains de jeu : respecte les propriétés privées, les
> établissements scolaires et les lieux de soin. »
>
> **Lien** — « Lire les conditions d'utilisation »
> **Action** — « J'ai compris »

Le §16 du cadrage exige cet avertissement sans en écrire le texte ; il est arrêté ici.

**Fréquence.** **Une fois par compte.** Cet avertissement porte sur la personne et sa conduite dans
la rue, pas sur une partie donnée. Le répéter à chaque entrée le transformerait en obstacle à
balayer, ce qui détruirait sa fonction.

### 6.1 La visibilité des zones — portée par les documents juridiques

**Aucune modale n'annonce ce que les autres joueurs voient.** L'information vit dans les conditions
d'utilisation et la politique de confidentialité, pas dans le parcours d'entrée en partie. Trois
obligations en découlent :

1. **Le cadrage §16 exige une mention explicite dans les documents juridiques**, pas à l'entrée en
   partie.
2. **La politique de confidentialité et les CGU (cadrage §13.12) couvrent explicitement deux
   choses** : que les autres joueurs voient **les zones capturées**, et qu'ils voient **le moment**
   de la capture.
3. **Le lien « Lire les conditions d'utilisation » de la modale de sécurité est le seul chemin
   d'information dans le parcours.** Il n'est pas décoratif et ne peut pas être retiré.

**Ce que ça coûte, et qui est assumé.** Le §4.4 — le départ définitif qui neutralise ses tuiles —
existe pour le joueur qui perd confiance dans le groupe. Un joueur qui n'a jamais lu les CGU
ignorera que ses zones sont visibles, donc ne pensera pas à s'en servir. La compensation partielle
est la ligne de réassurance en pied de la liste des joueurs (§7.4) : *« Le classement se met à jour
à chaque capture. Personne ne voit la position de personne. »* Elle dit ce qui n'est **pas** vu ;
elle ne dit pas ce qui l'est.

**États.** Normal uniquement. Cette feuille n'est **pas** annulable : ni bouton retour, ni
glissement, ni tap sur le voile. Elle n'a qu'une sortie, et c'est la seule exception à la règle de
fermeture du §2.5 — justifiée parce qu'un avertissement esquivé n'a pas été donné.

---

## 7. Écran Jeu

Écran central. La carte est **le jeu** et **la surface tactile principale**. Toute la conception
qui suit découle de là : chaque contrôle posé sur la carte vole des pixels et des gestes.

### 7.0 Inventaire des éléments persistants — et ce qui a été retiré

| Élément | Position | Persistant ? |
|---|---|---|
| **Puces de header** (identité + score à gauche, timer à droite) — **inertes, aucune cible tactile** | Haut, 40 dp, flottantes | Oui — **surfaces d'affichage, pas des contrôles** (§7.1) |
| Bandeau | Sous le header | Conditionnel, un seul (§2.4) |
| **Pile d'activité** | Bas gauche, 32 dp du bas | Oui — **surface d'affichage, pas un contrôle** (§7.2.1) |
| Bouton « Recentrer » | Bas droite, 96 dp du bas | **Conditionnel** — visible ⇔ caméra libre (§7.3) |
| **Bouton d'action « Partie »** | Bas droite, 32 dp du bas | Oui — ouvre la feuille Partie (§7.4) |
| Carte | Tout le reste | Oui |

**Deux contrôles permanents au-dessus de la carte, et un troisième conditionnel. C'est un
plafond, pas un état de fait.** Les puces de header et la pile d'activité n'entrent pas dans ce
compte : elles ne consomment aucun geste. Sur 360 dp de large, six boutons de 56 dp occupent une colonne
entière et interceptent les gestes de déplacement de la carte — exactement le geste dont dépend le
mode caméra libre (§7.3). Tout ce qui pourrait vouloir un bouton flottant est donc logé ailleurs :

| Fonction | Où elle vit |
|---|---|
| Paramètres | **Bout de la barre d'onglets de la feuille Partie** (§7.4) |
| Inviter | **Onglet** de la feuille Partie (§7.4) |
| Liste des joueurs | **Onglet** de la feuille Partie |
| Flux d'activité | **Pile d'activité** en bas gauche de la carte, plus une modale au tap (§7.2.1, §7.2.2) |
| Quitter la partie | **Bloc « Cette partie » de la modale Paramètres** (§8), hors de la zone du pouce |
| Code de la partie | **Onglet Inviter uniquement** |
| Compte à rebours du verrou de vol | **Bandeau réactif** (§7.3) |
| Indicateur de vitesse | **Même bandeau réactif** (§7.3) |

**Toute fonction ajoutée plus tard passe par ce tableau, jamais par un bouton de plus.**

### 7.1 Header — deux puces flottantes

**Rôle.** Porter en permanence l'état du joueur, **sans rien retirer à la carte**. Absent du §15 du cadrage, mais rendu nécessaire
par §4.1 (score à l'instant T), §8.2 (timer) et §5.2 (identité visuelle du joueur).

**Le header n'est pas une barre : ce sont deux puces flottantes.** Une barre pleine largeur de
56 dp coupe la carte d'un trait horizontal sur toute sa largeur, et ne peut pas être remplie — le
contenu du header fait ~300 dp pour 360, donc **une soixantaine de dp reste vide quoi qu'on fasse**.
Répartir ce vide ne le supprime pas : à gauche il devient une marge de fin, au milieu un trou, aux
deux extrémités deux demi-trous. **Supprimer la barre le supprime**, parce que l'espace redevient
de la carte — et la carte est le jeu (§2.2).

| Puce | Contenu | Largeur |
|---|---|---|
| **Identité + score**, ancrée à **gauche** | Hexagone 20 dp dans la couleur du joueur · `space-2` · « 124 hex · 12 400 pts » | épouse son contenu, ≈ **218 dp** |
| **Temps restant**, ancrée à **droite** | Le timer seul | épouse son contenu, ≈ **82 dp** |

**Traitement commun aux deux.** Hauteur **40 dp**, rembourrage horizontal `space-3`, **`radius-md`**,
fond `surface` **opaque**, `elev-1`, plus le **contour de 1 dp** qu'impose le §1.3 à tout élément
flottant au-dessus de la carte.

**`radius-md` et non `radius-full`.** Le §1.3 réserve `radius-full` à ce qui est **rond par nature**
— pastille de delta, bouton d'action, pastille d'alerte — et donne `radius-md` à ce qui est une
**surface de contenu** : carte, bandeau. Les puces portent du texte sur plusieurs valeurs : ce sont
des surfaces de contenu. En pilule, elles se lisaient comme des jetons flottants sans rapport avec
le bandeau (§2.4) qui apparaît juste dessous, et qui est en `radius-md` : deux vocabulaires de
forme empilés à 8 dp d'écart sur le même bord d'écran. **Aucune transparence, aucun flou** : les contrastes du §1.5 ne
valent que sur fond opaque, et un `BackdropFilter` au-dessus d'une surface Mapbox se repeint en
continu. Marge de 16 dp par rapport aux bords et à la safe area haute.

**Chaque puce épouse son contenu, donc rien ne dérive.** C'est la raison de fond, et elle interdit
deux dispositions qui semblent plus jolies :

- **Un score centré dérive en permanence.** Sa largeur change à chaque chiffre gagné ou perdu —
  « 124 hex » puis « 1 247 hex », « 12 400 pts » puis « 124 700 pts ». Centré, c'est le bloc entier
  qui se décale, et sur une valeur qui se met à jour en continu. Le §1.2 impose les chiffres
  tabulaires précisément pour que le score ne danse pas ; le centrer réintroduit la danse un cran
  plus haut.
- **Un score centré *entre* deux ancres dérive une seconde fois**, parce que le timer change de
  largeur lui aussi : il a **cinq formats** (« 27 j », « 2 j 04 h », « 18 h », « 1 h 12 »,
  « 09:47 »). Chaque bascule de format déplacerait le score — au moment précis où le joueur
  regarde l'écran parce que la fin approche.

Ancrées chacune à son bord, les deux puces ne bougent jamais : celle de gauche grandit vers la
droite, celle de droite vers la gauche, et l'écart entre elles est de la carte.

```
     ┌──────────────────────────────┐      ┌───────────┐
     │ ⬢  124 hex · 12 400 pts      │      │  2 j 04 h │
     └──────────────────────────────┘      └───────────┘
      └───────── ≈ 218 dp ──────────┘  ↑    └─ ≈ 82 dp ┘
                     ▲              la carte
      la pastille de delta se superpose
      ici, calée sur le bord droit intérieur
```

**Ce que ça change au budget vertical.** La carte **court sous les puces** jusqu'à la safe area
haute : elle n'est plus amputée de 56 dp sur toute sa largeur. L'occultation réelle passe de
**360 × 56 = 20 160 dp²** à **300 × 40 = 12 000 dp²**, et surtout elle cesse d'être un trait qui
traverse l'écran. Comme pour la pile d'activité (§7.2.1), **c'est une occultation, pas une
réduction** : le §2.2 ne décompte plus le header de la hauteur disponible, et dit ce qu'il occulte.

| Où | Contenu | Type |
|---|---|---|
| Puce gauche, en tête | Hexagone 20 dp plein dans la couleur du joueur, contour 1 dp | — |
| Puce gauche, après `space-2` | **« 124 hex · 12 400 pts »** | `type-headline` pour le nombre, `type-caption` pour les unités |
| Puce droite | Temps restant | `type-label`, `on-surface-muted` |
| Puce gauche, superposée | Pastille de delta, transitoire, calée sur le bord droit **intérieur** — **elle n'occupe aucune largeur propre** (§ « Le score vivant », point 3) | `type-label` |

**Les deux puces ne portent aucune cible tactile.** Elles sont **entièrement inertes** : de
l'information à lire, rien à toucher, et elles ne se réclament d'aucune des deux exceptions que le
§1.4 accorde à cette bande. Elles sont donc en `IgnorePointer` — le glissement de carte les
traverse, exactement comme la pile d'activité (§7.2.1) — **et elles restent dans l'arbre
d'accessibilité**, avec un `Semantics`
explicite posé en dehors de l'`IgnorePointer`. L'accès aux Paramètres passe par la barre d'onglets
de la feuille Partie (§7.4).

**Le score vivant — traitement (§4.1).** Le cadrage exige que l'interface montre que le score est
*vivant*, pas *acquis*, sinon la baisse passera pour un bug. Quatre décisions, aucune décorative :

1. **Le nombre d'hexagones est affiché avant les points, et jamais séparément.** C'est le levier
   principal. « 12 400 points » se lit comme un cumul acquis ; « 124 hex » se lit comme une
   possession, et une possession, ça se perd. Les points ne sont que 100 × la première valeur — les
   montrer ensemble enseigne la règle sans un mot d'explication.
2. **Hausse et baisse ont exactement le même traitement.** Même durée, même emplacement, même
   taille. Un delta discret à la baisse enseignerait que la baisse est anormale.
3. **La pastille de delta est une surimpression, pas un élément de la ligne.** Elle apparaît à
   chaque variation, `radius-full`, pendant 3 s :
   *« ↑ +300 »* ou *« ↓ −200 »*. Elle est posée **par-dessus le bloc de score**, alignée sur son
   bord droit, et **ne consomme aucune largeur** : le header ne se réorganise pas quand elle
   apparaît, et sa disparition ne fait rien bouger. C'est ce qui rend l'arithmétique du repli
   ci-dessous tenable — voir « La largeur, mesurée ».

   Entrée : fondu plus translation de 4 dp vers le haut, `motion-fast`. Sortie : fondu,
   `motion-fast` à 75 % (§1.6). Pendant les 3 s d'affichage, le score reste lisible **sous** la
   pastille sur toute la partie qu'elle ne couvre pas ; elle est calée à droite précisément parce
   que c'est le chiffre des points, secondaire, qu'elle peut masquer — **jamais le nombre de
   tuiles**, qui est la valeur principale (point 1).

   **La direction est portée par la flèche et le signe**, jamais par la couleur. Le fond est
   **neutre dans les deux sens** — `surface-dim`, texte `on-surface` — ce qui applique le point 2
   ci-dessus à la lettre. **Aucun vert ici** : le seul vert disponible à cette clarté serait une
   couleur joueur, et le joueur qui la porte verrait sa pastille d'identité et sa pastille de gain
   dans la même teinte, à 40 dp l'une de l'autre. Voir §1.5, sur l'absence de jeton `success`.
4. **Le bilan de retour** : au retour au premier plan après plus de 15 minutes d'absence, la
   pastille affiche une fois, pendant 6 s : *« Pendant ton absence : ↓ −4 hex »*. C'est le moment
   exact où la baisse serait prise pour un bug — le joueur rouvre l'app et voit un chiffre plus
   petit qu'à la fermeture. Rien à cet instant, et le doute s'installe pour toute la partie.

C'est le **même composant** que le message de captures perdues du §10.3, avec un texte différent.
Si les deux sont vrais au même instant, le bilan de score passe en premier et les captures perdues
prennent le bandeau priorité 13 — la cause y est, l'effet ici.

**Le timer.** Format adaptatif, couvrant toute l'amplitude de 30 min à 1 mois :

| Restant | Format | Exemple |
|---|---|---|
| **> 7 j** | jours seuls | *« 27 j »* |
| **48 h à 7 j** | jours + heures | *« 2 j 04 h »* |
| **2 h à 48 h** | heures seules | *« 18 h »* |
| 10 min à 2 h | heures + minutes | *« 1 h 12 »* |
| < 10 min | minutes + secondes, **rafraîchi à la seconde**, en `warning` | *« 09:47 »* |
| Écoulé | — | *« Terminée »* en attendant la clôture serveur |

Au-dessus de 10 minutes, le timer se rafraîchit **à la minute**. Un compte à rebours à la seconde
pendant un mois n'informe personne et empêche l'écran de se mettre en veille de rendu.

**Le repli aux grandes tailles de police.**

Le §1.2 exige de suivre le réglage système jusqu'à **200 %** sans troncature.

**La largeur, mesurée.** Sur l'écran de référence de 360 dp, à `textScaler` 1,0, la pastille de
delta étant une **surimpression** qui ne consomme aucune largeur :

| Élément | Largeur |
|---|---|
| Marge gauche (`space-4`) | 16 |
| **Puce identité + score** — `space-3` + hexagone 20 + `space-2` + texte ≈ 162 + `space-3` | ≈ 218 |
| **Écart entre les deux puces — de la carte** | ≈ 28 |
| **Puce timer** — `space-3` + texte ≈ 58 + `space-3` | ≈ 82 |
| Marge droite (`space-4`) | 16 |
| **Total** | **360 dp, exactement** |

**Il ne reste que ~28 dp d'écart entre les deux puces**, et ce n'est plus un vide : c'est de la
carte, au même titre que le reste de l'écran. Deux décisions rendent cet écart possible, chacune
valant une trentaine de dp : les puces **ne portent aucune cible tactile**, et la pastille de delta
est une **surimpression** sans largeur propre. Retirer l'une des deux ferait se toucher les deux
puces dès les premiers crans du réglage de police.

Seuls les deux blocs de texte suivent ce réglage — l'hexagone reste à 20 dp, les rembourrages
aussi. Cela fait **220 dp de texte pour 28 dp d'écart**, soit un contact à partir de **≈ 1,12**.

Règle de repli :

| `MediaQuery.textScaler` | Rendu | Hauteur occupée |
|---|---|---|
| **≤ 1,1** | **Deux puces côte à côte**, telles que décrites ci-dessus | **40 dp** |
| **> 1,1** | **Les puces s'empilent.** La puce timer passe **sous** la puce score, ancrée au même bord gauche, `space-2` entre les deux. Chacune continue d'épouser son contenu | **88 dp** |
| **Débordement résiduel** aux échelles extrêmes | Les **points** passent en seconde ligne **à l'intérieur de la puce score**, qui grandit en hauteur. **Le nombre de tuiles ne quitte jamais la première ligne** | 88 dp et plus |

**Les puces s'empilent à gauche, pas en diagonale.** Une puce ancrée à droite et l'autre à gauche,
sur deux lignes, produit un escalier que rien ne justifie. Empilées au même bord, elles se lisent
comme un bloc unique — et le bord gauche est celui du sens de lecture.

> **Le seuil de 1,1 est calculé sur le tableau ci-dessus, pas choisi.** Il est à revérifier sur les
> métriques réelles de Roboto avant de figer le composant — c'est inscrit au §15.2. Le seuil est bas
> parce que l'écart entre les puces est mince : c'est le prix d'une carte qui court dessous, et il
> se paie par un empilement qui reste lisible, pas par une troncature.

**Trois choses que ce repli refuse de faire, et pourquoi.**

1. **Aucun `FittedBox`, aucune réduction de taille.** Rapetisser le texte pour le faire entrer
   annule le réglage d'accessibilité que l'utilisateur a délibérément posé, et franchit le plancher
   de 12 dp du §1.2. C'est la solution la plus simple à coder et la seule qui soit inacceptable.
2. **Les unités « hex » et « pts » ne disparaissent pas.** Elles portent la pédagogie du §7.1 —
   « 124 hex » se lit comme une possession, donc comme quelque chose qui se perd. Les retirer
   économiserait de la place en détruisant ce que le header est censé enseigner.
3. **Le nombre de tuiles ne descend jamais en ligne 2.** C'est la valeur principale ; elle reste
   en tête de lecture quelle que soit l'échelle.

**Ce que ça coûte, et c'est assumé.** Empilées, les puces occultent **88 dp** de haut au lieu de 40,
sur leur seule largeur. La carte n'est pas amputée pour autant — elle court toujours dessous — mais
la zone illisible double. C'est le prix d'un réglage d'accessibilité que l'utilisateur a
délibérément posé, et il vaut mieux que tronquer du texte, ce que le §1.2 interdit.

**États des puces.** Normal : ci-dessus. Chargement (première entrée, score non encore reçu) :
« — hex · — pts », **jamais 0** — un zéro affiché est une information fausse. Erreur / hors ligne :
les valeurs restent affichées, figées, et le bandeau porte l'explication ; le header ne devient
jamais gris, il n'y a rien de faux dedans, juste du périmé. Vide, désactivé : sans objet.

### 7.2 Contrôles flottants sur la carte

**Bouton « Recentrer »** — §7.3 du cadrage.

| Aspect | Décision |
|---|---|
| Rôle | Repasser en caméra verrouillée. **Sert aussi d'indicateur d'état** : visible = mode libre. Un élément, deux fonctions |
| Position | **Bas droite**, 16 dp du bord droit, **au-dessus du bouton d'action « Partie »** (32 + 56 + 8 = 96 dp du bas) |
| Pourquoi là | Zone du pouce, côté dominant de la majorité, et il ne recouvre pas le marqueur du joueur qui est au centre |
| Taille | 56 dp, `elev-3`, **plus contour 1 dp** (§1.3) |
| Apparition | Fondu + translation de 8 dp, `motion-base`. **Jamais un surgissement** : il apparaît pendant que le doigt est sur la carte |

**États.** Normal : visible en caméra libre. Vide/masqué : caméra verrouillée. Chargement : sans
objet. Erreur : sans objet. Désactivé : sans objet — s'il n'est pas actionnable, il n'est pas là.
Hors ligne : **inchangé et pleinement fonctionnel** ; le GPS est indépendant du réseau (§7.3).

**Le tap sur un hexagone ne fait rien au MVP.** C'est le geste le plus instinctif sur une carte d'hexagones colorés (« c'est à qui, ça ? »), et le seul retour prévu
sur l'appartenance d'une tuile est le bandeau de priorité 8, qui suppose d'y **marcher**
physiquement. Le besoin est réel et il est déjà enregistré : le cadrage §7.6 spécifie une modale
« Mes hexagones », reportée après le MVP.

**Il est laissé vide volontairement, et pas par oubli.** Ajouter un tap sur la carte demande de
trancher ce qu'il ouvre, ce qu'il affiche pour une tuile neutre, et comment il coexiste avec le
double-tap de zoom de Mapbox — trois décisions pour une fonction dont le §2 du cadrage dit qu'elle
n'est pas nécessaire pour jouer. **Aucun geste de tap n'est donc réservé sur la couche hexagones**,
et le jour venu il n'y aura rien à défaire.

**Bascule de mode caméra — précision d'implémentation.** Le cadrage impose que le zoom ne casse
jamais le verrouillage, et que seul un déplacement latéral fasse basculer en mode libre. Sur un
écran tactile, un pincement de zoom produit presque toujours une composante de déplacement
parasite. La règle appliquée est donc : **bascule en mode libre uniquement sur un glissement à un
seul doigt d'au moins 24 dp.** Tout geste à deux doigts (zoom, rotation) est ignoré pour la
bascule. Sans ce seuil, la règle du cadrage serait vraie sur le papier et fausse à l'usage.

#### 7.2.1 La pile d'activité — surcouche de carte

**Rôle.** Rendre l'activité de la partie **perceptible sans geste**.

**Ce qui la justifie.** L'activité est le contenu qui **bouge le plus** de la partie, et le seul qui
exigerait **deux tapes** pour qu'on découvre qu'il s'est passé quelque chose s'il vivait dans un
onglet. Sur un jeu dont le cas dominant est le téléphone en poche (§10), rendre le dernier
événement lisible d'un coup d'œil à la réouverture est la fonction, entière, et elle se défend
seule. **Aucun usage futur n'entre dans cette justification** : la pile coûte de la carte
aujourd'hui, elle doit se payer aujourd'hui.

**Anatomie.**

```
        ┌──────────────────────────────┐  ← plus ancien, opacité 0,25
        │ ⬢⬢ Alice a pris 5 tuiles…    │
        ├──────────────────────────────┤  ← opacité 0,50
        │ ⬢ Chloé rejoint la partie.   │
        ├──────────────────────────────┤  ← opacité 1
        │ ⬢ Bob passe en tête.         │
        ├──────────────────────────────┤  ← plus récent, opacité 1
        │ ⬢ Alice dépasse 250 tuiles.  │
        └──────────────────────────────┘
   ▲ 32 dp du bas — même ligne de base que le bouton d'action « Partie »
```

| Aspect | Décision |
|---|---|
| Position | **Bas gauche.** 16 dp du bord gauche, **32 dp du bas** — même ligne de base que le bouton d'action « Partie », qui est en bas **droite**. Les deux ne se rencontrent jamais : la pile est plafonnée à 240 dp de large |
| Largeur | **240 dp maximum.** Laisse 56 dp au bouton Recentrer plus les marges, sur les 360 dp de l'écran de référence |
| Profondeur | **4 entrées au maximum**, la plus récente **en bas** |
| Dégradé d'opacité | **1 · 1 · 0,70 · 0,45**, du plus récent au plus ancien. **Deux lignes pleines, deux qui s'effacent.** 0,45 est un **plancher** : en dessous, du texte de 12 dp cesse d'être lisible pour tout le monde. Le dégradé est une profondeur, pas une disparition |
| Ligne | Une seule ligne de texte, `type-caption`, **tronquée à l'ellipse** — jamais deux lignes, sinon la pile double de hauteur sans prévenir |
| **Grandes tailles de police** | La pile **perd des entrées plutôt que des caractères** : 3 entrées au-dessus de `textScaler` 1,3, **2 au-dessus de 1,6**. La troncature reste, mais elle s'applique à une ligne qui a la place d'être lue — sans cette règle, il ne resterait qu'une dizaine de caractères par ligne à 200 % |
| Fond | Chaque ligne porte sa **plaque** `surface` **opaque**, `radius-sm`, plus le contour de 1 dp du §1.3. Sans plaque, du texte de 12 dp sur des hexagones saturés est illisible au soleil ; **et une plaque translucide ne permet pas de mesurer le contraste** (§1.5, règle de composition). Aucune transparence, aucun flou |
| Pastilles | Les couleurs des joueurs cités, 10 dp, en tête de ligne — comme dans l'onglet d'origine |

**Le geste — la décision qui rend la chose possible.**

- **Toute la pile est en `IgnorePointer`**, sauf la ligne du bas. Un élément qui n'est pas testé au
  toucher **n'intercepte rien** : le glissement de carte traverse la pile et va à la carte. C'est ce
  qui permet à une surcouche permanente de coexister avec la règle du §7.2, là où un contrôle
  ordinaire l'aurait cassée.
- **La pile reste dans l'arbre d'accessibilité.** Ne pas être touchable ne veut pas dire ne pas
  être lisible : la pile est **la seule surface d'activité
  permanente du jeu**, et un joueur utilisant un lecteur d'écran doit l'entendre. `IgnorePointer`
  est précisément le widget qui peut l'en retirer selon la version de Flutter et la manière dont
  il est posé. **La règle est donc explicite et vérifiable :** les quatre entrées sont annoncées,
  dans l'ordre du plus récent au plus ancien, sous un `Semantics(container: true,
  label: 'Activité récente')` ; la ligne du bas déclare en plus son action de tap. Un test
  d'accessibilité couvre ce point, il ne se vérifie pas à l'œil.
- **La ligne du bas est une cible de tap uniquement**, hauteur tactile 48 dp (§1.4 autorise
  explicitement l'extension de la zone autour du dessin). Elle déclare `onTap` et **rien d'autre** :
  un glissement qui démarre dessus est gagné par le reconnaisseur de la carte, exactement comme
  aujourd'hui entre le bouton d'action « Partie » et la carte.
- **Tap → la modale « Activité »**, qui porte la liste complète (§7.2.2).

**Comportement.**

| Événement | Rendu |
|---|---|
| Nouvelle entrée | Elle apparaît en bas, les autres montent d'un cran et perdent un pas d'opacité, la plus ancienne sort. `motion-base`, jamais de saut |
| **Lot d'entrées** au retour du réseau | **Sans animation**, comme les tuiles (§3.3). On ne rejoue pas trois heures de journal en cascade |
| Aucune entrée dans la partie | **La pile n'existe pas.** Aucun état vide sur la carte : le vide se dit dans la modale, pas sur le jeu |
| Feuille Partie ouverte | La pile est **masquée** — elle serait derrière le voile |
| Bandeau affiché (§2.4) | La pile est **inchangée** : le bandeau est en haut, elle est en bas |
| `MediaQuery.disableAnimations` | Les entrées apparaissent sans transition, la pile reste |

**États.** Normal : ci-dessus. Vide : absente. Chargement : absente — on n'affiche pas un squelette
sur la carte. Erreur : absente, et la modale porte le message ; une surcouche de carte n'est pas un
endroit où signaler une panne. Désactivé : sans objet. **Hors ligne** : la pile reste avec ses
dernières entrées connues, sans mention de fraîcheur — elle est déjà datée par nature, et le
bandeau réseau dit l'essentiel.

**Ce que ça coûte.** La pile occupe **240 × 120 dp**, soit **28 800 dp²** du coin bas-gauche de la
carte. Les 74-80 % de carte visible annoncés au §2.2 sont exacts **au sens de la mise en page** —
la pile n'est pas un élément de flux, la carte s'étend jusqu'à la safe area basse sous elle — mais
ils ne disent rien de la **lisibilité** de ce coin. Il faut le dire ici plutôt que de laisser le
pourcentage le suggérer.

**Deux choses limitent le coût réel, et ce sont elles qui font accepter l'échange :**

1. **La pile n'existe que s'il y a quelque chose à dire.** Aucune entrée dans la partie, aucune
   pile — c'est l'état de départ de toute partie neuve, et il dure jusqu'au premier événement.
2. **Elle est en bas à gauche, à l'opposé du marqueur du joueur**, qui est au centre. Elle ne
   couvre jamais la tuile sur laquelle on se trouve, c'est-à-dire la seule dont la couleur change
   à l'instant où on la regarde (§3.3).

Le §7.0 passe donc de « deux contrôles permanents » à **deux contrôles et une surface
d'affichage**, cette dernière ne consommant aucun geste.

#### 7.2.2 La modale « Activité »

**Rôle.** Porter la liste complète, ce que quatre lignes tronquées ne peuvent pas faire. C'est
l'usage du soir : lire ce qui s'est passé dans la journée.

**Forme.** Feuille modale (§2.5) en pleine hauteur, **avec son titre** « Activité » — on y arrive
par un tap sur un élément nommé, la règle du §2.5 s'applique. Contenu, formats, neuf types
d'entrée, pagination et états : **identiques à ce que spécifiait l'onglet** (§7.4), déplacés sans
modification.

**Pourquoi une feuille et pas un agrandissement de la pile.** La pile est un objet de coup d'œil,
la modale un objet de lecture. Les faire cohabiter dans une même surface qui grandit aurait produit
un troisième point d'ancrage de feuille, en concurrence avec ceux de la feuille Partie (§2.5) sur le
même bord d'écran.

### 7.3 Le bandeau d'explication — verrou de vol et vitesse

**Rôle.** Expliquer une action sans effet. Le cadrage justifie explicitement le compte à rebours du
verrou de vol par : *« sans lui, marcher sur une tuile adverse sans rien obtenir passera pour un
bug »* (§4.2). **Le plafond de 50 km/h (§4.3) pose exactement le même problème et n'a aucun retour
prévu par le cadrage.** Les deux sont traités par le même composant, parce qu'ils ont le même
besoin.

**Décision de forme : réactif, pas permanent.** Le compte à rebours n'est pas un indicateur affiché
en continu sur la carte. Il apparaît **au moment où le joueur subit l'effet**, et disparaît quand
l'effet cesse. Motifs :

- Le cadrage exige un compte à rebours **visible**, pas **permanent**. Un compteur affiché en
  continu est du bruit dans plus de 99 % du temps de jeu, puisqu'un joueur ne tente un vol que
  rarement.
- Il occuperait une position fixe sur la carte, donc un contrôle permanent de plus (§7.0).
- Affiché en permanence, il est là **tout le temps sauf** au moment où il faudrait le remarquer :
  le joueur qui marche regarde la rue, pas l'écran. Déclenché par l'événement, il peut porter un
  retour haptique et une notification, ce qu'un compteur passif ne peut pas.

**Les deux cas :**

| Cas | Déclencheur | Texte | Fin |
|---|---|---|---|
| **Verrou de vol** | Le joueur entre dans un hexagone appartenant à un autre joueur alors que `last_steal_at` + recharge est dans le futur | **Deux lignes.** *« Cette tuile est à Alice. »* en `type-label`, puis *« Tu pourras la reprendre dans 1 min 12 s. »* en `type-caption`, décompté à la seconde | À 0, le message se remplace 3 s par « Tu peux la reprendre. » puis disparaît |
| **Vitesse** | La moyenne glissante dépasse 50 km/h **et** le joueur traverse des hexagones capturables | « Trop vite : tes pas ne comptent pas. » | Dès que la vitesse repasse sous le seuil |

Le second déclencheur est doublement conditionné : afficher « trop rapide » à un passager de train
qui traverse un désert d'hexagones neutres qu'il ne voulait pas capturer serait une nuisance. Le
message n'a de sens que quand le joueur perd réellement quelque chose.

**Calcul.** Le verrou est calculé **localement**, avec la valeur `steal_cooldown_seconds` reçue à
l'entrée en partie (§4.2) — le client applique la même règle que le serveur. La vitesse est
calculée **côté serveur** (§4.3, non négociable) ; le client reçoit un drapeau et se contente de
l'afficher. **Ce drapeau fait partie du contrat serveur** (cadrage §4.3) : un booléen dans la
réponse aux lots de positions, aucun calcul déplacé côté client, donc aucune ouverture anti-triche
(cadrage §12.5).

**États.** Normal : affiché tant que la condition tient. Vide : absent — c'est le cas dominant.
Chargement, erreur, désactivé : sans objet. **Hors ligne** : le verrou reste affiché (calcul local,
horloge locale) ; **l'indicateur de vitesse disparaît**, parce que la capture est déjà en pause pour
une autre raison et que le bandeau réseau, plus prioritaire, dit déjà l'essentiel.

### 7.4 La feuille « Partie »

**Rôle.** Réunir en un seul composant tout ce que §15 listait comme éléments séparés de l'écran de
jeu : liste des participants (§7.5), flux d'activité (§11), code de partie (§6), départ définitif
(§4.4).

**Décision (§15, points 2 et 3) : un panneau glissant à onglets, pas des modales séparées.**

Pourquoi un panneau glissant plutôt qu'une modale plein écran : le tap sur un joueur fait glisser
la caméra vers sa dernière tuile capturée (§7.5). Une modale plein écran cacherait le résultat de
l'action qu'on vient de déclencher — il faudrait la fermer pour voir, puis la rouvrir. Le panneau à
mi-hauteur laisse la carte visible pendant que la caméra se déplace.

Pourquoi un seul panneau à onglets plutôt que trois panneaux : ce seraient trois composants
identiques à la donnée près. Le cadrage impose l'unicité de composant pour les bandeaux (§9.3) ; le
même raisonnement s'applique ici. Et trois panneaux, c'est trois boutons flottants sur la carte.

**Anatomie.**

```
╔══════════════════════════════════╗
║             ───                  ║  poignée 32×4, zone de geste 48 dp
║  ┌────────────┬───────────┬────┐ ║
║  │  Joueurs   │  Inviter  │ ⚙  │ ║  onglets 48 dp · Paramètres 48 dp
║  └────────────┴───────────┴────┘ ║
║                                  ║
║        (contenu de l'onglet)     ║
║                                  ║
╚══════════════════════════════════╝
```

**L'entrée Paramètres est au bout de la barre d'onglets.** Elle occupe un emplacement de
**48 × 48 dp** séparé des deux onglets par un filet vertical en `outline`, glyphe `Gear` (§1.8).
**Ce n'est pas un troisième onglet** : elle n'a pas d'état sélectionné, elle n'échange pas le
contenu de la feuille, elle **ouvre la modale Paramètres par-dessus** (§8). C'est la seule porte
vers les Paramètres pendant une partie, et elle est **en bande basse**, donc atteignable au pouce
sans rattraper le téléphone (§1.4).

**Deux onglets, pas trois.** L'activité ne vit pas ici : elle est posée sur la carte (§7.2.1) avec
sa modale au tap (§7.2.2), parce que c'est le contenu qui bouge le plus et que deux tapes pour
découvrir qu'il s'est passé quelque chose sont deux de trop. **Cette feuille porte ce qui se
consulte à froid** — qui joue, et comment inviter.

**Ni en-tête, ni pied.**

- **Pas de barre de titre.** La feuille glisse depuis l'écran de jeu, ses deux onglets se nomment
  eux-mêmes, et un bandeau qui ne ferait que se nommer coûterait **48 dp de contenu** dans un
  panneau dont la fonction est de **lire des listes** — à mi-hauteur, 5,6 lignes visibles au lieu
  de 6,3. Son nom accessible est porté par `Semantics(label: 'Partie')`, jamais par des pixels.
  **C'est propre à cette feuille** : les autres — Créer, Rejoindre, Choix de couleur, Tableau des
  scores — portent leur titre, parce qu'on y arrive par un bouton nommé (§2.5).
- **Le code de partie ne vit qu'à un seul endroit, l'onglet Inviter.** Le répéter dans un en-tête
  le dupliquerait, avec un second bouton copier — contraire au principe DRY que le cadrage §2 pose
  explicitement.
- **Pas de pied.** « Quitter la partie » vit dans la modale Paramètres (§8) ; le raisonnement est
  au pied de ce paragraphe.

**Ouverture par un bouton d'action.** La feuille s'ouvre par un **bouton d'action rond de 56 dp**,
en bas à droite, à 32 dp du bas, rempli en `accent`, avec le contour de 1 dp du §1.3. Le bouton
« Recentrer » se place au-dessus de lui, à 96 dp du bas.

**Rien d'autre ne vit en bas de l'écran** — pas de bande, pas de poignée, pas de classement
permanent : la carte descend jusqu'à la safe area, et c'est ce qui donne les 74-80 % du §2.2.

**Ce que ça coûte, et il faut le dire :** le classement n'est pas lisible sans geste. Le §7.5 du
cadrage réclame un classement vivant ; il l'est, mais il se consulte. **Compensation :** l'onglet
Joueurs affiche en tête *« 5 joueurs · fin dans 2 j 04 h »*, et le score du joueur est porté par le
header, qui reste permanent.

**Ouverture automatique (§6).** À la **toute première** entrée en partie du créateur, la feuille
s'ouvre seule à mi-hauteur sur l'onglet **Inviter**. Une seule fois, jamais à la réouverture de
l'app — sinon elle devient une nuisance quotidienne sur une partie longue.

**Aucune pastille de non-lu n'est nécessaire.** Le signal d'activité est porté par la pile de la
carte (§7.2.1), qui montre la dernière entrée en permanence. Un compteur sur un onglet aurait dit
« il s'est passé quelque chose » là où la pile dit **quoi**.

#### Onglet « Joueurs » (§7.5)

**En-tête de l'onglet.** Une ligne de contexte en `type-caption`, `on-surface-muted` :
*« 5 joueurs · fin dans 2 j 04 h »*. C'est elle qui porte l'essentiel dès l'ouverture, en l'absence
de classement permanent (§7.4). Sous elle, un en-tête de colonne discret : *« hex · pts »*, aligné
à droite.

**En pied de liste**, une ligne de réassurance en `type-caption` :
*« Le classement se met à jour à chaque capture. Personne ne voit la position de personne. »*
Elle redit ce que la mention d'entrée en partie (§6) annonce une fois — mais cette page est
précisément celle où l'on se demande ce que les autres voient de nous.

Une ligne par joueur, hauteur **64 dp**, tappable en entier.

```
⬢  Alice                    312 hex · 31 200 pts
   dernière capture il y a 2 h
```

| Élément | Détail |
|---|---|
| Pastille | 16 dp, couleur du joueur, contour 1 dp |
| Pseudo | `type-body`. Le joueur lui-même est en graisse 600 et porte « (toi) » |
| Score | `type-label`, aligné à droite : tuiles **et** points, même logique qu'au header |
| Fraîcheur | `type-caption`, `on-surface-muted` : « dernière capture il y a 2 h » — **obligatoire** (§7.5) |
| Tri | Par nombre de tuiles décroissant. Le rang n'influence **jamais** la couleur |

**Interaction.** Tap sur une ligne → la feuille **se ferme** et la caméra **glisse**
(`motion-camera`, 600 ms) vers la dernière tuile capturée de ce joueur, **jamais sa position en
direct**. La caméra passe en mode libre : le bouton « Recentrer » apparaît, ce qui indique
exactement comment revenir.

**La pastille voyage avec la caméra.** Le déplacement se fait
par **transition d'élément partagé** (`Hero`) : la pastille de 16 dp de la ligne quitte la liste et
devient le repère posé sur la tuile de destination, pendant que la feuille redescend et que la
caméra glisse. Motif : un glissement de caméra seul ne relie pas l'action à son résultat — le
joueur tape une ligne, l'écran bouge, et rien ne dit que ce qu'il voit **est** ce qu'il a demandé.
La pastille qui voyage le dit sans un mot. Le repère disparaît en fondu après 2 s, ou au premier
geste sur la carte.

**Arrivée de la liste.** Les lignes apparaissent en cascade, `motion-stagger` — **30 ms par ligne,
plafonnée à 8 lignes**. Au-delà de huit, les dernières traînent et la liste paraît lente au lieu de
paraître vivante. La même règle vaut pour la modale Activité (§7.2.2) et pour l'historique des
parties (§8.2).

**États.**

| État | Rendu |
|---|---|
| Normal | La liste |
| **Vide** | Un seul joueur : sa ligne est affichée, suivie de « Personne d'autre pour l'instant. » et d'un bouton « Inviter » qui bascule sur l'onglet Inviter. C'est le cas normal juste après la création (§9) |
| **Vide par joueur** | Un joueur qui vient de rejoindre : « aucune capture pour l'instant » à la place de la fraîcheur. La ligne est **non tappable** — jamais de saut vers des coordonnées nulles (§7.5) |
| Chargement | Trois lignes en squelette |
| Erreur | « La liste des joueurs n'est pas arrivée. » + « Réessayer » |
| Désactivé | Une ligne sans capture, comme ci-dessus |
| Hors ligne | Dernières valeurs connues + mention en tête de liste : *« Mis à jour il y a 6 min »* |

#### Contenu de la modale « Activité » (§11)

Liste chronologique inverse, la plus récente en haut. Chaque entrée porte **un horodatage** et
**une bande de distance** (§11.2).

```
⬢⬢  il y a 12 min · dans ta région
    Sur la dernière heure : Alice +23 tuiles, Bob +12, Chloé +4.
```

| Élément | Format |
|---|---|
| Horodatage | Relatif sous une heure : *« il y a 12 min »*. Absolu au-delà : *« Hier 18 h 42 »* |
| Bande de distance | « près de toi » (< 2 km) · « dans ta région » (2–50 km) · « loin » (> 50 km) |
| Calcul de la bande | **Localement, sur l'appareil**, depuis le centre de gravité reçu et la position locale. La position du lecteur ne quitte jamais l'appareil (§11.2) |
| Pastilles | Les couleurs des joueurs cités, en tête de ligne |

Les **onze** types d'entrée, avec leurs textes :

| Type | Texte |
|---|---|
| Arrivée | *« Chloé rejoint la partie. »* |
| Départ définitif | *« Bob quitte la partie. 137 tuiles sont libérées. »* — le nombre est obligatoire (§11.3) |
| Fin imminente | *« La partie se termine dans 1 heure. »* / *« …dans 10 minutes. »* |
| Fin de partie | *« La partie est terminée. »* |
| Bilan périodique | « Sur la dernière heure : Alice +23 tuiles, Bob +12, Chloé +4. » |
| Tête du classement | « Bob passe en tête. » |
| Palier de territoire | *« Alice dépasse 250 tuiles. »* |
| Vols agrégés | « Alice a pris 5 tuiles à Bob dans la dernière heure. » |
| Rythme exceptionnel | « Chloé a capturé 30 tuiles en 20 minutes. » |
| **Vol subi** *(ajout)* | *« Alice t'a pris 2 tuiles. »* |
| **Vol réussi** *(ajout)* | *« Tu as pris 3 tuiles à Alice. »* |

> **Pourquoi les deux derniers existent.** Les neuf premiers sont à la **troisième personne** : ils
> racontent ce que les autres font entre eux. Or le §4.2 fonde le verrou de vol sur le fait qu'un
> joueur doit comprendre ce qui lui arrive, et le §7.1 sur le fait qu'une **baisse de score
> inexpliquée passe pour un bug**. Le bandeau du §7.3 et le bilan de retour du §7.1 disent la
> baisse **au moment où elle se voit** ; ces deux types-là en sont **la trace consultable
> ensuite**. Le header dit « −200 », le journal dit **qui** et **quand**.
>
> **Trois règles qui les encadrent :**
>
> 1. **Ils remplacent le type « Vols agrégés » quand le lecteur est concerné**, ils ne s'y
>    ajoutent pas. Une même série de vols ne produit jamais deux entrées.
> 2. **Ils sont agrégés sur la même fenêtre** que les vols entre tiers (§11.5) — jamais une entrée
>    par tuile, sinon un joueur qui traverse un territoire adverse produit trente lignes.
> 3. **Ils ne nomment aucun lieu** et portent la bande de distance comme les autres (§11.1). « Près
>    de toi » y est fréquent par construction : un vol se produit là où l'on est.

**Aucune entrée ne nomme un lieu** (§11.1). La bande de distance est le seul repère spatial, et
c'est un palier grossier, jamais une valeur chiffrée.

**Distinction visuelle.** Les entrées structurelles (arrivée, départ, fin) portent un liseré à
gauche ; les entrées de progression n'en portent pas. Deux niveaux, pas neuf icônes.

**États.**

| État | Rendu |
|---|---|
| Normal | La liste, **paginée** (§12.4) : chargement de la page suivante à l'approche du bas |
| **Vide** | « Rien à relever pour l'instant. Le premier bilan tombe dans 5 minutes. » — le délai est calculé depuis la fréquence de la partie (§11.5), ce qui transforme un vide en attente comprise |
| Chargement | Trois lignes en squelette |
| Chargement de page | Indicateur de 32 dp en pied de liste |
| Erreur | En pied de liste : « La suite n'est pas arrivée. » + « Réessayer ». Les entrées déjà chargées restent |
| Hors ligne | Entrées en cache + mention en tête : *« Mis à jour il y a 6 min »* |
| Désactivé | Sans objet |

#### Onglet « Inviter » (§6)

**Contenu.** Le code à 6 caractères en `type-mono`, à **40 dp** de taille, centré, sur un fond
`surface-dim` de 88 dp de haut, avec un bouton « Copier le code » (56 dp) et un bouton
« Partager » (56 dp) qui ouvre la feuille de partage Android.

**Textes.** « Donne ce code à tes amis pour qu'ils rejoignent la partie. » · « Le code reste valide
pendant toute la partie. » (§6 : on peut rejoindre en cours). Après copie : *« Code copié »* en
`SnackBar` de 2 s.

**Le texte partagé.** C'est, au MVP, **le seul vecteur d'acquisition du jeu** : sans QR ni lien
profond (§6), tout nouveau joueur arrive par ce message. Il doit donc nommer le jeu, donner le code, et dire où l'installer — un
message qui ne porte qu'un code de six caractères est illisible pour qui ne connaît pas Arpendo.

> *« Rejoins ma partie sur Arpendo, le code est **K7MQ4P**.*
> *Arpendo, c'est un jeu de territoire : tu colores les hexagones où tu marches.*
> *https://play.google.com/store/apps/details?id=… »*

| Règle | Motif |
|---|---|
| **Trois lignes, pas une** | Le code seul ne dit rien à qui ne connaît pas le jeu |
| **Le code est en gras et isolé sur la première ligne** | C'est ce qu'on recopie, et beaucoup de messageries tronquent l'aperçu après la première ligne |
| **Le lien du Play Store est en clair, en dernier** | Les messageries en font un aperçu ; placé au milieu, il coupe le texte en deux |
| **Aucun émoji** | §0, règle de ton |
| **Une seule chaîne i18n, avec le code en paramètre** | Le message est un texte, pas une concaténation de morceaux traduits séparément |

Le lien profond du post-MVP (§6) **remplacera la troisième ligne** sans toucher aux deux premières
— c'est ce que garantit le module d'invitation à interface unique, et c'est ce qui évite d'avoir à
réserver quoi que ce soit aujourd'hui.

**Pas d'emplacement réservé pour le QR code ni le lien profond.** Le cadrage les repousse
explicitement après le MVP (§6) et garantit leur ajout indolore par un **module d'invitation à
interface unique** — c'est-à-dire par l'architecture, pas par un trou dans la maquette. Un
emplacement vide est un composant qui n'existe qu'au cas où.

**États.** Normal. Chargement : le code arrive avec l'état de partie, donc jamais absent en
pratique ; si absent, squelette. Erreur : « Le code n'est pas arrivé. » + « Réessayer ».
Hors ligne : le code est en cache local et reste affiché — **c'est précisément la situation où on
veut le lire**, avec des amis autour de soi et un réseau saturé. Vide, désactivé : sans objet.

#### « Quitter la partie » — déplacé dans la modale Paramètres

**Rôle.** Départ définitif et irréversible (§4.4).

**Emplacement.** L'action ne vit **pas** au pied de la feuille Partie, mais dans le bloc **« Cette partie »** de la modale Paramètres (§8), atteignable par l'icône
Paramètres de la barre d'onglets de la feuille Partie (§7.4). Motifs :

- **Un composant en moins.** Un pied de feuille qui n'existerait que pour porter ce seul bouton,
  avec son filet et son `space-12`, est un composant qui existe pour se justifier.
- **La garantie ergonomique est la même.** « Quitter la partie » reste hors de portée du pouce au
  repos, en fin de liste défilante — la règle du §1.4, appliquée où qu'elle vive.
- **Une seule porte vers les Paramètres, et elle est ici.** L'icône vit dans la barre d'onglets de
  cette feuille (voir l'anatomie ci-dessus), pas dans le header du Jeu — qui est inerte (§7.1). Une
  seconde porte aurait recréé le défaut que §7.0 a passé son temps à supprimer.
- **Les liens juridiques y sont déjà**, dans le bloc « Informations » (§8) : rien à déplacer.

**Ce que ça coûte, et pourquoi c'est acceptable.** Le chemin est « bouton d'action → icône
Paramètres → faire défiler jusqu'au bas ». Trois gestes pour une action irréversible, tous dans la
zone du pouce sauf le dernier : c'est une action qu'on veut **délibérée**, pas fluide.

**Ce que ça impose au §8.** Le bloc « Cette partie » n'apparaît **que si une partie est active**, et
il porte un **libellé de section visible** qui nomme la portée de ce qu'on va détruire. Il est le
pendant du bloc « Ce compte », qui n'apparaît **qu'au Menu** : les deux ne sont jamais visibles
ensemble, et « Quitter la partie » ne peut donc jamais être confondu avec « Supprimer mon compte ».

**La modale de confirmation** (§2.6, `saisieRequise: true`), inchangée :

> **Titre** — « Quitter définitivement ? »
> **Corps** — « Tu laisses 1 247 hexagones derrière toi. Ils redeviennent libres, et tu ne les
> récupéreras pas. » *(le nombre est réel, jamais un exemple)*
> **Corps 2** — « Tu peux rejoindre à nouveau, mais tu repars de zéro. »
> **Champ** — libellé « Écris **définitivement** pour confirmer »
> **Action** — « Quitter définitivement » — désactivée tant que le champ ne correspond pas
> **Annuler** — « Annuler »

Le corps 1 dit la conséquence pour les autres ; le corps 2 dit la possibilité de revenir : sans lui,
le joueur ignore qu'il peut rejoindre, et le message ressemble à une suppression de compte.

**Après confirmation :** la modale Paramètres et l'écran Jeu se ferment **immédiatement**, route
vers le Menu. Le créneau de partie active se libère tout de suite ; la neutralisation continue en
tâche de fond (§4.4). Aucun écran d'attente : le joueur attendrait sans comprendre. Un `SnackBar`
de 4 s sur le Menu : *« Tu as quitté la partie. »*

### 7.5 États de l'écran Jeu — synthèse

| État | Ce qui est affiché |
|---|---|
| Normal | **Puces de header** + carte + **pile d'activité** + bouton d'action « Partie » |
| Chargement initial | Carte au fond `surface-dim`, puce de score avec « — hex · — pts », bouton d'action présent mais inactif, **pile absente**. **Aucun voile plein écran** : la carte doit apparaître dès qu'elle peut |
| Vide | Partie neuve, aucune tuile et aucune entrée : état normal, **sans pile**. Le vide n'appelle aucun message ici |
| Erreur de viewport | Dernières données conservées + bandeau. **Ne jamais vider la couche** |
| Hors ligne | Couche à 60 %, bandeau 5 ou 6, carte navigable, capture selon la phase (§10.1) |
| Localisation refusée | Carte **non instanciée**, fond `surface-dim`, bandeau bloquant, **bouton d'action « Partie » actionnable** — le seul chemin vers les Permissions (§12.2) |
| Désactivé | Sans objet — un écran de jeu n'est jamais désactivé, il est expliqué |

---

## 8. Modale Paramètres

**Rôle.** Composant **unique**, ouvert depuis le Menu comme depuis le Jeu (§15), avec **deux blocs
contextuels** qui s'excluent — voir ci-dessous. C'est le point de rattrapage permanent : un joueur
sans permission de localisation garde l'accès à cette modale, donc garde accès à ses **Permissions**
en toutes circonstances, et à la suppression de son compte — depuis le Menu directement, depuis une
partie par le lien web du bloc Informations (§15, note de cohérence).

**Forme.** Feuille modale (§2.5) en pleine hauteur. **Deux points d'ouverture, un par contexte :**
l'icône de la barre d'onglets de la feuille Partie **en partie** (§7.4), l'icône de la barre de
titre **au Menu** (§5). Il n'y en a jamais deux à la fois.

**Contenu**, dans cet ordre :

| # | Bloc | Contenu | En partie | Au Menu | Cible |
|---|---|---|---|---|---|
| 1 | Identité | Pastille de couleur si en partie · pseudo, **lecture seule** · **l'adresse du compte Google**, en `type-caption` et `on-surface-muted` : *« compte Google · theo@gmail.com »* · mention « Ton pseudo est définitif. » | ✔ | ✔ | — |
| 2 | **Permissions** | Ligne avec **pastille d'alerte** si un niveau manque → réglages système | ✔ | ✔ | 64 dp |
| 3 | **Historique des parties** | Liste des parties terminées, paginée | ✔ | ✔ | 64 dp / ligne |
| 4 | Informations | Version de l'app · « Politique de confidentialité » · « Conditions d'utilisation » · **« Supprimer mon compte depuis le web »** | ✔ | ✔ | 48 dp |
| **5** | **Cette partie** | Libellé de section, puis, après `space-12`, **« Quitter la partie »** — bouton texte `danger` | ✔ **en dernier** | ✖ | 48 dp |
| **5** | **Ce compte** | Libellé de section, puis « Se déconnecter de Google » — bouton texte neutre, puis après `space-12` **« Supprimer mon compte »** — bouton texte `danger` | ✖ | ✔ | 48 dp |

> **Les deux blocs contextuels occupent la même position, la dernière**, et ils s'excluent. C'est ce
> qui rend la modale identique en structure dans les deux contextes : quatre blocs communs, puis un
> cinquième qui nomme la portée de ce qu'on va détruire. Le §1.4 pose que les actions destructives
> vivent **en fin de liste défilante** ; les placer plus haut les rendrait visibles sans défiler.

**Pourquoi l'adresse du compte Google est affichée.** Le cadrage §5.2 exclut la photo de profil, et
c'est la seule donnée Google de l'interface. Elle est là pour une raison précise : **un joueur qui
possède plusieurs comptes Google doit pouvoir vérifier lequel il utilise.** C'est la seule donnée personnelle affichée à l'écran, elle n'est visible que
par son propriétaire, elle n'est jamais transmise à un autre joueur et ne figure dans aucune liste
ni aucun classement. À répercuter dans la politique de confidentialité (cadrage §13.12).

Le libellé de déconnexion devient **« Se déconnecter de Google »** plutôt que « Déconnexion » :
il nomme ce qu'on quitte, ce qui compte quand on a plusieurs comptes.

Tout ce qui est destructif est en bas de liste défilante, hors de portée du pouce au repos —
**« Quitter la partie » comme « Supprimer mon compte », sans exception**. Dans la version « au
Menu », « Supprimer mon compte » est en dernier et séparé de la déconnexion par `space-12` : c'est
l'action la plus destructive de l'app.

**La modale est contextuelle.** Deux blocs s'excluent mutuellement :
**« Cette partie » n'existe qu'en partie, « Ce compte » n'existe qu'au Menu.** Ils ne sont donc
jamais visibles ensemble, et le risque de confondre « Quitter la partie » avec « Supprimer mon
compte » disparaît par construction. Les libellés de section restent, parce qu'ils nomment la
portée de ce qu'on va détruire.

**Pourquoi la déconnexion et la suppression de compte disparaissent en partie.** Ce n'est pas une
question d'encombrement, c'est une question d'état. Pendant une partie, un **service de premier
plan tourne**, il capture des positions et il porte un jeton de session (§10). Se déconnecter à cet
instant laisse un service actif avec une session morte — un état qu'il faut soit gérer par du code
défensif, soit rendre impossible. **On le rend impossible.** La suppression de compte pose le même
problème, en pire : elle déclenche la libération des tuiles et de la couleur (§8.2) pendant que le
service continue d'en capturer.

**Ce que ça ne doit surtout pas coûter, et la condition qui l'empêche.** Une partie peut durer
**un mois**. Retirer « Supprimer mon compte » de la modale en partie sans rien mettre à la place
reviendrait à dire à un joueur qui veut effacer ses données qu'il doit d'abord quitter sa partie —
ce qui n'est pas défendable. **La contrepartie est donc obligatoire : le bloc Informations porte,
en permanence et dans les deux contextes, un lien « Supprimer mon compte depuis le web ».**
Le cadrage §12.2 garantit déjà cette voie sans installer l'app ; elle cesse ici d'être une note de
bas de page et devient la porte de secours en partie. Sans elle, ce retrait ne passe pas.

**Le bouton Permissions, lui, reste dans les deux contextes** (§9.3), y compris quand tout est
accordé. C'est le point de rattrapage permanent : un joueur en partie dont la localisation est
refusée voit une carte masquée, et **c'est son seul chemin de retour**. Un point de rattrapage qui
disparaît au moment où on en a besoin n'en est pas un.

**Ce que cela impose à l'écran Jeu.** Puisque l'unique porte vers cette modale en partie est
l'icône de la barre d'onglets de la feuille Partie, **le bouton d'action « Partie » et la feuille
qu'il ouvre restent présents et actionnables dans tous les états dégradés** — carte masquée
comprise (§12.2), hors ligne, permission retirée en cours de partie. Un bouton d'action désactivé
dans l'état « carte masquée » enfermerait le joueur : plus de carte, et plus de chemin vers ses
Permissions.

### 8.1 Ligne « Permissions »

| État | Rendu |
|---|---|
| Tout accordé | « Permissions » · sous-titre « Tout est autorisé. » · **aucune pastille** |
| Un niveau manquant | Pastille d'alerte 8 dp `warning` sur l'icône · sous-titre nommant le manque : *« Localisation en arrière-plan non autorisée »*, *« Notifications non autorisées »* |
| Plusieurs manquants | Sous-titre : *« 2 autorisations manquantes »* |
| Tap | Ouvre l'écran des réglages système de l'app (`AppSettings`), jamais une boîte de dialogue de l'app |

### 8.2 Historique des parties (§8.4)

Une ligne par partie terminée : durée, date de fin, **rang du joueur**, tuiles finales.

```
24 h · terminée le 9 août            2ᵉ sur 5 · 312 hex
```

Tap → détail : l'instantané figé (§8.4), pseudo / couleur / points / tuiles, **seuls les joueurs
présents à la fin**. Un compte supprimé apparaît « Joueur supprimé » et sa pastille passe en
`outline` neutre — sa couleur ne lui appartient plus.

**États.**

| État | Rendu |
|---|---|
| Normal | La liste, **paginée** (§12.4) |
| **Vide** | « Aucune partie terminée pour l'instant. » + « Tes parties apparaissent ici une fois terminées. » |
| Chargement | Trois lignes en squelette |
| Erreur | « L'historique n'est pas arrivé. » + « Réessayer » |
| **Partie abandonnée** | Mention « abandonnée » à la place du rang. Le détail n'affiche **aucun podium** (§4.5) |
| Hors ligne | Liste en cache si elle a déjà été chargée, sinon état d'erreur avec « Réessayer » |
| Désactivé | Sans objet |

### 8.3 Modale « Supprimer mon compte » (§12.2)

Modale de confirmation (§2.6), `saisieRequise: true`, mot attendu « **supprimer** ».

**Accessible depuis le Menu uniquement** (bloc « Ce compte »). En partie, la suppression passe par
le lien web du bloc Informations — voir le raisonnement au §8.

> **Titre** — « Supprimer ton compte ? »
> **Corps** — « Ton compte est désactivé immédiatement et toutes tes données sont effacées sous
> 30 jours. »
> **Liste** — « Ton pseudo devient "Joueur supprimé" dans les classements. » · « Ta couleur est
> libérée. » · « Tes hexagones redeviennent libres. » · « Ton pseudo ne sera jamais réattribué. »
> **Champ** — « Écris **supprimer** pour confirmer »
> **Action** — « Supprimer définitivement »
> **Annuler** — « Annuler »

Après confirmation : déconnexion et retour à l'écran Connexion, avec *« Ton compte a été
supprimé. »* La suppression est aussi accessible par une URL web sans installer l'app (§12.2) —
hors périmètre de ce document, mais le lien figure dans le bloc Informations.

---

## 9. Fin de partie et tableau des scores

**Rôle.** Clôturer (§4.5, §8.4).

**Décision de forme.** Le tableau des scores est une **feuille modale ouverte par-dessus le Menu**,
pas un troisième écran de fond. Motif : à la fin de la partie, il n'y a plus de partie active, donc
§8.3 route vers le Menu. La feuille s'ouvre par-dessus. C'est cohérent avec la règle des deux
écrans de fond, et cela veut dire que fermer la feuille laisse le joueur exactement là où il doit
être — devant « Créer une partie ».

**Déclenchement.** À la réception de l'événement de fin (SSE si au premier plan, notification push
sinon), l'écran Jeu se ferme et la feuille s'ouvre. Si le joueur était en arrière-plan, elle s'ouvre
à la réouverture de l'app. **Une seule fois** : elle reste ensuite consultable dans l'historique.

**Contenu.**

| Cas | Rendu |
|---|---|
| **Partie terminée par le timer** | Podium des 3 premiers (le premier plus haut et plus grand), puis la liste complète. La ligne du joueur est mise en avant même hors du podium |
| **Partie abandonnée** | **Aucun podium** (§4.5). Titre « Partie abandonnée », corps « Tous les joueurs ont quitté la partie. » puis la liste, si elle n'est pas vide |

Chaque ligne : pastille · pseudo · **points** en `type-display` · tuiles en `type-caption`.
Seuls les joueurs présents à la fin sont listés (§8.4). Un joueur parti n'apparaît pas — ce n'est
pas un oubli, c'est la décision du §8.4, et le texte de pied le dit : « Les joueurs ayant quitté la
partie n'apparaissent pas au classement. »

**Actions.** « Fermer » (56 dp, bas de feuille). Pas de bouton « Rejouer » : il n'existe pas de
mécanisme de revanche au MVP, et proposer une action qui recrée une partie vide avec les mêmes
personnes serait un composant inventé.

**États.** Normal : ci-dessus. Vide : partie abandonnée sans aucun joueur restant → « Cette partie
s'est terminée sans joueur. » Chargement : squelette de podium. Erreur : « Le classement n'est pas
arrivé. » + « Réessayer ». Hors ligne : si l'instantané n'a pas été reçu, état d'erreur ; il est
figé côté serveur et ne changera plus, donc un réessai réussira. Désactivé : sans objet.

---

## 10. La notification permanente — spécification complète

**Rôle.** Interface du service de capture en arrière-plan. Imposée par Android (§9.1), mais le
cadrage lui donne un second rôle décisif : **« La notification permanente devient le canal
d'alerte »** (§10.3).

> **C'est la seule interface du cas dominant.** Le §10.3 le dit : le cas dominant du jeu est le
> téléphone en poche, app fermée. Pendant les heures — parfois les semaines — où c'est vrai, cette
> notification est **tout ce que le joueur voit d'Arpendo**. Elle mérite le même niveau de soin que
> l'écran de jeu.

### 10.1 Canal et comportement

| Propriété | Valeur | Motif |
|---|---|---|
| Canal | `capture` — « Capture en cours » | Un canal distinct de celui des notifications de partie, pour que le joueur puisse couper l'un sans l'autre |
| Importance | **`IMPORTANCE_LOW`** | Pas de son, pas de vibration, pas d'apparition en surimpression. Une notification qui vit des semaines et qui sonne est une désinstallation |
| `ongoing` | vrai | Non balayable, comme l'exige un service de premier plan |
| `showWhen` | **faux** | Un horodatage sur une notification permanente vieillit et donne l'impression d'un service mort |
| `onlyAlertOnce` | vrai | Les changements de texte ne réalertent pas |
| Icône | Monochrome, silhouette d'hexagone | Contrainte Android : l'icône de statut est réduite à une silhouette |
| Tap | Ouvre l'app **sur l'écran Jeu**, sans recréer la pile de navigation | |

**Aucun bouton d'action.** Il n'existe aucune action utile depuis cette notification : « quitter la
partie » y serait irréversible et à un tap d'un balayage de poche, et « mettre en pause » n'existe
pas dans les règles du jeu.

### 10.2 Contenu, par état

Le titre est **stable**, le texte porte l'état. Un titre qui change fait perdre le repère visuel
dans un tiroir de notifications rempli.

| État | Titre | Texte |
|---|---|---|
| **Nominal, en mouvement** | « Arpendo » | *« 124 hex · 2 j 04 h restantes »* |
| **Nominal, immobile** | « Arpendo » | *« 124 hex · 2 j 04 h restantes »* — identique. Le mode veille (§9.1) n'est pas un incident, il n'a rien à signaler |
| **Connexion instable** | « Arpendo » | « Connexion instable » |
| **Hors ligne au-delà de 5 min** | « Arpendo » | « Hors ligne : tes pas ne comptent pas. » |
| **Serveur injoignable** | « Arpendo » | « Le serveur ne répond pas. La reprise est automatique. » |
| **Trop rapide** | « Arpendo » | « Trop vite : tes pas ne comptent pas. » |
| **Localisation retirée** | « Arpendo » | « Sans localisation, la capture est arrêtée. » |
| **Partie terminée** | « Arpendo » | *« Partie terminée »* — puis le service s'arrête et la notification disparaît |

**Les états et leur ordre de priorité sont exactement ceux du bandeau (§2.4).** Même table de
vérité, deux rendus : bandeau au premier plan, notification en arrière-plan. C'est la même règle
métier écrite une seule fois — une divergence entre les deux produirait deux diagnostics
contradictoires pour un même incident.

Le texte nominal porte le **compte de tuiles et le temps restant**, pas le score en points : c'est
la valeur qui bouge, elle tient en peu de caractères, et sur un écran verrouillé c'est la seule
chose qu'on lit. Il est mis à jour **au plus une fois par minute**, jamais à chaque capture — une
notification qui se réécrit en continu réveille l'écran et vide la batterie, ce que §9.1 interdit.

### 10.3 Le cas où elle n'existe pas

Depuis Android 13, afficher une notification exige une permission d'exécution. Si elle est refusée,
**le service tourne mais sa notification n'est pas affichée**. Toute la mécanique d'alerte de §10.3
tombe silencieusement, et les notifications push de §14.2 avec elle.

Traitement retenu — **quatrième niveau du modèle de permissions** (§13) :

- L'autorisation est demandée **après** la localisation de base, à la première entrée en partie,
  avec une phrase d'amorce : « Arpendo t'avertit si la capture s'arrête, et quand la partie se
  termine. »
- Refusée : le jeu **fonctionne intégralement**, capture comprise. Bandeau priorité 11 :
  « Arpendo ne peut pas t'avertir si la capture s'arrête. » + « Réglages » · « Masquer pour cette
  partie ».
- Pastille d'alerte permanente sur « Permissions » dans la modale Paramètres (§8.1).
- **Compensation au premier plan** : pour ces joueurs, le bilan de retour du §7.1 et le bandeau de
  captures perdues (priorité 13) sont les seuls canaux restants. Ils ne sont donc **jamais**
  supprimés ni écourtés.

### 10.4 Le message de captures perdues (§10.3)

Au retour au premier plan, si des captures ont été perdues au-delà de la fenêtre de 5 minutes,
l'indiquer **une fois, sobrement** — c'est l'exigence littérale du cadrage.

- Bandeau priorité 13 : *« La coupure a duré trop longtemps : 12 captures sont perdues. »*
- Disparaît seul après 6 s. Aucune action, aucune modale, aucune confirmation.
- **Une seule fois par épisode hors ligne.** Compté côté serveur, sur les positions rejetées, pas
  côté client.

Sans ce message, le joueur constate un score incohérent et conclut à un bug ou à de la triche.
Avec une modale, on transformerait une perte mineure en événement — la reprise doit rester
silencieuse (§10.1).

---

## 11. Notifications push et mise à jour

### 11.1 Notifications push (§14.2)

Trois, et trois seulement, sur un canal distinct de celui de la capture :

| Événement | Titre | Texte | Tap |
|---|---|---|---|
| Fin imminente | « La partie se termine bientôt » | *« Plus qu'une heure. Tu es 3ᵉ avec 124 hex. »* | Écran Jeu |
| Fin de partie | « Partie terminée » | *« Alice gagne avec 312 hex. Tu es 3ᵉ. »* | Feuille Tableau des scores |
| Classement | — | **Fusionné avec le précédent.** Deux notifications à une seconde d'intervalle pour le même événement sont une notification de trop | — |

**Aucune notification pour le flux d'activité** (§14.2). Le flux ne réveille jamais le téléphone et
ne sort jamais de l'application.

> **Cette règle porte sur les notifications système**, pas sur ce que l'écran montre pendant qu'on
> le regarde. La pile d'activité (§7.2.1) est visible en permanence
> **dans** l'application, et ne contredit donc rien ici : elle n'alerte pas, elle n'interrompt pas,
> elle ne survit pas à la fermeture de l'app. Un joueur qui range son téléphone n'en entend jamais
> parler.

### 11.2 Mise à jour (§14.1)

**Version minimale — écran bloquant.** `z 500`, plein écran, pas de bouton retour, pas de
fermeture. Titre « Mise à jour nécessaire ». Corps « Cette version d'Arpendo n'est plus compatible
avec le serveur. Installe la dernière version pour continuer à jouer. » Bouton « Mettre à jour »
(56 dp, bande basse) → Play Store. Corps 2, `type-caption` : « Ta partie et ta progression sont
conservées. » — sans quoi le joueur croit tout perdre et hésite.

**Si le magasin ne s'ouvre pas** — ni l'application du magasin ni un navigateur ne répond au lien —
**l'écran ne change pas** : aucun message, aucun état d'erreur, et le bouton reste tapable. C'est
l'exception à la règle du §13.3 (« toute erreur récupérable porte "Réessayer" »), et elle est
motivée : il n'y a **rien à récupérer dans l'application**. Le seul geste utile — installer la
mise à jour — se fait dehors, et un message qui ne propose aucune action n'ajouterait que de
l'inquiétude à un écran déjà bloquant.

Cet écran s'affiche **avant** tout appel authentifié (§2.1).

**Version recommandée — bandeau.** Priorité 12 du bandeau unique (§2.4), fermable. Une fois fermé,
il ne réapparaît **pas** pour la même version ; il réapparaît à la version suivante.

---

## 12. Permissions — parcours complet

**Rôle.** Le cadrage définit un modèle unique à réévaluer à chaque passage au premier plan (§9.3).
Ce document en spécifie l'interface, **quatrième niveau compris** — celui qu'exige §10.3.

### 12.1 Les quatre niveaux

| Niveau | Effet sur le jeu | Interface |
|---|---|---|
| **Localisation de base refusée** | Carte masquée. **Création et participation bloquées.** Modale Paramètres toujours accessible | Bandeau bloquant, priorité 1 ou 2 |
| **Base accordée, arrière-plan refusé** | **Jeu complet.** Perte de la seule reprise après redémarrage du téléphone | Bandeau non bloquant, priorité 10, masquable pour la partie · pastille permanente sur « Permissions » |
| **Notifications refusées** *(ajout)* | **Jeu complet.** Perte du canal d'alerte et des notifications de fin | Bandeau non bloquant, priorité 11, masquable pour la partie · pastille permanente |
| **Tout accordé** | — | Aucun bandeau, aucune pastille |

Le message du second niveau est **« Ta progression s'arrêtera si ton téléphone redémarre »** — mot
pour mot le cadrage (§9.2), et surtout **pas** « si tu fermes l'app », ce qui est faux et
pousserait le joueur à garder l'app ouverte, vidant sa batterie pour rien.

### 12.2 L'état « carte masquée » — décision (§15, point 8)

**Aucun widget Mapbox n'est instancié.** L'écran affiche :

- Un fond `surface-dim` uni, avec un motif d'hexagones très pâle (`outline` à 20 %) — assez pour
  que l'écran ait une identité, assez peu pour qu'on ne le confonde pas avec une carte.
- Le **bandeau bloquant** (priorité 1, 2 ou 3), centré verticalement plutôt que collé en haut :
  c'est le seul contenu de l'écran, le mettre en haut laisserait un grand vide sous lui.
- Les **puces de header restent affichées**, avec leurs valeurs figées. Elles sont inertes (§7.1),
  elles ne portent donc aucun chemin de sortie.
- **Le bouton d'action « Partie » reste présent et actionnable**, et c'est lui qui porte la
  garantie de cohérence du §15 : il ouvre la feuille, dont la barre d'onglets porte l'icône
  Paramètres, d'où l'on atteint ses **Permissions** — le seul chemin de retour — et le lien web de
  suppression de compte. Il est en bande basse, donc à portée du pouce d'un joueur qui vient de
  comprendre qu'il ne peut pas jouer.

Deux raisons de ne pas instancier la carte plutôt que de la masquer derrière un voile :

1. Une carte sous un voile continue de charger des tuiles et **consomme du quota MAU Mapbox** —
   le risque financier n°1 du projet (§13.10). Un joueur qui ne peut pas jouer ne doit rien coûter.
2. Le retour de permission doit faire **réapparaître la carte automatiquement, sans quitter et
   rouvrir l'app** (§9.3). Instancier proprement à ce moment-là est plus fiable que de réveiller un
   widget resté en vie derrière un voile pendant des heures.

**Transition de retour.** À la réévaluation qui détecte l'autorisation, la carte est instanciée et
apparaît en fondu (`motion-base`), la caméra déjà verrouillée sur la position. Aucun message de
succès : le retour de la carte **est** le message.

### 12.3 Séquence de demande

1. **Localisation de base** — demandée à la première entrée en partie, avec une amorce interne
   avant la boîte système : « Arpendo a besoin de ta position pour colorer les hexagones où tu
   marches. » Une amorce n'est pas une politesse : c'est ce qui évite le premier refus, et **deux
   refus consécutifs déclenchent le refus définitif d'Android** (§9.3).
2. **Notifications** — juste après, avec l'amorce du §10.3.
3. **Arrière-plan** — **jamais dans la même séquence.** Demandée quand le joueur revient dans l'app
   après une première session de jeu, avec l'amorce « Avec cette autorisation, la capture reprend
   toute seule après un redémarrage de ton téléphone. » Enchaîner trois demandes système à
   l'inscription maximise les refus, et le refus de la localisation d'arrière-plan est définitif au
   second essai.
4. **Exemption d'optimisation de batterie** — proposée depuis la ligne « Permissions » et dans le
   bandeau de niveau 2, jamais en interruption. C'est un réglage constructeur, pas une permission
   Android standard.

Cela fait **quatre autorisations distinctes** à obtenir, et la séquence ci-dessus les étale pour ne
pas aggraver le taux de refus.

---

## 13. États vides, chargement et erreur — table transverse

Récapitulatif consolidé de tous les états vides, de chargement et d'erreur du document.

### 13.1 États vides

| Où | Texte | Action |
|---|---|---|
| Historique des parties | « Aucune partie terminée pour l'instant. » + « Tes parties apparaissent ici une fois terminées. » | — |
| Liste des participants | « Personne d'autre pour l'instant. » | « Inviter » |
| Joueur sans capture | « aucune capture pour l'instant » *(§7.5, littéral)* | Ligne non tappable |
| Modale Activité (§7.2.2) | « Rien à relever pour l'instant. Le premier bilan tombe dans 5 minutes. » | — |
| Pile d'activité sur la carte (§7.2.1) | **Aucun texte** — la pile n'existe pas tant qu'il n'y a rien. Un état vide posé sur le jeu serait du bruit | — |
| Couche hexagones | Aucun texte — le vide est l'état de départ normal | — |
| Tableau des scores d'une partie abandonnée sans joueur | « Cette partie s'est terminée sans joueur. » | « Fermer » |

### 13.2 États de chargement

Règle générale : **squelette pour une structure connue, indicateur pour une action déclenchée par
le joueur.**

**Le délai de 600 ms ne s'applique qu'à l'attente subie.** Les deux cas ne posent pas le même
problème :

| Cas | Délai | Motif |
|---|---|---|
| **Attente subie** — le joueur n'a rien déclenché : chargement d'un écran, d'une liste | **600 ms** avant tout indicateur | En dessous, il clignote et fabrique une impression de lenteur là où il n'y en a pas |
| **Attente provoquée** — le joueur vient de taper un bouton | **Aucun délai**, l'indicateur remplace le libellé immédiatement | C'est l'accusé de réception du tap. 600 ms de bouton inerte se lisent comme un tap perdu, et le joueur retape |

| Où | Forme |
|---|---|
| Hexagones du viewport au pan/zoom (§7.1) | **Rien.** Les données déjà chargées restent affichées, les nouvelles arrivent par-dessus. Un indicateur à chaque déplacement de carte serait insupportable |
| Entrée en partie / création | Indicateur **dans le bouton**, feuille maintenue ouverte |
| Vérification du pseudo (§5.1) | Indicateur dans le champ, après 400 ms d'inactivité de frappe |
| Listes (joueurs, flux, historique) | Trois lignes en squelette |
| Page suivante d'une liste paginée | Indicateur 32 dp en pied de liste |
| Démarrage de l'app | Écran d'attente (§2.1), **aucun indicateur** — le bloc de marque tient ce rôle, et le délai du client HTTP borne l'attente |

### 13.3 États d'erreur

Trois formes, et pas une de plus :

| Forme | Quand | Exemple |
|---|---|---|
| **Bandeau** (§2.4) | État persistant, extérieur à l'action du joueur | Réseau, serveur, permission |
| **Message en ligne** | Échec local à un champ ou une liste | « Ce code n'existe pas. » |
| **Modale** | Échec bloquant et définitif seulement | Compte banni |

Toute erreur récupérable porte **« Réessayer »**. Aucune erreur n'affiche de code technique ni de
trace : ils partent à Sentry (§13.10), pas à l'écran.

**Une exception, nommée : le magasin qui ne s'ouvre pas** (§11.2). L'écran bloquant de mise à jour
ne montre alors ni message ni « Réessayer » — il n'y a rien à récupérer *dans* l'application, le
seul geste utile se fait dehors. La règle ci-dessus vaut pour tout le reste, et toute exception
nouvelle s'écrit ici **et** dans le § qui la porte : une exception inscrite d'un seul côté est
invisible au lecteur qui arrive par l'autre.

### 13.4 Pagination

Toutes les réponses d'API sont paginées et plafonnées (§12.4). Les trois listes concernées —
historique, flux d'activité, et la liste des participants au-delà de 10 lignes (jamais atteint au
MVP mais l'API le prévoit) — chargent la page suivante **à 3 lignes du bas**, jamais sur un bouton
« Charger plus ».

---

## 14. Récapitulatif des décisions

Index des décisions structurantes, avec leur renvoi. Il ne remplace aucune section : il sert à
retrouver où une décision est spécifiée.

| # | Sujet | Décision | Où |
|---|---|---|---|
| 1 | Placement des boutons d'action sur l'écran Jeu | Header, bouton d'action « Partie », Recentrer conditionnel, plus la pile d'activité qui n'est pas un contrôle | §7.0, §7.2 |
| 2 | Participants : modale ou panneau glissant | **Panneau glissant**, onglet « Joueurs » | §7.4 |
| 3 | Flux d'activité : modale ou panneau | **Ni l'un ni l'autre** — pile permanente en bas gauche de la carte, non interactive sauf sa ligne du bas, plus une modale au tap | §7.2.1, §7.2.2 |
| 4 | Dessin des motifs `pattern_id` | Recette de rendu spécifiée, **rien livré au MVP** | §15.2 |
| 5 | Style Mapbox de base | **Mapbox Standard**, libellés désactivés, slot `bottom` | §3.2 |
| 6 | Traitement visuel de la variation de score | Tuiles avant points · symétrie hausse/baisse · pastille de delta · bilan de retour | §7.1 |
| 7 | Rendu de l'agrégation au dézoom | Propriétaire majoritaire, opacité pleine, seuil de 5 % | §3.3 |
| 8 | Rendu de l'état « carte masquée » | Aucun widget Mapbox instancié | §12.2 |
| 9 | Animation de capture d'un hexagone | 300 ms de couleur + pulsation de contour + haptique, **jamais sur un lot** | §3.3 |
| 10 | Réapparition des écrans d'entrée en partie | **Une seule modale, la sécurité, une fois par compte.** La mention de visibilité est retirée de l'interface et portée par les documents juridiques | §6, §6.1 |
| 11 | **Retour visuel du plafond de 50 km/h** | Bandeau réactif partagé avec le verrou de vol | §7.3 |
| 12 | **Jeu d'icônes** | **Phosphor `Regular`**, 24 dp de dessin, 48 dp de cible ; trois silhouettes de sévérité non substituables | §1.8 |
| 13 | **Le mode sombre habille-t-il la carte ?** | **Oui** — `lightPreset: night` sur le style Standard, même canal de configuration que les libellés | §1.5, §3.2, §15.2 |
| 14 | **Comportement au clavier de l'écran Accueil** | Défilement, le bloc marque sort de l'écran, le bloc Créer ne remonte pas | §5 |
| 15 | **Course sur la couleur choisie** | La feuille reste ouverte, la pastille bascule en « Prise », aucune sélection à la place du joueur | §5.3 |
| 16 | **Texte du message de partage** *(seul vecteur d'acquisition au MVP)* | Trois lignes : code en gras, phrase de présentation, lien Play Store | §7.4 |
| 17 | **Tap sur un hexagone** | **Rien au MVP**, et aucun geste réservé sur la couche | §7.2 |

---

## 15. Faisabilité SDK

Le cadrage impose de signaler ce qui n'est pas réalisable plutôt que de le spécifier dans le vide.

### 15.1 Confirmé

| Élément | Base |
|---|---|
| `GeoJsonSource` + `FillLayer` / `LineLayer` pour la couche hexagones | `mapbox-flutter-patterns` — recommandation explicite au-delà de quelques centaines d'entités |
| Coloration par expression `['match', ['get', 'color_id'], …]` | Spécification de style Mapbox, expressions supportées par le SDK Flutter |
| `flyTo` avec durée, pour le glissement vers la tuile d'un joueur | `mapbox-flutter-patterns` |
| Puck de position et orientation par cap | `mapbox-flutter-patterns` |
| Notification permanente de service de premier plan, texte modifiable | Android standard |

### 15.2 À vérifier au démarrage de l'implémentation

Chacun de ces points a un repli spécifié, donc **aucun ne bloque la conception**. Ils sont à lever
avant d'écrire l'écran de jeu, pas avant de valider ce document.

| Point | Risque | Repli |
|---|---|---|
| **Slot `bottom`** et désactivation des libellés du style Standard depuis Flutter | L'insertion sous les routes est la décision §7.2 | Style personnalisé sans libellés + insertion par identifiant de calque, avec le repli déjà prévu au §7.2 |
| **`LocationPuck3D` et la coloration du modèle** | Le marqueur doit porter la couleur du joueur. Si le modèle n'est pas teintable, il faut 10 fichiers glTF | 10 fichiers glTF, ou repli sur un puck 2D teinté — dégradation acceptable, le marqueur reste identifiable |
| **Distinction glissement / pincement** dans les rappels de geste du `MapWidget` | Toute la machine à trois états de la caméra (§7.3) en dépend | Seuil de 24 dp sur un seul pointeur (§7.2) ; si le SDK ne donne pas le nombre de pointeurs, détection au niveau Flutter par-dessus le widget |
| **Transitions de propriété de peinture** (`fill-color-transition`) exposées côté Flutter | L'animation de capture (§3.3) | Couche éphémère dédiée à la tuile capturée, animée depuis Dart par un `Ticker` — garanti faisable, coût : une source et une couche de plus |
| **Motifs `fill-pattern`** | Le passage à 50 joueurs (§5.2) | Second `FillLayer` de motif au-dessus du calque de couleur, alimenté par la même source, `fill-pattern` piloté par `['get', 'pattern_id']` et 5 images monochromes à fond transparent. **Rien n'est livré au MVP** (§15.3) |
| **`lightPreset` du style Standard** exposé côté Flutter | Le mode sombre de la carte (§1.5 règle 2, §3.2) | Le mode sombre n'habille que le chrome et la carte reste en `day` — le comportement d'origine. Dégradé, jamais bloquant |
| **Métriques réelles de Roboto pour la ligne du header** | Le seuil de repli à `textScaler` 1,1 (§7.1) est calculé sur des largeurs estimées, avec 12 dp de marge | Mesurer la ligne à 1,0 sur l'écran de référence ; si elle déborde, le seuil descend, ou les unités « hex » et « pts » passent en `type-caption` plus étroit. **Jamais de `FittedBox`** (§7.1) |
| **Annonce de la pile d'activité par le lecteur d'écran** | `IgnorePointer` peut retirer la pile de l'arbre sémantique selon la version de Flutter (§7.2.1) | Envelopper la pile dans un `Semantics` explicite en dehors de l'`IgnorePointer`. Test d'accessibilité obligatoire, le point ne se vérifie pas à l'œil |

### 15.3 Recette de rendu des motifs — pour plus tard, pas pour le MVP

Le cadrage veut pouvoir passer de 10 à 50 joueurs sans refonte (§5.2). La recette est écrite ici
pour que la promesse tienne ; **rien n'est livré au MVP**, parce qu'un calque qui ne dessine rien
est un composant qui n'existe qu'au cas où.

- **Ne pas** produire 50 images (10 couleurs × 5 motifs) : la couleur serait dupliquée dans les
  ressources, et la palette cesserait d'avoir une seule source de vérité.
- **Ajouter un second `FillLayer` de motif** au-dessus du calque de couleur, alimenté par la même
  source, avec `fill-pattern` piloté par `['get', 'pattern_id']` et **5 images monochromes à fond
  transparent**. La couleur vient du calque du dessous, le motif du calque du dessus.
- Coût le jour venu : 5 fichiers, une couche, zéro migration de données, zéro changement de
  palette.

---

---

## 16. Deux contraintes à ne pas rouvrir

1. **`accent` ne peut pas être clair.** Les dix couleurs joueur occupent toute la roue chromatique
   entre L 0,470 et 0,761 : **aucune teinte au-dessus de L 0,40 n'est à ΔE ≥ 15 des dix.** Tout
   accent de mode clair est donc sombre, et tout accent de mode sombre est pâle. Ce n'est pas un
   goût, c'est le résultat d'un balayage complet de l'espace OKLCH.
2. **La palette joueur (§3.1) ne fait pas partie de l'identité de marque.** Elle est contrainte par
   l'accessibilité et validée. Toute modification future doit repasser le validateur en mode
   `--pairs all` **et** revérifier la séparation de l'accent.

Le raisonnement complet, les directions écartées et les calculs de séparation sont dans
`03-identite-visuelle.md`.
