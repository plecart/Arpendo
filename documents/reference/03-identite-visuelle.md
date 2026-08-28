# Arpendo — Identité visuelle

> **Statut : clos.** Direction **« Relevé »** retenue le 13 août 2026, et **ses valeurs sont la
> seule palette du projet** — reprises au §1.5 de `02-specification-ux.md`, qui fait foi. Les deux
> directions écartées sont résumées au §2 **sans leurs valeurs**, pour qu'aucun autre jeu de
> couleurs ne subsiste dans le projet. Les répercussions du §4 sont appliquées.
> **Portée :** couleur d'accent et jetons de chrome, typographie, logotype, icône d'app, marqueur 3D,
> ton d'écriture. MVP, Android d'abord, français seul.
> **Source normative :** `01-cadrage.md` et `02-specification-ux.md`, tous deux clos.
> **Entrée :** `brief-identite-visuelle.md`, rempli le 13 août 2026.
> **Ce document ne décide plus rien.** Il conserve le raisonnement, les calculs de séparation et
> les ressources SVG. **En cas de divergence avec `02-specification-ux.md`, c'est elle qui fait
> foi.**

---

## 0. Le fait qui commande tout le reste

Avant de choisir quoi que ce soit, une question devait être tranchée par le calcul : **où reste-t-il
de la place chromatique ?** Les dix couleurs joueur du §3.1 occupent la roue presque entière dans la
bande de clarté L 0,470 – 0,761. J'ai balayé l'espace OKLCH complet — 13 bandes de clarté × 12
familles de teinte × toutes les chromas atteignables en sRGB — en mesurant pour chaque point sa
distance minimale aux dix.

**Résultat : au-dessus de L 0,40, il n'existe aucune teinte à ΔE ≥ 15 des dix couleurs joueur.**

```
ΔE minimal atteignable, par bande de clarté × famille de teinte (chroma libre 0,02–0,32)
L        rouge  orange  ambre  olive   vert  vert-eau  cyan  bleu-cyan  bleu  indigo  violet  magenta
0.20      30.2   31.0   31.6   31.6   31.3    31.1    31.0    31.1     30.6   30.2    29.9    29.9
0.30      21.8   23.7   24.0   22.6   21.8    21.6    21.5    21.8     22.2   21.7    21.4    21.4
0.35      18.1   19.6   21.0   18.4   17.4    17.1    17.0    17.3     18.4   19.2    17.6    17.7
0.40      15.3   16.4   17.3   15.3   13.3    12.9    12.8    13.2     14.6   18.8    14.7    14.8
0.50      12.9   13.3   13.2   12.7    8.8     8.2     8.1     8.6     11.7   11.7    12.3    11.9
0.60      13.9   11.4   10.7   10.4   10.7    12.4    12.5    13.2     14.3   15.2    15.9    15.8
0.70      10.5   10.5   11.0   11.9   11.5    10.7    10.1    10.0     12.1   11.7    12.2    12.0
0.80      12.4   12.3   12.3   13.6   11.5    10.2     9.1     9.0      9.5   12.2    13.2    12.1
```

Trois conséquences, non négociables et communes aux trois directions :

1. **L'accent en mode clair est nécessairement sombre** (L ≤ 0,40). Ce n'est pas un parti pris
   esthétique, c'est le seul espace libre. La direction « Topographique » du questionnaire décrivait
   déjà « une seule couleur d'accent sombre » — le calcul confirme qu'il n'y avait pas d'alternative.
2. **En mode sombre, l'accent doit remonter au-dessus de L 0,84**, en chroma modérée. Un accent
   sombre serait invisible sur une surface sombre, et un accent de clarté moyenne retomberait dans
   la bande des joueurs. Les accents sombres des trois directions sont donc des teintes pâles, pas
   des versions « éclaircies » de l'accent clair.
3. **L'état pressé s'inverse selon le mode.** En clair il fonce ; **en sombre il éclaircit**
   (voile blanc de 16 %). Foncer un accent pâle en mode sombre le ferait retomber dans la bande des
   joueurs — vérifié, ΔE 11 à 12, échec. C'est la méthode des *state layers* de Material 3, et ici
   ce n'est pas une préférence : c'est la seule sortie.

### 0.1 Ce que le questionnaire a produit comme lecture

