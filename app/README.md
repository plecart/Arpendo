# Arpendo — application mobile

Application Flutter, Android d'abord (`applicationId` `com.arpendo.game`). La spécification
d'interface est `documents/reference/02-specification-ux.md` ; ses jetons de conception (§1) sont
transcrits dans le thème, ses écrans arrivent avec leur domaine. Aujourd'hui l'app démarre sur
l'écran d'attente de la séquence de démarrage (UX §2.1) : contrôle de version contre
`GET /version` avant tout autre appel, puis état terminal `Pret` — que le domaine Compte
prolongera. Cet écran ne porte **aucun indicateur de progression** : le bloc de marque tient ce
rôle, et le délai du client HTTP borne l'attente. Si le build installé est sous le minimum publié
par le serveur, l'écran d'attente est **remplacé** par l'écran bloquant de mise à jour (UX §11.2),
dont on ne sort pas ; s'il est seulement sous le recommandé, le bandeau 12 s'ajoute par-dessus,
non fermable.

## Lancer

Prérequis : `fvm install` une fois après le clone (voir le README racine), une chaîne Android
(`fvm flutter doctor`), un appareil ou un émulateur, et un `.env` à la racine (copié de
`.env.example`, section « Application »).

```
just install-app
just run
```

`just run` injecte `API_BASE_URL` en `--dart-define` depuis le `.env` de la racine — l'app
**refuse de démarrer** sans elle, avec la marche à suivre dans le message. Un `flutter run` nu
échoue donc exprès : aucune url par défaut n'est écrite en dur.

La même recette injecte `SENTRY_DSN` et `SENTRY_SAMPLE_RATE`, qui obéissent à la règle
**inverse** : absentes ou vides, elles n'arrêtent rien — Sentry n'est simplement pas initialisé
pour la première, et la seconde laisse envoyer 100 % des événements. C'est le défaut du poste.
Voir « Rapport d'erreurs ».

## Structure