| Signal | Source | Conséquence retenue |
|---|---|---|
| Sobre 2, calme 2, discret 1, intemporel 1, intérieur « minimaliste » | §4 | Chrome nu, une seule couleur d'accent, aucune surface colorée large |
| Nature/dehors 1, « arpenter = la marche, l'Auvergne, un champ de baies » | §4.2, §12.1 | Registre du dehors, pas du tableau de bord |
| Artisanal→technique 4, « pantalon de costume avec t-shirt » | §4, §1.8 | Structure formelle, port décontracté. Ni raide, ni bricolé |
| Rejet : trop de couleurs, dégradés, tout arrondi, ombres marquées, emojis, « AI slop » | §2.2, §2.4 | Aucun dégradé, aucune ombre décorative, aucun emoji, arrondis sobres |
| Duel 7 A — une seule couleur vive, le reste neutre | §3 | Un accent unique, jamais deux |
| Duel 17 B — contraste doux ; 10.1 — « beau » plutôt que « lisible » | §3, §10 | **Contraste doux dans le décor, dur dans l'information.** Voir §0.2 |
| Duel 8 B — fond sombre ; mais §2.2 rejette « fond sombre imposé » | §3, §2.2 | Thème clair par défaut, sombre disponible et **suivant le réglage système**, jamais imposé |
| Duel 10 B — tout à plat ; mais §3.4 impose un marqueur 3D | §3 | Aucune ombre portée. L'élévation passe par le contour 1 dp déjà prévu au §1.3 |
| Duel 13 A + duel 16 B — géométrique **et** organique | §3 | Formes régulières, tracé légèrement irrégulier |
| 9.3 — hexagone **et** « une trace, un pas, un chemin » | §9 | Le chemin est le sujet du signe, l'hexagone en est le résultat |
| 5.2 — le soir, on veut lire ce qui s'est passé | §5 | La densité va dans la feuille Partie, pas sur la carte |
| 5.3 — plein soleil : seuls les hexagones doivent rester lisibles | §5 | Le contraste dur est réservé au texte et aux contours d'hexagone |
| 7.1 B + 7.2 A + 7.3 arbitre | §7 | **Arbitre neutre, mais humain dans la mauvaise nouvelle.** Voir §0.3 |
| 6.1 pion sans visage, 6.3 « c'est moi », « une forme qui flotte, un tic-tac » | §6 + précisions orales | Capsule flottante, sans membres, avec un point d'ancrage pour les futurs accessoires |
| La capture d'écran est un livrable marketing | précision orale | L'écran Jeu doit être frappant sur une fiche Play Store |

### 0.2 La règle de contraste, arbitrée

Tu as coché « beau » plutôt que « lisible » (10.1) et « contraste doux » (duel 17), tout en disant
que sous le soleil, seuls les hexagones doivent survivre (5.3). Ces réponses ne s'opposent pas si on
sépare le décor de l'information :

- **Décor — contraste doux.** Surfaces, séparateurs, contours, fonds teintés se parlent en nuances
  rapprochées. C'est ce qui donne le calme.
- **Information — contraste dur, sans exception.** Tout texte reste ≥ 4,5:1 sur son fond, et le
  contour d'hexagone conserve son rôle de relief exigé par le §3.1. C'est gratuit
  esthétiquement — un texte à 15:1 n'est pas plus laid qu'un texte à 3:1 — et c'est ce qui empêche
  l'app de devenir illisible à midi.

Les contrastes de chaque direction sont mesurés et reportés dans son tableau de jetons.

### 0.3 La règle de ton, arbitrée