La racine de composition est `lib/main.dart` : `main()` seul lit l'environnement de compilation,
met le rapport d'erreurs en place, puis construit les services (`ApiConfig`,
`ConnectivityService`, `PackageInfo`, `ApiClient`, `MagasinService`) — c'est aussi le **seul
endroit qui attende** la plateforme. La construction vit dans `_construireEtLancer`, que
`demarrerAvecRapport` exécute : rien qui puisse échouer ne se produit avant que le filet soit
tendu (voir « Rapport d'erreurs ») ;
`ArpendoApp` les reçoit et les expose par `provider` — `Provider<ApiClient>` (le `dispose`
appelle `close()`) et le premier ViewModel, `DemarrageViewModel` (`ChangeNotifier`), dont l'état
scellé `EtatDemarrage` pilote un `switch` exhaustif → écran. Les écrans vivent dans
`lib/ui/<feature>/`, les services dans `lib/data/services/`, les règles pures dans
`lib/domain/`.

Le thème s'applique dans les deux modes, en `ThemeMode.system`. Les couches UI (vues + ViewModels)
et Data (repositories + services) naissent **avec leur premier contenu** — aucun dossier n'est créé
avant : `lib/ui/core/theme/` existe depuis le thème, `lib/data/services/` depuis le client HTTP,
`lib/l10n/` depuis les textes, `lib/domain/` depuis les règles du bandeau.

`lib/domain/` porte les règles **qui ne dépendent ni d'un écran ni d'un transport** : elles
n'importent rien de `lib/ui/`, et c'est ce qui permet de les rejouer ailleurs qu'à l'écran — la
notification permanente d'Android (UX §10.2) applique la même règle de bandeau sans widget.

## Tester et vérifier

Toujours par `just`, jamais par `flutter` nu (c'est le SDK global qui répondrait) :

| Commande | Rôle |
|---|---|
| `just l10n` | régénère les textes — préalable aux trois suivantes (voir « Textes ») |
| `just test-app` | tests de widget et unitaires |
| `just test-one-app test/app_test.dart` | un seul fichier, pour la boucle TDD |
| `just lint-app` | `flutter analyze`, modes stricts activés dans `analysis_options.yaml` |
| `just fmt-app` / `just fmt-check-app` | `dart format` — la première écrit, la seconde vérifie seulement |
| `just build` | `flutter build appbundle` |

Sur un poste qui n'a pas encore lancé `just install-app`, **`just lint-app` et `just test-app`**
échouent sur `lib/l10n/generated/app_localizations.dart` introuvable — ni `flutter test` ni
`flutter analyze` ne le régénèrent — et `just test-one-app` échoue sur toute cible qui l'importe, fût-ce indirectement.
`just l10n` suffit à réparer. Les deux autres s'en tirent seules, pour des raisons opposées :
`just build` fait dépendre son instantané de noyau de la génération des localisations, donc la
déclenche avant de compiler ; `dart format` ne résout aucun import — il analyse la syntaxe — donc
`fmt-check-app` passe même sans le généré. Attention, `just build` ne lance que `gen-l10n`, jamais
le script : sur un clone neuf, où `app_fr_XA.arb` n'existe pas encore, il produit un bundle avec
la seule locale `fr`.

## Thème — les jetons de conception

`lib/ui/core/theme/` est la **source unique** des valeurs de la spec UX §1. Il n'existe pas de
`tokens.json` : ce module Dart *est* le fichier de jetons machine. Aucune couleur, taille, durée
ni glyphe ne se pose en dur ailleurs dans `lib/`.

| Fichier | Ce qu'on y lit | § |
|---|---|---|
| `theme.dart` | `themeArpendo(Brightness)`, les onze couleurs de chrome des deux modes, et `CouleursChrome` pour les deux que Material 3 ne nomme pas | 1.5 |
| `typographie.dart` | les huit styles, leurs créneaux Material, la variante `.tabulaire` | 1.2, 1.7 |
| `mesures.dart` | `Espacements`, `CiblesTactiles`, `Rayons`, `Elevations` | 1.1, 1.3, 1.4 |
| `mouvement.dart` | `JetonMouvement` et `Mouvement.of(context)` | 1.6 |
| `icones.dart` | la table sémantique Phosphor — **seul fichier à importer `phosphor_icons`** | 1.8 |

### Lire un jeton depuis un écran

```dart
final couleurs = Theme.of(context).colorScheme;   // surface, onSurface, primary…
final chrome = CouleursChrome.of(context);        // accentPressed, warning
final mouvement = Mouvement.of(context);          // durées, réglage d'accessibilité compris

Container(
  padding: const EdgeInsets.all(Espacements.x4),
  decoration: BoxDecoration(
    color: couleurs.surface,
    borderRadius: BorderRadius.circular(Rayons.md),
  ),
  child: Text('12 400', style: Typographie.display.tabulaire),
);
```

**Un `Text` sans style explicite rend `type-body`.** Les créneaux Material du thème sont remplis
par les jetons : `Theme.of(context).textTheme.bodyLarge` et `Typographie.body` donnent le même
rendu, et les deux lectures sont interchangeables. Un écran n'a pas à choisir un style à la main
pour du texte courant.

**Les durées ne se lisent que par `Mouvement.of(context)`**, jamais depuis `JetonMouvement`
directement : c'est ce passage obligé qui applique `MediaQuery.disableAnimations`, sans exception
(§1.6). La sortie d'un jeton vaut toujours 75 % de son entrée et n'est jamais saisie à la main.

### Ajouter un jeton

1. **Vérifier qu'il est décidé dans la spec.** Le module transcrit, il n'arbitre pas. Une valeur
   absente du §1 est une décision à prendre là-bas d'abord — voir `.claude/rules/decisions-vs-doc.md`.
2. L'ajouter au fichier de sa famille, avec son nom de jeton d'origine et son emploi en doc.
   Pour un style, **déclarer chaque propriété, y compris quand elle vaut zéro** : `MaterialApp`
   fusionne le thème avec la géométrie typographique de Material (`ThemeData.localize`), et ce
   qu'un jeton laisse indéfini vient alors d'elle. Un jeton muet sur une propriété ne la rend pas.
3. **Ne pas écrire de test qui recopie la valeur.** Les tests de `test/ui/core/theme_test.dart`
   portent sur des *comportements* — l'inversion de l'état pressé, la coupure des animations, le
   rapport de sortie. Un test qui compare une constante à la spec ne prouve que la copie.

**Les thèmes de composant naissent avec le premier composant qui les réclame**, écran sous les
yeux. Les deux premiers sont arrivés avec l'écran d'attente (#46) : `FilledButtonThemeData`
(56 dp, fond `primary`, appui `accent-pressed` — state layer Material neutralisé, le jeton est
déjà l'état pressé —, `radius-md`) et `TextButtonThemeData` (cible tactile 48 × 48 du §1.4, que
les actions du bandeau reçoivent du thème, sans style local qui le masquerait).
`scaffoldBackgroundColor` vaut `surfaceDim` (« fond d'écran hors carte », §1.5) — le report
documenté ici depuis #34 est soldé. `InputDecorationTheme` et leurs semblables attendent le leur.

## Textes — l'ARB et la locale allongée

`lib/l10n/app_fr.arb` est la **seule source versionnée** des textes de l'interface. Tout ce qui
s'affiche en vient : aucun texte affiché n'est écrit en dur dans `lib/` (cadrage §12.6). Les
textes eux-mêmes sont
arrêtés par la spec UX — l'ARB les transcrit, il ne les rédige pas.

| Fichier | Versionné | Rôle |
|---|---|---|
| `lib/l10n/app_fr.arb` | oui | la source : une clé, sa valeur, sa `description` |
| `lib/l10n/app_fr_XA.arb` | non | locale de test, dérivée par `tool/allonger_arb.dart` |
| `lib/l10n/generated/` | non | `AppLocalizations`, écrite par `flutter gen-l10n` |
| `l10n.yaml` | oui | la configuration de la génération |

`just l10n` réécrit les deux dérivés. Elle est appelée par `just install-app`, donc par
`just install` : un clone neuf n'a rien de plus à lancer, en CI comme sur un poste.

### Ajouter une clé

1. **Vérifier que le texte est arrêté dans la spec.** Un texte entre « guillemets français » y est
   définitif (UX §0). Un texte absent est une décision à prendre là-bas d'abord — voir
   `.claude/rules/decisions-vs-doc.md`.
2. L'ajouter à `app_fr.arb` sous une clé en **camelCase français préfixée par son composant ou son
   écran** (`marqueAccroche`, `bandeauPasDeReseau`), jamais par le § : les § bougent, les
   composants non.
3. Lui donner une `description` qui **cite le §** d'où vient le texte. `gen-l10n` la rend en
   doc-comment du getter : elle se lit au point d'usage, sans ouvrir la spec.
4. Un texte **cité mot pour mot du cadrage** porte
   `"description": "Cité — cadrage §x.y, ne pas modifier"`. C'est la marque qui interdit de le
   réécrire en passant.
5. `just l10n`, puis lire le texte par `AppLocalizations.of(context).maCle`. Le getter n'est
   **jamais nul** (`nullable-getter: false`) : aucun `!` au point d'usage.
6. Si la clé arrive avec un composant, **ajouter ce composant à `composants`** dans
   `test/l10n/fr_xa_test.dart`.

### Ce que prouve le test `fr-XA`

`tool/allonger_arb.dart` dérive `app_fr_XA.arb` de `app_fr.arb` : chaque valeur est allongée de
30 % et encadrée des marqueurs `⟦…⟧`, les `{placeholders}` et les métadonnées `@` traversant
intacts. `test/l10n/fr_xa_test.dart` pompe chaque composant de sa liste sous `Locale('fr', 'XA')`,
sur l'écran de référence 360 × 800 dp, et exige trois choses du même rendu :

- **tout texte rendu porte les marqueurs** — un littéral en dur n'en a pas, et fait rougir le
  test. Le contrôle porte sur les `Text` de l'arbre, `Text.rich` compris, et lit leur texte
  *visible* : ni le `semanticsLabel`, qui masquerait un littéral, ni les `WidgetSpan` ;
- **aucun débordement** — la tolérance de +30 % de longueur exigée par la spec UX §0 ;
- **aucune troncature** — `didExceedMaxLines` est faux partout : la spec veut des conteneurs qui
  grandissent, pas qui coupent (UX §0, §1.2).

C'est la seule barrière contre les chaînes en dur : il n'y a pas de lint dédié. Un composant
absent de la liste n'est pas couvert, d'où l'étape 6 ci-dessus. Le garde regarde les `Text` de
l'arbre, `Offstage` et branches d'`IndexedStack` comprises, et exige que le texte soit **une seule**
valeur de l'ARB — `'⟦a⟧ — ⟦b⟧'` rougit, parce que le séparateur, lui, est écrit en dur.

Ce qu'il ne voit pas, faute d'un cas réel qui le justifie :

| Angle mort | Pourquoi |
|---|---|
| un littéral dans un `RichText` nu ou un `SelectableText` | l'app écrit des `Text` ; ces deux-là ne passent pas par un `Text` |
| ce qu'un composant ne construit qu'à l'interaction | infobulle d'un `Tooltip`, items d'un `PopupMenuButton`, contenu d'un `showDialog`, tiroir fermé — le test ne fait qu'un rendu |
| un `semanticsLabel` de `Text` ou d'`Icon` | il n'est pas rendu comme texte — à surveiller sur une icône porteuse de sens |
| un texte clippé par un conteneur trop petit | sans `maxLines` ni `ellipsis`, le paragraphe ne se déclare pas tronqué |

Et un faux positif à connaître : un composant qui embarque du mobilier Material écrivant son propre
texte — compteur de `TextField(maxLength:)`, boutons d'`AboutDialog` — fera rougir le garde. Ce
texte-là est bien localisé, mais par `GlobalMaterialLocalizations`, pas par notre ARB : un tel
composant ne se teste pas de cette façon.

`fr-XA` n'est **jamais** livrée : `supportedLocales` de production ne contient que `fr`, et un
test de `test/app_test.dart` le vérifie.

## Composants uniques

### Le bandeau — une règle, une table de lignes

La spec UX §2.4 impose **un seul bandeau à la fois** : quand plusieurs conditions sont vraies, la
plus prioritaire gagne et les autres se taisent. `lib/domain/bandeau/` porte cette règle, et rien
d'autre.

| Fichier | Ce qu'on y lit |
|---|---|
| `entree_bandeau.dart` | `Severite`, `ActionBandeau`, `EntreeBandeau`, et `resoudre(actives)` qui rend l'unique entrée à afficher |
| `lignes.dart` | les deux lignes que l'app sait déjà former — réseau absent (prio 5), mise à jour recommandée (prio 12) |

**Ajouter une ligne ne touche ni `resoudre` ni `lignes.dart`.** Une ligne appartient au domaine qui
possède sa condition, et s'y déclare :

```dart
EntreeBandeau ligneVitesseExcessive() => EntreeBandeau(
  priorite: 7,                       // le rang de la table du §2.4, jamais renuméroté
  severite: Severite.avertissement,
  texte: (l10n) => l10n.bandeauTropVite,
);
```

Puis la racine de composition joint les lignes actives et remet le résultat à l'affichage :

```dart
final entree = resoudre([
  if (!enLigne) ligneReseauAbsent(),
  if (vitesseExcessive) ligneVitesseExcessive(),
]);
```

Il n'existe **volontairement** aucune énumération centrale des conditions : ce serait le point que
chaque ligne nouvelle devrait modifier. Deux `assert` gardent ce que le module peut vérifier :

- **deux entrées ne portent jamais le même rang** — un rang identifie une ligne de la table ;
- **une entrée porte zéro, une ou deux actions**, pas davantage : c'est l'anatomie du §2.4.

**Ce qu'aucun `assert` ne peut voir, et qui est à ta charge** : la règle d'exclusivité du §2.4 est
bien plus forte que l'unicité des rangs — « aucune condition ne doit pouvoir être vraie en même
temps qu'une condition plus prioritaire ». Elle porte sur les **conditions**, que le module ne
reçoit jamais. Deux lignes dont les conditions se recouvrent passeront sans un mot, et la mieux
classée masquera l'autre en silence. En déclarant une ligne, vérifie que sa condition exclut celles
d'au-dessus.

Les deux lignes de `lignes.dart` n'ont pas encore de domaine propriétaire — le réseau ira à
Territoire avec la fenêtre de cinq minutes (lignes 4 et 6), la mise à jour à la séquence de
démarrage. Elles déménageront chez eux, et ce fichier n'est pas destiné à grossir.

**Dette connue, et c'est exactement le piège ci-dessus** : `ligneReseauAbsent()` ne porte pas la
borne « coupure de moins de 5 min » que la table donne à la ligne 5, faute d'horloge de coupure.
Tant que la ligne 6 (« Coupure de plus de 5 min ») n'existe pas, c'est sans effet. **Le jour où
Territoire la livre, la ligne 5 doit recevoir sa borne dans le même lot** : sinon les deux seront
actives ensemble et la 5, de rang plus bas, masquera la 6 — l'inverse de ce que le §2.4 demande.
Le raccourci est marqué `ponytail:` dans le code, donc `/ponytail-debt` le retrouve où qu'il aille.

`bloquant` est **porté comme donnée** par l'entrée ; son effet — carte masquée, interactions de jeu
coupées (§12.2) — se réalisera avec la carte, pas ici.

### Le bandeau à l'écran

| Fichier | Ce qu'on y lit |
|---|---|
| `ui/core/bandeau/bandeau.dart` | `Bandeau(entree)` — l'anatomie du §2.4 ; le glyphe et sa couleur se **dérivent** de `severite`, ils ne se passent pas en paramètre |
| `ui/core/bandeau/emplacement_bandeau.dart` | `EmplacementBandeau(entree?)` — le créneau unique `Calque.bandeau` ; `null` libère la place, que la carte reprend en `motion-base` |

**Aucune hauteur n'est posée dans le code** : elle vaut le rembourrage plus le contenu, et grandit
de 24 dp par ligne de message. 56 dp sur une ligne sans action, 80 sur deux, 112 dès qu'une action
est présente, 136 pour deux lignes et une action — des résultats que les tests mesurent, pas des
constantes. Les actions vivent sur une **seconde rangée**, parce que deux libellés et un message ne
tiennent pas côte à côte sur 360 dp, et ce sont des `Wrap`, pour qu'un réglage de taille de police
système à 200 % (§1.2) les fasse passer l'un sous l'autre plutôt que déborder.

`ui/core/mise_en_page/apparition_animee.dart` porte l'apparition et la disparition, et c'est **le
point unique où le §1.6 s'applique** — durées d'entrée et de sortie, réglage d'accessibilité.
Tout composant qui doit rendre sa place en partant passe par lui plutôt que de réécrire un
contrôleur. Deux pièges y sont documentés une fois pour toutes : `AnimatedSize` ne joue jamais son
contrôleur à l'envers, donc sa `reverseDuration` est inerte ; et poser une `reverseCurve` sur un
contrôleur qu'on rembobine applique un **second** miroir temporel, ce qui inverse l'effet voulu.

### La pile de calques et les safe areas

`ui/core/mise_en_page/pile_de_calques.dart` porte les trois pièces du contrat de mise en page :

- **`enum Calque`** — les huit rangs `z` du §2.2, du fond (`carte`) vers l'avant (`bloquant`).
- **`PileDeCalques(children: {Calque: Widget})`** — l'unique `Stack` d'écran. Il trie par `z`, donc
  l'ordre d'écriture n'a aucune importance, et il enveloppe **tout sauf `carte`** dans une
  `SafeArea` : la carte occupe l'écran entier, encoche comprise. Chaque plan se dimensionne
  lui-même — une carte se donne en `SizedBox.expand`, un header à sa hauteur propre.
- **`rembourrageBas(context)`** — ce qu'une feuille modale ajoute sous son contenu. Le résultat
  dépend du point d'appel, et c'est voulu : sous une `SafeArea` il ne rend que le clavier, parce
  que le rembourrage y a déjà été appliqué *et* retiré du `MediaQuery`. Une feuille s'affiche par
  le `Navigator`, donc hors de la pile, et reçoit bien les deux.

### Le bloc de marque

`ui/core/marque/marque_centree.dart` — `MarqueCentree(sous: …)` compose le bloc **centré** et ce
qui s'écrit dessous. Elle existe pour tenir **un invariant, pas pour éviter de retaper dix
lignes** : le logo occupe la même place sur tous les écrans qui l'emploient — attente (§2.1) et
mise à jour obligatoire (§11.2) aujourd'hui, Connexion (§4) et Accueil (§5) demain — donc il ne
saute jamais quand l'un remplace l'autre. `sous` est peint par un `Align(heightFactor: 0)` : il ne
compte pas dans la hauteur, sans quoi le bloc remonterait de la moitié de ce qui paraît (52 dp
mesurés avant #98).

**La bande basse est réservée en permanence**, remplie ou non — `bandeBasse` reçoit le bouton
quand il y en a un. Les deux effets sont indissociables : réserver *toujours* empêche le bloc de
bouger quand une action paraît ou disparaît, et réserver *tout court* empêche `sous` de recouvrir
le bouton (31 dp de recouvrement mesurés sur 360 × 800 sans la réservation). Comme `sous` est hors
du flux, **aucun défilement ne peut le sauver** : c'est la place qu'on lui laisse, ou rien — d'où
le test de non-recouvrement que chaque écran garde en propre.


`ui/core/marque/bloc_de_marque.dart` — signe, logotype, accroche (§4), la même composition pour
les trois écrans sans carte : attente (§2.1), Connexion (§4), Accueil (§5). Le signe est
`assets/signe-arpendo.svg` (copié depuis `documents/assets/`, source unique), teinté
`ColorFilter.mode(primary, srcIn)` — les opacités des courbes survivent, le mode sombre est
gratuit. Le logotype est du **texte Roboto w500** (§1.2, amendé le 3 septembre 2026) : son corps
se dérive de la hauteur de capitale de 24 dp du §4 par le ratio lu dans la fonte
(`sCapHeight/unitsPerEm` = 1456/2048), il ne se pose pas. Le nom vit dans l'ARB (`marqueNom`,
intraduisible) parce que le garde `fr-XA` exige que tout texte rendu en vienne.

### Le bouton pleine largeur

`ui/core/boutons/bouton_pleine_largeur.dart` est le bouton principal des écrans sans carte
(§4, §11.2) : un `FilledButton` pleine largeur qui porte le retour d'appui `motion-press` du
§1.6 — échelle 0,98 à l'appui, via `Mouvement.of`. L'échelle vit **dans ce widget et pas dans le
thème** : `ButtonStyle` n'a aucune propriété d'échelle, et ses `ButtonLayerBuilder` sont clippés
par la forme du `Material`. L'assombrissement d'appui, lui, vient du `FilledButtonThemeData`
(`accent-pressed`). Les marges d'écran (`space-4`) restent à l'appelant.

## Icône de lancement

`documents/assets/icone-app.svg` est la **source unique** de l'icône (identité visuelle §1.5,
variante A″2). Android la reçoit en adaptive icon — `res/mipmap-anydpi-v26/ic_launcher.xml`
déclare le fond, le premier plan et le calque monochrome — transcrite **à la main** dans
`res/drawable/ic_launcher_foreground.xml` et `res/values/ic_launcher_background.xml`. Aucun
script, aucun rasteriseur, aucun PNG : `minSdk` vaut 26 (Android 8.0, cadrage §1) pour que
l'adaptive icon soit la seule ressource d'icône.

| Dans le SVG | Dans les ressources Android |
|---|---|
| `<rect fill>` | `<color name="ic_launcher_background">` |
| `<path d>` | `<path android:pathData>` — chaîne recopiée caractère pour caractère |
| `<circle cx cy r>` | `<path>` de deux arcs `A r r 0 1 0 …` de même centre et rayon, seule transcription admise |
| `opacity` d'un trait | `android:strokeAlpha` |

Le `<group>` qui enveloppe les trois tracés ne vient pas du SVG : il réduit le signe dans la zone
sûre du masque (66/108, échelle 0,85 autour du centre), et rien d'autre — le décalage de 2 % vers le
haut que demande le §1.5 est déjà dans les coordonnées du SVG (hexagone centré en y = 51), il ne se
rajoute pas. Le calque `<monochrome>` réutilise le premier plan : il est déjà d'une seule couleur,
et Android en remplace la couleur par celle du thème en ne gardant que l'alpha.

**Une retouche du SVG se recopie ici**, attribut par attribut ; le drawable ne se retouche jamais
seul. L'icône 512 × 512 de la fiche Play s'exporte du même SVG.

## Réseau

Tout ce qui parle au serveur passe par `lib/data/services/api_client.dart`, seul fichier à importer
`package:http` — comme `lib/data/services/connectivity_service.dart` est le seul à importer
`package:connectivity_plus`. `ApiClient` reçoit sa configuration (`ApiConfig` : url de base et
délai par tentative), la version du client et le service de connectivité, ne connaît aucune valeur
en dur, et rend tout échec en `ApiException` scellée — `HorsLigne`, `ServeurInjoignable`,
`ErreurHttp`, `ReponseInvalide` — jamais en exception de transport, jamais avec un texte destiné à
l'écran (UX §13.3). Le corps est décodé en UTF-8 depuis ses octets, sans consulter `Content-Type` ;
le délai borne **chaque tentative** de transport et non la séquence, de sorte qu'une enveloppe
d'espacement progressif passée au paramètre `client` du constructeur puisse durer plus longtemps
que lui ; `close()` libère le client détenu, créé ou injecté — l'injecter, c'est le céder.
L'étendre, c'est l'envelopper, pas le modifier : un verbe de plus naît avec son premier appelant.
Son premier appelant réel est `lib/data/services/version_client.dart`, qui lit `GET /version` et
décode les deux seuils de build — la séquence de démarrage compare, lui ne fait que lire.

`ConnectivityService` répond de deux façons, et la bonne dépend de la question posée :

| Question | Verbe | Ce qu'il rend |
|---|---|---|
| « suis-je en ligne, là, maintenant ? » | `isOnline()` | un `Future<bool>`, une sonde ponctuelle |
| « préviens-moi quand ça change » | `enLigne()` | un `Stream<bool>`, **un événement par changement d'état** |

**Ne pas se fier au premier événement d'`enLigne()` pour connaître l'état initial** : sur Android le
plugin l'émet à l'abonnement, mais pas à tous. Qui a besoin de savoir où il en est lit `isOnline()`,
et traite un premier événement identique comme un doublon.

Les deux verbes présument le réseau **présent** sur un incident de plateforme (cadrage §10.3) et
laissent remonter toute autre erreur. La parité s'arrête à un cas : un **plugin absent de la build**
ne fait pas d'erreur sur le flux, il le rend muet ; c'est `isOnline()` qui reste tolérant à
celui-là.

Le pourquoi de ces trois comportements — et celui du `distinct` que `enLigne()` applique en plus de
celui du plugin — est au point d'usage, dans le dartdoc de
`lib/data/services/connectivity_service.dart`, avec les sources qui l'établissent. Ces raisons-là ne
se recopient pas : elles se lisent là où on écrit l'appel.

C'est `enLigne()` qui alimente la ligne 5 du bandeau (UX §2.4) — voir « Composants uniques ».

> `connectivity_plus` fusionne la permission Android `ACCESS_NETWORK_STATE` dans le manifeste.
> Elle est normale et n'affiche aucune invite, mais elle apparaît dans l'APK.

## Mise à jour du client — deux niveaux, deux services

La séquence de démarrage compare le build installé aux deux seuils de `GET /version` (UX §11.2) :

| Verdict | Ce qui s'affiche |
|---|---|
| build < **minimal** | `EcranMiseAJour` **remplace** l'écran d'attente — `Calque.bloquant` (z 500), `PopScope(canPop: false)`, aucune sortie, pas même le geste de retour. Il reprend le **bloc de marque centré** et la mécanique de l'écran d'attente (`Align(heightFactor: 0)`), donc le logo ne bouge pas d'un écran à l'autre. Il ne porte **aucune réassurance sur les données** : une mise à jour n'en fait perdre à personne, et le dire créerait la peur qu'on prétend calmer |
| build < **recommandé** | l'écran d'attente reste, la **ligne 12** du bandeau s'ajoute sur son calque. **Aucun bouton** : le message est lui-même le lien (graisse 500, même couleur), et c'est le bandeau entier qui est tapable |
| sinon | rien de plus |

Un service de la couche Data sert les deux niveaux, et il est **le seul à importer son plugin** —
la règle qui vaut déjà pour `api_client.dart` et `connectivity_service.dart` :

| Fichier | Plugin | Ce qu'il fait |
|---|---|---|
| `data/services/magasin_service.dart` | `url_launcher` | essaie `market://details?id=…`, puis le lien web ; **si aucun des deux ne s'ouvre, rien ne se passe à l'écran** (§11.2) et l'échec part par `signalerIncident` |

**La condition de la ligne 12 vit dans `DemarrageViewModel`, pas ailleurs** : elle n'est vraie
qu'en état `Pret` et sous le build recommandé. La borner à `Pret` n'est pas cosmétique — sans
ça, une recommandation lue avant un « Réessayer » raté continuerait de piloter le bandeau
par-dessus l'écran de panne, deux messages dont l'un est la cause de l'autre (§2.4).

**Le bandeau n'est pas fermable.** La fermeture — et la persistance par version qu'elle suppose —
sont repoussées après le MVP (cadrage §20) ; c'est pourquoi l'application n'a **aucun** stockage
local aujourd'hui.

`main()` reçoit l'`applicationId` de `PackageInfo` et le passe au service du magasin : c'est
l'application **réellement installée** dont on ouvre la fiche, jamais une constante qui
divergerait d'une saveur de build.

## Rapport d'erreurs — Sentry, et ce qu'on ne lui envoie jamais

Un seul fichier importe `sentry_flutter` : `data/services/rapport_erreurs.dart`, rangé en quatre
volets — ce qui est partagé, le démarrage, le signalement, l'assainissement. Il expose trois
choses ; la racine de composition n'en connaît que la première, plus `tauxEnvoiValide` qui valide
le taux avant tout contact avec le SDK.

| | |
|---|---|
| `demarrerAvecRapport` | lance l'application, **sous Sentry seulement si `SENTRY_DSN` est non vide** |
| `signalerIncident` | écrit un incident de plateforme au journal **et** le remonte à Sentry |
| `assainir` | ce que le `beforeSend` applique : rend un événement débarrassé de ce qu'on n'a pas le droit d'envoyer |

Quatre réglages sont posés sur le SDK, et rien de plus : le DSN, `sendDefaultPii = false`
(cadrage §13.10), `assainir` en `beforeSend`, et le **taux d'envoi**. Les deux derniers sont les
deux garde-fous que le cadrage §16 exige ensemble — « filtrage entrant **et** échantillonnage dès
le jour 1 ». L'échantillonnage n'est pas décoratif côté app : le quota de 5 000 erreurs par mois
est celui de l'**organisation**, donc l'application et l'api le consomment ensemble, et la
déduplication du SDK ne rattrape rien sur le chemin des incidents de plateforme — elle repose sur
`exception.hashCode`, or `PlatformException` n'a ni `==` ni `hashCode`.

À ne pas confondre avec `tracesSampleRate`, qui échantillonne les **mesures de performance** :
celui-là reste absent, aucune mesure n'étant demandée.

Le taux, lui, est **transmis au SDK natif** (`androidOptions.setSampleRate`), là où `beforeSend`
ne l'est pas : l'échantillonnage couvre donc les deux voies, y compris les plantages natifs que
`assainir` ne voit jamais. C'est l'argument le plus fort en faveur du §16, et il ne vaut que pour
ce garde-fou-là.

**`configurerSentry` ne lève jamais, et c'est sa propriété la plus importante.** Elle s'exécute
dans la closure de configuration de `SentryFlutter.init`, que le SDK enveloppe dans un `try` qui
**avale**. Une exception y laisserait Sentry s'initialiser avec le vrai DSN et **sans**
`beforeSend` — `assainir` ne tournerait jamais, sans un mot. Le garde `dsn == null` du SDK ne
rattraperait rien : le DSN est déjà posé en amont depuis le `--dart-define`. Les bornes du taux
sont donc vérifiées **avant**, par `tauxEnvoiValide` à la racine de composition ; ce qui reste
dans la closure normalise au lieu de refuser.

**Et le `beforeSend` échoue fermé.** Le SDK Dart, lui, échoue **ouvert** : son `_runBeforeSend`
part de l'événement d'origine et son `catch` ne l'annule pas, si bien qu'un `beforeSend` qui lève
laisse partir l'événement **brut** — l'inverse exact du `sentry_sdk` Python, qui part de `None` et
abandonne. Comme `assainir` modifie l'événement **sur place**, un jet à mi-parcours laisserait
partir un événement à moitié nettoyé. Le callback l'enveloppe donc et **abandonne** ce qu'il ne
sait pas assainir : la divergence qui compte entre les deux modules n'est pas dans les motifs,
elle est dans le mode de panne.

**Abandonner ne fait pas perdre le signal.** Le SDK compte l'événement écarté
(`DiscardReason.beforeSend`) et attache le rapport à la prochaine enveloppe : l'incident apparaît
dans les statistiques d'événements écartés de l'organisation. C'est ce qui permet de rendre `null`
plutôt que de bricoler un « événement minimal » à partir d'une structure qu'on vient d'échouer à
parcourir.

> **`developer.log` n'écrit pas dans logcat** — son contrat est d'émettre vers la vue Logging de
> DevTools. En release, sans service VM, l'appel ne fait rien (il ne lève pas). C'est un confort de
> développement, pas un canal d'exploitation : les deux chemins qui ne s'appuient que sur lui — le
> repli d'initialisation et l'abandon d'un événement — se voient au premier `just run`, et nulle
> part ailleurs.

**Vide veut dire « aucun appel au SDK »**, et non « `init` avec un DSN vide » : ce dernier
installe quand même les intégrations et le hook des exceptions non rattrapées. La différence ne se
voit pas sur un poste de développement et compte partout ailleurs. C'est la même décision, pour la
même raison, que `configure_sentry` côté api.

`lancer` est appelé dans les deux branches et **une seule fois** : sous DSN, c'est le SDK qui
l'exécute, dans la zone où il capte les erreurs non rattrapées. Tout le démarrage — construction
des services comprise — est donc à l'intérieur.

### Les incidents qu'aucun écran ne montre

Deux services avalent délibérément une panne de plateforme : `ConnectivityService` présume le
réseau **présent** sur un canal natif en erreur (§10.3), et `MagasinService` ne montre **rien** à
l'écran quand aucun lien ne s'ouvre (§11.2). Dans les deux cas le choix est bon et le silence ne
l'est pas : l'incident devient indiscernable du fonctionnement normal. Ils appellent donc
`signalerIncident`, qui écrit au journal de la plateforme **et** remonte l'exception à Sentry.

Ils ne l'importent pas depuis `sentry_flutter` : ils reçoivent un `Signalement` en paramètre, dont
le défaut est `signalerIncident`. C'est ce qui garde **un seul importeur du plugin** et ce qui rend
la trace observable en test — sans quoi rien ne prouverait qu'elle part.

Sans Sentry initialisé, l'appel ne coûte rien et ne lève pas : le hub et la file de tâches du SDK
valent `NoOpHub` et `NoOpTaskQueue` tant qu'aucun `init` n'a eu lieu. Aucun appelant n'a donc à
savoir si le rapport d'erreurs tourne.

### Ce qu'`assainir` retire

Trois motifs, **recopiés de `api/src/arpendo_api/core/sentry.py`** : une divergence de motif serait
une divergence de protection (cadrage §13.10 — sans scrubbing explicite, on reconstruit
l'historique de localisation que §12.3 interdit).

| Motif | Règle |
|---|---|
| coordonnées | reconnues **à la paire**, ≥ 4 décimales — un nombre isolé est indécidable, et un horodatage ISO (`…:35.751365Z`) a exactement la même forme |
| jeton porteur | `Bearer …`, insensible à la casse |
| adresse e-mail | forme usuelle |

La règle de la paire vaut aussi pour les **nombres** : une composante n'est retirée que si le
conteneur qui la porte en contient une seconde de même forme. Le faux positif assumé est un
conteneur de deux mesures fines, assaini pour rien — perdre un centile se voit et se répare,
laisser fuir une position ne se voit pas et ne se répare pas.

**Lacune connue, et commune aux deux langages** : le séparateur du motif exclut le tiret, pour ne
pas le confondre avec le signe de la seconde composante — une paire jointe par un tiret nu
(`48.858370-2.294481`) passe donc. Aucun encodage du projet ne produit cette forme, et la corriger
devrait se faire **des deux côtés à la fois**.

### Où il les retire

**Tous les emplacements porteurs de texte**, et pas seulement ceux qu'un rapport de bogue citerait :
message (gabarit et paramètres compris), exceptions (valeur et mécanisme), fils d'Ariane, fils
d'exécution, utilisateur, requête, contextes, `transaction`, `culprit`, `logger`, `serverName`,
`fingerprint`, `modules`, étiquettes et `extra`. **Cette énumération est le prix d'un protocole
typé** — le `before_send` de Python reçoit un dictionnaire, celui de Dart un `SentryEvent`. Elle est
d'autant moins évitable que le SDK Dart n'a **pas** d'`EventScrubber` : là où l'api superpose deux
filets, `assainir` est le seul de la voie Dart.

Ce qui la rend tenable est le **test de population** qui l'accompagne : un événement dont chaque
emplacement porte une donnée interdite, sérialisé comme le SDK le sérialise, puis relu. Ajouter un
champ au fixture sans l'assainir fait rougir la suite — un `expect` par champ ne l'aurait pas fait.

Restent dehors, délibérément : le `type` d'une exception et les piles d'appels (du **code**, jamais
une donnée de joueur), l'`id` d'utilisateur (ce qui rend un rapport attribuable), et `release` /
`dist` / `environment` / `platform` (des métadonnées de build que l'application choisit).

### La voie qui échappe à `assainir`

`SentryFlutter.init` installe `NativeSdkIntegration` et laisse `enableNativeCrashHandling` vrai : un
**plantage natif ou un ANR** est envoyé par le SDK Android, dans sa propre enveloppe, sans passer
par le `beforeSend` Dart — le SDK le dit lui-même, « captureEnvelope does not call the beforeSend
callback ». Ce que le natif reçoit du Dart, c'est `sendDefaultPii`, transmis à
`androidOptions.setSendDefaultPii`. Un rapport natif porte une pile, un contexte d'appareil et un
état de mémoire, pas les chaînes de l'application — mais il faut savoir que le filet ne s'y applique
pas.

### L'éprouver

`assainir` ne parle à rien : ni réseau, ni `init`, ni projet Sentry. Un test la nourrit d'un
`SentryEvent` écrit à la main. Elle **modifie l'événement reçu** et le rend, là où son homologue
Python en construit une copie : les objets du protocole Dart sont typés et mutables, et le SDK
lui-même déprécie `copyWith` au profit de l'affectation directe.

Les **réglages** posés sur le SDK s'éprouvent eux aussi : `configurerSentry` est séparée de l'appel
à `SentryFlutter.init`, parce qu'une configuration écrite dans la closure de `init` serait la seule
ligne du module que rien n'exerce — or c'est celle dont l'absence *est* l'incident. Un
`SentryFlutterOptions` s'instancie sans réseau, donc un test lit chaque réglage et fait passer un
événement par le `beforeSend` qui vient d'y être posé.

Enfin, **le filet lui-même peut tomber** : `SentryFlutter.init` n'est pas total (l'`ArgumentError`
du DSN, le binding natif et les intégrations sont hors de son `try`, et `appRunner` ne tourne
qu'après elles). `demarrerAvecRapport` rattrape, écrit au journal de la plateforme et lance
l'application quand même — un outil d'observabilité qui empêche de démarrer coûte plus qu'il ne
rapporte, et la panne ne serait visible qu'en production, le poste et la CI tournant DSN vide.

Pour voir la collecte réellement partir, renseigner `SENTRY_DSN` dans le `.env` et relancer
`just run` — rien d'autre à changer.