Tu as choisi la formulation **conversationnelle** pour la mauvaise nouvelle (7.1 B : « On a perdu le
réseau. Tes pas ne comptent plus pour l'instant. ») et la formulation **factuelle** pour la bonne
(7.2 A : « Bob passe en tête. »), en te décrivant comme voulant un arbitre (7.3).

C'est une règle précise, et elle est inhabituelle dans le bon sens : **l'app est plate quand tout va
bien, et elle explique quand quelque chose ne va pas.** L'inverse — s'enthousiasmer sur un succès et
rester sèche sur une panne — est le défaut standard des applications de jeu. Les trois directions
appliquent cette règle ; elles diffèrent par le registre, pas par le principe.

---

## 1. Direction A — **Relevé**

> **Principe.** *Une carte de randonnée qu'on aurait apprise par cœur : du papier, un trait, et la
> couleur réservée à ce qui compte — le territoire.*

Le chrome se retire au maximum. Aucune surface pleine autre que la carte, aucun bloc de couleur,
des séparateurs plutôt que des cartes, un fond de papier crème qui réchauffe l'écran sans le teinter.
La couleur, dans cette direction, appartient exclusivement aux joueurs : l'accent vert forêt est si
sombre qu'il se lit comme de l'encre plutôt que comme une couleur.

### 1.1 Couleur d'accent

| Rôle | Hex | OKLCH (L, C, H) |
|---|---|---|
| `accent` | **`#123D1E`** | 0,321 · 0,072 · 150° |
| `accent-pressed` (état pressé, mode clair) | **`#052D11`** | 0,261 · 0,066 · 150° |
| `accent-light` (fond teinté, mode clair) | **`#E8EFE9`** | 0,945 · 0,012 · 150° |
| `accent` (mode sombre) | **`#C9F7BE`** | 0,930 · 0,090 · 140° |
| `accent-pressed` (mode sombre — voile blanc 16 %) | **`#D2F8C8`** | 0,942 · 0,077 · 140° |
| `accent-light` (fond teinté, mode sombre) | **`#23331F`** | 0,300 · 0,040 · 140° |

### 1.2 Vérification ΔE — calcul exécuté

**Distances individuelles de l'accent aux dix couleurs joueur** (OKLab ×100, vision normale) :

```
                          accent #123D1E    accent sombre #C9F7BE
  vs rouge clair #E9878A        44.4               27.1
  vs brique      #BD3216        30.4               45.8
  vs ocre        #A6841D        32.5               31.5
  vs vert pomme  #97C425        45.6               19.4  <- pire
  vs émeraude    #007559        18.3  <- pire      43.3
  vs cyan        #56C4CA        44.5               19.5
  vs bleu        #3B6DF4        35.9               44.3
  vs lilas       #BE85F9        46.5               33.3
  vs prune       #773B95        26.5               51.8
  vs magenta     #EB31A5        44.5               43.2
```

**Accent clair : ΔE min = 18,3. Accent sombre : ΔE min = 19,4. Plancher exigé : 15. PASS.**
Dérivés vérifiés : `accent-pressed` clair 24,2 · `accent-light` clair 20,8 · `accent-pressed`
sombre 20,2 · `accent-light` sombre 21,0. Tous ≥ 15.

**Sortie du validateur** — `scripts/validate_palette.py` du skill `dataviz`, mode `--pairs all`
(celui des cartes, où n'importe quelles deux couleurs peuvent se toucher), palette = les 10 couleurs
joueur **+ l'accent**, surface `#F1EDE2` :

```
Palette (light, surface #F1EDE2, categorical): 11 slots
  [FAIL] Lightness band         outside band: [["#123D1E",0.321]]
  [FAIL] Chroma floor           below floor (reads gray): [["#123D1E",0.072]]
  [PASS] CVD separation         worst all-pairs #56C4CA↔#E9878A ΔE 9.1 (deutan) · tritan 10.0
  [PASS] Normal-vision floor    worst all-pairs #A6841D↔#E9878A ΔE 17.1 (normal)
  [WARN] Contrast vs surface    below 3:1 — relief required: [["#E9878A",2.16],["#97C425",1.75],
                                ["#56C4CA",1.77],["#BE85F9",2.27]]
```

**Lecture honnête de ce rapport.** Les deux `FAIL` portent sur l'accent et sont **attendus** : ce
sont les contrôles « bande de clarté » et « plancher de chroma », qui vérifient qu'une couleur est
un *slot de série de données* comparable aux autres. L'accent n'est pas une onzième série — il est
délibérément hors de la bande, et c'est précisément ce qui le rend non confondable. Les deux
contrôles qui gouvernent la confusabilité passent tous les deux.

**La preuve décisive est dans la ligne `Normal-vision floor`** : la pire paire des 55 reste
`#A6841D ↔ #E9878A` à ΔE 17,1 — **exactement la même paire et la même valeur que dans le rapport
de référence du §3.1 à 10 couleurs.** Ajouter l'accent n'a créé aucune paire plus proche : il est
donc à plus de 17,1 de chacune des dix.

**Le `WARN` de contraste est inchangé** par rapport au §3.1 (2,22 / 1,80 / 1,82 / 2,33 sur
`#F2F0EB`, contre 2,16 / 1,75 / 1,77 / 2,27 sur `#F1EDE2`). Il reste traité par le contour
d'hexagone du §3.3. La nouvelle surface ne dégrade rien :

```
=== 10 joueurs seuls sur #F1EDE2 (nouvelle surface-dim) ===
  [PASS] Lightness band         all 10 inside L 0.43–0.77
  [PASS] Chroma floor           all 10 >= 0.1
  [PASS] CVD separation         worst all-pairs #56C4CA↔#E9878A ΔE 9.1 (deutan) · tritan 10.0
  [PASS] Normal-vision floor    worst all-pairs #A6841D↔#E9878A ΔE 17.1 (normal)
  [WARN] Contrast vs surface    4 couleurs sous 3:1 -> relief obligatoire
```

Structure identique au rapport du §3.1. **La palette joueur n'est pas touchée et son rapport reste
valide.**

### 1.3 Typographie

**Roboto**, la police système Android. Assumée, sans réserve.

- **Coût d'APK : 0 octet.** Aucune ressource embarquée, aucun chargement, aucun *flash of unstyled
  text*.
- **Couverture française : totale**, y compris `œ`, `Œ`, `Æ`, `«` `»`, et les capitales accentuées
  `À É È Ê Ç Ù`.
- **Justification par tes réponses :** duel 1 = A (« police système, sobre, invisible ») et
  10.3 = « la solution la plus simple à mettre en œuvre ». Dans cette direction, l'identité est
  portée par la couleur et le trait ; la typographie doit se taire.
- **Échelle inchangée** (§1.2 de la spec). Traitement propre à la direction : graisse 400 par
  défaut, les autres jetons montant selon le tableau du §1.2 sans dépasser 600 sauf
  `type-display` ; interlettrage `+0,01 em` sur `type-caption` pour la tenue des petites tailles au
  soleil ; chiffres **tabulaires** (`fontFeatures: ['tnum']`) sur le score et le timer, pour que les
  valeurs ne dansent pas quand elles changent.
- Le logotype n'est **pas** composé en Roboto : c'est un dessin (§1.5), livré en SVG.

### 1.4 Jetons de chrome

**Mode clair**

| Token | Valeur | Vérification |
|---|---|---|
| `surface` | `#FDFBF6` | papier blanc, très légèrement chaud |
| `surface-dim` | `#F1EDE2` | crème ; rapport joueur revalidé ci-dessus |
| `on-surface` | `#1A1D18` | **16,47:1** sur `surface` |
| `on-surface-muted` | `#5C6157` | 6,15:1 sur `surface` · 5,44:1 sur `surface-dim` |
| `outline` | `#C7C3B5` | contours et séparateurs, 1 dp |
| `scrim` | `#1A1D18` à 40 % | inchangé en nature |
| `accent` | `#123D1E` | blanc dessus : **12,27:1** |
| `accent-pressed` | `#052D11` | — |
| `accent-light` | `#E8EFE9` | `on-surface` dessus : 14,56:1 |
| `danger` | `#B3261E` | 6,32:1 sur `surface` — voir §1.9 |
| `warning` | `#7A4F00` | 6,89:1 sur `surface` — assombri, voir §1.9 |

**Mode sombre**

| Token | Valeur | Vérification |
|---|---|---|
| `surface` | `#1A1E1A` | |
| `surface-dim` | `#101310` | |
| `on-surface` | `#EDEAE0` | **14,02:1** sur `surface` |
| `on-surface-muted` | `#9CA096` | 6,33:1 sur `surface` |
| `outline` | `#3A403A` | |
| `scrim` | `#000000` à 55 % | plus dense qu'en clair : un voile de 40 % ne sépare rien sur fond sombre |
| `accent` | `#C9F7BE` | **15,62:1** sur `surface-dim` ; texte `#101310` dessus : 15,62:1 |
| `accent-pressed` | `#D2F8C8` | 16,03:1 |
| `accent-light` | `#23331F` | |
| `danger` | `#F2B8B5` | 9,88:1 sur `surface` |
| `warning` | `#F5C77E` | 10,73:1 sur `surface` |

> **La carte suit le mode.** Le style Mapbox Standard expose un `lightPreset`
> (`dawn` · `day` · `dusk` · `night`) sur l'import de style, par **le même appel de configuration**
> que la désactivation des libellés retenue en `02-specification-ux.md` §3.2 : `night` en mode
> sombre, `day` sinon. Le coût est d'une propriété, pas d'un style à maintenir — et un jeu de
> marche joué le soir afficherait sans cela une carte blanche plein écran sous un chrome sombre,
> c'est-à-dire l'exact cas d'usage où le mode sombre sert.
>
> **`accent` en mode sombre garde néanmoins son plancher de ΔE 15.** La couche hexagones n'est
> **pas** affectée par le `lightPreset` — elle porte les couleurs joueur, pleines, dans les deux
> modes — donc le bouton « Recentrer » flotte toujours au-dessus d'aplats colorés. Seul le fond
> neutre s'assombrit.
>
> **Le rapport du validateur de la palette joueur est à rejouer sur le fond sombre.** Il a été
> calculé contre un fond clair (`#F1EDE2`). Sur un fond `night`, les quatre couleurs en `WARN` de
> contraste cessent de l'être — ce sont les plus claires — et ce sont les trois plus sombres
> (`#BD3216`, `#007559`, `#773B95`) qui passent sous 3:1. Le contour d'hexagone reste le relief qui
> traite le cas. Inscrit en `02-specification-ux.md` §15.2.

### 1.5 Logotype et icône d'app

**Le signe : des courbes de niveau dont le sommet est un hexagone.**

Trois tracés emboîtés, de plus en plus serrés, exactement comme un relief sur une carte
topographique. Les deux extérieurs sont des courbes libres et légèrement irrégulières — c'est ton
duel 16, l'organique. Le troisième, au centre, s'est refermé en hexagone régulier — c'est ton
duel 13, le géométrique. L'hexagone n'est **pas** le sujet du signe : il en est le point d'arrivée,
le sommet du relief. On lit d'abord une carte, ensuite seulement un hexagone.

C'est la réponse à ta double contrainte : l'hexagone est indispensable puisque le jeu est bâti
dessus, mais il ne doit pas être ce qu'on voit en premier.

```svg
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Arpendo — courbes de niveau refermées sur un hexagone">
  <g fill="none" stroke="#123D1E" stroke-linejoin="round" stroke-linecap="round">
    <path d="M32 4.5 C46.5 6 58.5 16.5 59 30.5 C59.5 45 47 59.5 32 60
             C16.5 60.5 5 46.5 5 31.5 C5 16.5 18 3 32 4.5 Z"
          stroke-width="2" opacity="0.30"/>
    <path d="M32 14 C42.5 15 50.5 21.5 50.5 31.5 C50.5 41.5 42 50.5 32 50.5
             C21.5 50.5 13.5 42 13.5 31.5 C13.5 21.5 21.5 13 32 14 Z"
          stroke-width="2" opacity="0.58"/>
  </g>
  <path d="M32 21.4 L40.6 26.4 L40.6 36.4 L32 41.4 L23.4 36.4 L23.4 26.4 Z"
        fill="#123D1E"/>
</svg>
```

**Le logotype.** `Arpendo` en capitale initiale (ta réponse 9.1), lettres dessinées sur une base
linéale à contraste faible, terminaisons droites, `p` et `d` à hampes légèrement raccourcies pour
que le mot forme un bloc horizontal stable. Interlettrage `+0,02 em`. Le signe se place **à gauche
du mot**, hauteur égale à la hauteur de capitale.
L'accroche « prends du terrain » vient **sous** le mot, en `type-body`, `on-surface-muted`, bas de
casse, sans point final — discrète, conformément à ta réponse 9.2.

```svg
<svg viewBox="0 0 260 64" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Arpendo — prends du terrain">
  <g transform="translate(0,6) scale(0.8)">
    <g fill="none" stroke="#123D1E" stroke-linejoin="round" stroke-linecap="round">
      <path d="M32 4.5 C46.5 6 58.5 16.5 59 30.5 C59.5 45 47 59.5 32 60
               C16.5 60.5 5 46.5 5 31.5 C5 16.5 18 3 32 4.5 Z"
            stroke-width="2.4" opacity="0.30"/>
      <path d="M32 14 C42.5 15 50.5 21.5 50.5 31.5 C50.5 41.5 42 50.5 32 50.5
               C21.5 50.5 13.5 42 13.5 31.5 C13.5 21.5 21.5 13 32 14 Z"
            stroke-width="2.4" opacity="0.58"/>
    </g>
    <path d="M32 21.4 L40.6 26.4 L40.6 36.4 L32 41.4 L23.4 36.4 L23.4 26.4 Z"
          fill="#123D1E"/>
  </g>
  <text x="66" y="34" font-family="Roboto, Arial, sans-serif" font-size="27"
        font-weight="500" letter-spacing="0.5" fill="#123D1E">Arpendo</text>
  <text x="67" y="52" font-family="Roboto, Arial, sans-serif" font-size="13"
        font-weight="400" fill="#5C6157">prends du terrain</text>
</svg>
```

**L'icône d'app.** Forme **et** couleur (ta réponse 9.4). Fond `surface-dim` crème, les deux courbes
de niveau en vert forêt à opacité réduite, l'hexagone plein au centre — décalé de 2 % vers le haut
pour compenser l'illusion optique de chute dans un masque rond. Aucun dégradé, aucune ombre.
À 48 px, les deux courbes fusionnent visuellement en une auréole ; **l'hexagone plein reste le
signal**, et c'est ce qui rend l'icône reconnaissable dans un tiroir rempli.

```svg
<svg viewBox="0 0 108 108" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Icône Arpendo — direction Relevé">
  <rect width="108" height="108" rx="24" fill="#F1EDE2"/>
  <g fill="none" stroke="#123D1E" stroke-linejoin="round" transform="translate(0,-2)">
    <path d="M54 16 C74 18 90 32 90 54 C90 76 74 92 54 92
             C34 92 18 76 18 54 C18 32 34 14 54 16 Z"
          stroke-width="3" opacity="0.26"/>
    <path d="M54 30 C68 31 78 41 78 54 C78 67 68 78 54 78
             C40 78 30 67 30 54 C30 41 40 29 54 30 Z"
          stroke-width="3" opacity="0.52"/>
  </g>
  <path d="M54 36 L67 43.5 L67 58.5 L54 66 L41 58.5 L41 43.5 Z" fill="#123D1E"/>
</svg>
```

### 1.6 Le marqueur 3D

**Silhouette.** Une **capsule verticale posée sur sa pointe arrondie**, proportions 1 : 1,7
(largeur : hauteur) — la forme de galet dressé que tu as décrite comme un « tic-tac ». Aucun
membre, aucun visage, aucune articulation : rien à animer, donc rien qui puisse mal s'animer. Elle
**flotte** à 0,25 fois sa hauteur au-dessus du sol et respire d'un mouvement vertical de ±3 % sur un
cycle de 2,4 s. Le flottement remplace la marche ; c'est ce qui permet de suivre le GPS sans jamais
poser un pied.

**Niveau de détail.** 320 à 400 triangles. Une seule mesh fermée, un seul matériau, sans normal map.
Ombrage `KHR_materials_unlit` — un aplat pur — plus un liseré sombre obtenu par la technique du
*backface hull* : une copie de la mesh agrandie de 3 %, normales inversées, matériau `#1A1D18`.
C'est un contour propre, indépendant de l'éclairage de la scène, et c'est ce qui donne le trait
dessiné de la direction. Aucune ombre portée, aucun spéculaire : ta réponse 2.2 les exclut.

**Comment il porte la couleur du joueur — et pourquoi pas autrement.**
Tu m'as laissé proposer (6.4). Il y a un piège que la question ne dit pas : **le joueur se tient
presque toujours sur sa propre tuile, donc sur sa propre couleur.** Un marqueur entièrement teinté
disparaîtrait dans son propre territoire à l'instant précis où on le regarde.

La répartition retenue :

| Zone | Traitement | Part |
|---|---|---|
| Coque haute | `surface` — crème `#FDFBF6` | ~55 % |
| **Bandeau bas** | **couleur du joueur, aplat pur** | ~45 % |
| Liseré | `#1A1D18`, 3 % d'échelle | contour continu |
| Disque de contact au sol | `#1A1D18` à 18 %, ellipse aplatie, **sans flou** | 20 px |

La coque crème est l'invariant : quelle que soit la tuile sous lui, le marqueur porte une masse
claire qui le détache. La couleur est en bas, là où elle touche visuellement la tuile — le marqueur
semble prendre sa teinte du sol qu'il occupe, ce qui est exactement ce que le jeu raconte.

**Lisibilité à 40 px sur carte colorée.** Trois mécanismes, tous indépendants de la teinte :

1. **La coque crème** est plus claire que les dix couleurs joueur (L 0,98 contre 0,470–0,761). Le
   contraste de clarté fonctionne même sur la tuile de même teinte.
2. **Le liseré sombre continu** sépare le marqueur de tout fond, clair comme foncé. C'est le même
   principe que le contour d'hexagone du §3.3, et pour la même raison.
3. **Le disque de contact** ancre la forme au sol et crée une seconde rupture de valeur sous elle.

À 40 px, la silhouette occupe 24 × 40 px : la capsule reste une capsule, le bandeau reste lisible
comme une bande de couleur, et l'ensemble se distingue à la forme avant même la couleur.

**Le point d'ancrage pour le MVP 2.** Le sommet de la capsule est **plat sur 6 px de diamètre** —
imperceptible à l'œil, mais c'est une surface d'appui. Un accessoire futur (chapeau, casque,
antenne) s'y visse par un nœud nommé `socket_top` dans le glTF, sans retoucher la mesh de base. Le
prévoir maintenant coûte une face ; le rétrofitter coûterait le modèle entier.

**Vue de face** *(hexagone de fond = tuile du joueur, pour montrer le cas le plus défavorable)* :

```svg
<svg viewBox="0 0 120 140" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Marqueur Relevé, vue de face, sur une tuile de sa propre couleur">
  <defs>
    <clipPath id="relCaps">
      <rect x="36" y="18" width="48" height="86" rx="24"/>
    </clipPath>
  </defs>
  <path d="M60 6 L104 31 L104 81 L60 106 L16 81 L16 31 Z" fill="#3B6DF4" opacity="0.9"/>
  <path d="M60 6 L104 31 L104 81 L60 106 L16 81 L16 31 Z" fill="none"
        stroke="#161616" stroke-opacity="0.25" stroke-width="1.5"/>
  <ellipse cx="60" cy="116" rx="21" ry="5.5" fill="#1A1D18" opacity="0.18"/>
  <g clip-path="url(#relCaps)">
    <rect x="36" y="18" width="48" height="86" fill="#FDFBF6"/>
    <rect x="36" y="66" width="48" height="38" fill="#3B6DF4"/>
  </g>
  <rect x="36" y="18" width="48" height="86" rx="24" fill="none"
        stroke="#1A1D18" stroke-width="3"/>
  <line x1="52" y1="19.5" x2="68" y2="19.5" stroke="#1A1D18"
        stroke-width="1" opacity="0.35"/>
</svg>
```

### 1.7 Ton d'écriture

**Le registre : le carnet de relevé.** Phrases courtes, verbes au présent, aucun point
d'exclamation, aucune interjection, aucun superlatif. On énonce ce qui est. Quand quelque chose ne
marche pas, on dit **ce qui se passe** puis **ce qu'on peut faire** — jamais l'inverse, et jamais
d'excuse.

**Trois textes de la spécification, avant et après la passe de ton du 28 août 2026 (#29) :**

| § | Avant | En vigueur |
|---|---|---|
| §2.4, priorité 6 | « Capture en pause — tes déplacements ne comptent plus » | **« Coupure depuis 5 min. Tes pas ne comptent pas pour l'instant. »** — sans nommer de cause : le bandeau vaut pour le réseau absent comme pour le serveur en panne, que le cadrage §10.3 impose de distinguer |
| §7.4, modale de départ | « Tu perds tes 1 247 hexagones et tes 124 700 points. Cette action est irréversible. » | **« Tu laisses 1 247 hexagones derrière toi. Ils redeviennent libres, et tu ne les récupéreras pas. »** |
| §13.1, flux vide | « Rien ne s'est encore passé. Le premier bilan arrive dans 5 minutes. » | **« Rien à relever pour l'instant. Le premier bilan tombe dans 5 minutes. »** |

Les trois obéissent à la règle du §0.3 : la panne s'explique, la perte se constate sans dramatiser,
l'attente se date.

### 1.8 Ce que cette direction rend impossible ou difficile

1. **L'accent partage sa famille de teinte avec le joueur émeraude.** ΔE 18,3, donc validé — mais
   c'est la marge la plus étroite des dix distances de cette direction, et l'écart tient surtout à
   la clarté (L 0,321 contre 0,500). Quand le joueur 5 est en partie, l'œil verra du vert dans le
   chrome **et** du vert sur la carte. Ils ne se confondent pas ; ils se ressemblent.
2. **Le crème plafonne le contraste maximal.** `surface` à `#FDFBF6` au lieu du blanc pur coûte
   environ 3 % de contraste sur tout l'écran. Négligeable en valeur, mais c'est un plafond
   définitif : cette direction ne pourra jamais aller plus loin en lisibilité.
3. **Aucune place pour un second niveau de couleur.** Un jour, si le produit veut signaler un
   événement, une saison, un mode spécial, il n'y a plus de couleur libre — l'accent est déjà le
   seul survivant du balayage, et la palette joueur occupe le reste. Il faudra passer par la forme
   ou le mouvement.
4. **C'est la direction la moins immédiatement remarquable des trois.** Sur une fiche Play Store, à
   côté de captures saturées, une carte crème avec des taches de couleur demande une seconde de
   plus pour être comprise. Elle gagne à l'usage, pas à la vignette.
5. **Le liseré du marqueur 3D est un coût de rendu réel.** La technique du *backface hull* double
   le nombre de triangles du modèle. Sur 400 triangles c'est indolore ; c'est à savoir si le modèle
   se complexifie un jour.

### 1.9 Note sur `danger` et `warning`

En mesurant l'accent, j'ai contrôlé les autres jetons de couleur de la spec par acquit de
conscience. **Deux collisions non signalées au §1.5 :**

```
danger   #B3261E  ΔE  3,1 du brique  #BD3216   <-- quasi-identique
warning  #8A5A00  ΔE 12,2 du brique  #BD3216   <-- sous le plancher
```

`#B3261E` et le brique joueur sont pratiquement la même couleur. Ce n'est **pas** aussi grave que
la collision de l'accent, pour une raison précise : `danger` et `warning` n'apparaissent jamais en
remplissage sur la carte — ce sont des couleurs de texte et d'icône sur `surface`, dans des feuilles
et des modales. Le joueur ne les voit jamais côte à côte avec un territoire.

**Et il n'existe pas de correction possible sans perdre plus qu'on ne gagne** : le rouge est une
convention universelle pour le danger, et tout rouge de valeur moyenne est proche du brique, qui
*est* un rouge sombre. J'ai cherché — le meilleur candidat à ΔE ≥ 15 est `#684231`, un brun boueux
qui ne dit plus « danger » du tout.

**Décision : garder `danger` = `#B3261E`, assombrir légèrement `warning` à `#7A4F00`** (contraste
7,05:1 au lieu de 4,58:1, utile au soleil), et **inscrire au §5 la règle qui rend la collision
inoffensive** : ni `danger` ni `warning` ne peuvent servir de couleur de remplissage sur la couche
carte. Cette règle vaut pour les trois directions.

---

## 2. Les deux directions écartées

> **Leurs valeurs ont été retirées de ce document le 13 août 2026.** Elles avaient été spécifiées
> aussi complètement que « Relevé » — accent, jetons de chrome en clair et en sombre, typographie,
> logotype, marqueur, ton d'écriture. **Ces tableaux ont été supprimés**, parce qu'un document qui
> présente trois jeux de couleurs également crédibles fait choisir le mauvais. **Le projet ne
> contient plus qu'une seule palette : celle du §1, reprise au §1.5 de la spécification UX.**
>
> Ce qui suit conserve ce qui sert encore : **pourquoi** elles ont été écartées.

### 2.1 « Cadastre » — l'aplat

*Un plan de parcelles : des aplats, des limites franches, et rien d'autre. La carte et l'interface
dessinées par la même main, avec le même outil.* Neutres purs, angles francs, aucune texture,
hexagone plein, accent terre brûlée. C'était la seule direction à tenir la promesse « les hexagones
et l'interface parlent le même langage », le seul trait que le questionnaire avait retenu de la
direction « Signalétique ».

**Écartée sur trois motifs cumulés.** Elle embarquait une police de marque — environ 128 Ko d'APK
et une dépendance à maintenir, contre le §2 du cadrage qui veut un MVP volontairement petit. Son
marqueur était le moins lisible des trois sur sa propre tuile : le corps entièrement teinté ne se
détachait que par une calotte blanche. Et c'était la direction la plus froide, alors que le
questionnaire répondait « chaleureux 2 ».

### 2.2 « Terrain » — le jeu désamorcé

*La vitalité d'un jeu débarrassée de ses tics : rien n'est rond, rien ne s'enfonce, rien n'est
énorme, mais tout est franc.* Fond clair franc, formes pleines, angles nets, et le seul accent
réellement **vif** que le balayage du §0 laissait disponible — un indigo profond.

**Écartée sur deux motifs, dont un mesuré.** Son accent était un bleu, et le joueur 7 est un bleu :
séparés de ΔE 18,7, donc non confondables au sens de la mesure, mais l'écran aurait contenu deux
bleus dont l'un est un bouton et l'autre un territoire — le défaut exact que le §1.5 de la
spécification demandait de corriger, corrigé sur le fond et seulement atténué sur la forme. En mode
sombre, son accent devenait **la pire paire du jeu de couleurs**, à ΔE 8,3 du cyan joueur en
protanopie, contre un plancher de 8 et contre 9,1 pour les deux autres directions. S'ajoutait un
motif de goût : un indigo saturé sur blanc bleuté décrit aussi beaucoup d'applications de 2026, et
la réponse 10.2 du questionnaire demandait « une identité qu'on garde dix ans ».

**Le verdict du porteur, à la vue des trois maquettes :** *« la couleur Terrain me semble un peu
trop flashy, un peu trop bleu ».*

---

## 3. Pourquoi « Relevé »

**Ce paragraphe était une recommandation ; elle a été suivie.** Il est conservé parce qu'il dit
pourquoi, et que la question reviendra.

1. **Elle correspond à ce que tu as dit ET à ce que tu as coché.** C'est ta réponse 8.1 (« la A »),
   et elle est cohérente avec calme 2, sobre 2, discret 1, nature 1, intemporel 1, ainsi qu'avec
   « intérieur : minimaliste » et « une promenade en montagne ».
2. **Elle ne coûte rien.** Zéro octet d'APK, zéro dépendance, zéro composant supplémentaire — ta
   réponse 10.3, et le §2 du cadrage (« MVP volontairement petit »).
3. **Sur la vignette Play Store, elle est plus distinctive que Terrain, pas moins.** Dix couleurs
   franches sur un papier crème, c'est une image qu'aucune autre application de carte ne produit.
   Un indigo sur blanc bleuté, si.
4. **Son marqueur est le plus sûr à lire** sans être le plus complexe à modéliser, et sa coque
   claire résout le problème de la tuile de même couleur par construction plutôt que par
   compensation.
5. **Le seul reproche sérieux** est la parenté de teinte entre l'accent vert forêt et le joueur
   émeraude. Elle est mesurée à ΔE 18,3 — trois points au-dessus du plancher — et l'écart tient à la
   clarté, la dimension que l'œil sépare le mieux. C'est un inconvénient d'ambiance, pas de lecture.
6. **Cadastre est la meilleure des trois formellement**, et la seule qui tienne la promesse « la
   carte et l'interface parlent le même langage ». Elle est écartée sur trois motifs cumulés : le
   poids d'APK, la lisibilité du marqueur, et le fait qu'elle soit froide quand tu as répondu
   chaleureux 2.
7. **Terrain est la plus frappante et la plus fragile.** Si tu veux privilégier la capture d'écran
   au-dessus de tout, c'est elle — mais elle réintroduit un bleu face au bleu joueur, et elle
   vieillira comme les applications que tu ne veux pas imiter.

---

## 4. Répercussions — **appliquées le 13 août 2026**

Toutes les modifications ci-dessous ont été **portées** dans `02-specification-ux.md` et
`01-cadrage.md` après l'arbitrage en faveur de « Relevé ». La liste est conservée telle quelle
comme trace de ce qui a bougé et où.

### 4.1 Dans `02-specification-ux.md`

| § | Modification | Nature |
|---|---|---|
| **§1.5** | Remplacer les neuf valeurs provisoires par le tableau de jetons de la direction retenue, **en clair et en sombre**. Supprimer l'encadré ⚠️ sur la collision de `accent` : elle est résolue et mesurée | Obligatoire |
| **§1.5** | Ajouter trois jetons absents du tableau actuel : `accent-pressed`, `accent-light`, et la mention explicite que l'état pressé **fonce en clair et éclaircit en sombre** | Obligatoire |
| **§1.5** | Ajouter la règle issue du §1.9 ci-dessus : **`danger` et `warning` ne servent jamais de couleur de remplissage sur la couche carte**, parce que `danger` est à ΔE 3,1 du brique joueur. Assombrir `warning` à `#7A4F00` | Obligatoire |
| **§1.2** | Nommer la famille retenue et son traitement (graisse par défaut, chiffres tabulaires, interlettrage). Si direction B : ajouter la dépendance Archivo et le repli `fontFamilyFallback: ['Roboto']` | Obligatoire |
| **§3.1** | Ajouter une note : le rapport du validateur a été **rejoué sur la nouvelle `surface-dim`** et sa structure est inchangée (mêmes PASS, même pire paire à ΔE 17,1, mêmes 4 couleurs en WARN). La palette n'est pas modifiée | Recommandé |
| **§3.4** | Remplacer « modèle glTF » par la spécification complète du marqueur de la direction retenue : silhouette, budget de triangles, matériau, répartition de la couleur joueur, disque de contact, nœud `socket_top` | Obligatoire |
| **§1.6** | **Différencier les courbes d'entrée et de sortie** : `easeOutCubic` à l'entrée, `easeInCubic` à la sortie, la sortie à 75 % de la durée d'entrée. Aujourd'hui le document impose une courbe unique | Recommandé — c'est la seule répercussion issue de la recherche sur le mouvement |
| **§1.6** | Ajouter `motion-press` = 120 ms (entrée) / 90 ms (sortie), échelle 0,98 + assombrissement de surface, **sans changement d'élévation** | Recommandé |
| **§3.3** | Préciser que le remplissage de la tuile capturée est **radial depuis le point de contact du marqueur**, et non un fondu uniforme. La durée de 300 ms et l'interdiction d'animer un lot sont inchangées | Recommandé |
| **§7.4** | Préciser que le tap sur une ligne joueur utilise une **transition d'élément partagé** (`Hero`) : la pastille de couleur de la ligne devient le repère sur la carte, en même temps que la caméra glisse | Recommandé |
| **§7.4** | Listes de la feuille Partie : **cascade de 30 ms par ligne, plafonnée à 8 lignes** | Recommandé |
| **§4** | Ajouter le logotype et l'accroche à l'écran Connexion, avec leur hiérarchie : accroche discrète sous le nom (réponse 9.2) | Obligatoire |

### 4.2 Dans `01-cadrage.md`

| § | Modification | Nature |
|---|---|---|
| **§1** | Ajouter une ligne « Identité visuelle » renvoyant à ce document et nommant la direction retenue | Obligatoire |
| **§7.2** | Ajouter la contrainte de réglage du style Mapbox : **aucune couleur du fond de carte à moins de ΔE 15 d'une couleur joueur**, l'eau étant le risque principal face au cyan et au bleu. Elle figure déjà au §3.2 de la spec UX mais pas dans le cadrage | Recommandé |
| **§13.1** | Préciser le budget du modèle glTF (260 à 450 triangles selon la direction), le matériau unlit, et le fait que **le modèle est teinté par instance** — ce qui lève par avance le risque §15.2 de la spec UX (« si le modèle n'est pas teintable, il faut 10 fichiers ») | Recommandé |
| **§18.2** | Entrée de journal datée | Obligatoire |

### 4.3 Ce que ce document n'a pas tranché

- **Le style Mapbox réglé.** Le §3.2 de la spec impose la vérification ΔE du fond de carte ; elle se
  fait sur le style réel, dans l'application, pas ici.
- **Les cinq motifs `pattern_id`** du post-MVP. La recette est en §15.3 de la spec UX ; leur dessin
  dépendra de la direction retenue.
- **Les accessoires du marqueur MVP 2.** Seul le nœud d'ancrage est spécifié.
- **La fiche Play Store** : captures, bannière, texte de description.

---

*Document produit le 13 août 2026. Tous les ΔE sont en OKLab ×100. Le validateur est
`scripts/validate_palette.py` du skill `dataviz`, exécuté en mode `--pairs all`, celui destiné aux
cartes où n'importe quelles deux couleurs peuvent se toucher.*
