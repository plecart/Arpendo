# Arpendo — application mobile

Application Flutter, Android d'abord (`applicationId` `com.arpendo.game`). La spécification
d'interface est `documents/reference/02-specification-ux.md` ; ses jetons de conception (§1) sont
transcrits dans le thème, ses écrans arrivent avec leur domaine. Aujourd'hui l'app démarre sur un
écran vide, habillé du thème.

## Lancer

Prérequis : `fvm install` une fois après le clone (voir le README racine), une chaîne Android
(`fvm flutter doctor`), un appareil ou un émulateur.

```
just install-app
cd app && ../.fvm/flutter_sdk/bin/flutter run
```

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

## Structure

`lib/main.dart` porte `ArpendoApp`, racine pilotée par l'état (UX §2.1) : l'écran affiché
dépendra de la séquence de démarrage. Elle applique le thème dans les deux modes, en
`ThemeMode.system`. Les couches UI (vues + ViewModels) et Data (repositories + services) naissent
avec leur premier contenu, sous `lib/ui/` et `lib/data/` — aucun dossier n'est créé avant :
`lib/ui/core/theme/` existe depuis le thème, `lib/data/services/` depuis le client HTTP,
`lib/l10n/` depuis les textes, `lib/domain/` depuis les règles du bandeau.

`lib/domain/` porte les règles **qui ne dépendent ni d'un écran ni d'un transport** : elles
n'importent rien de `lib/ui/`, et c'est ce qui permet de les rejouer ailleurs qu'à l'écran — la
notification permanente d'Android (UX §10.2) applique la même règle de bandeau sans widget.

## Thème — les jetons de conception

`lib/ui/core/theme/` est la **source unique** des valeurs de la spec UX §1. Il n'existe pas de
`tokens.json` : ce module Dart *est* le fichier de jetons machine. Aucune couleur, taille, durée
ni glyphe ne se pose en dur ailleurs dans `lib/`.

| Fichier | Ce qu'on y lit | § |
|---|---|---|
| `theme.dart` | `themeArpendo(Brightness)`, les onze couleurs de chrome des deux modes, et `CouleursChrome` pour les deux que Material 3 ne nomme pas | 1.5 |
| `typographie.dart` | les huit styles, leurs créneaux Material, la variante `.tabulaire` | 1.2, 1.7 |
| `mesures.dart` | `Espacements`, `Rayons`, `Elevations` | 1.1, 1.3 |
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

**Le thème de composant n'existe pas encore.** `FilledButtonThemeData`, `InputDecorationTheme` et
leurs semblables naissent avec le premier composant qui les réclame, écran sous les yeux — de même
que `scaffoldBackgroundColor`, qui vaudra `surfaceDim` (« fond d'écran hors carte », §1.5).

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
   écran** (`marqueAccroche`, `bandeauPasDeConnexion`), jamais par le § : les § bougent, les
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

`ConnectivityService` répond de deux façons, et la bonne dépend de la question posée :

| Question | Verbe | Ce qu'il rend |
|---|---|---|
| « suis-je en ligne, là, maintenant ? » | `isOnline()` | un `Future<bool>`, une sonde ponctuelle |
| « préviens-moi quand ça change » | `enLigne()` | un `Stream<bool>`, **un événement par changement d'état** |

**Ne pas se fier au premier événement d'`enLigne()` pour connaître l'état initial** : sur Android le
plugin l'émet à l'abonnement, mais pas à tous — le canal est mis en cache et son `onListen` ne se
déclenche qu'au passage de zéro à un auditeur, donc un second abonné simultané ne l'aura pas. Qui a besoin de savoir où il en est
lit `isOnline()`, et traite un premier événement identique comme un doublon.

Son `distinct` ne fait pas double emploi avec celui du plugin : celui-ci compare des **listes
d'interfaces**, si bien qu'un passage du Wi-Fi aux données mobiles le traverse et produirait deux
« en ligne » ; le nôtre compare l'état.

Les deux verbes présument le réseau **présent** sur un incident de plateforme (cadrage §10.3) et
laissent remonter toute autre erreur — pour `enLigne()`, cela veut dire qu'un incident survenu
après une coupure fait basculer le flux en ligne. La parité s'arrête à un cas : un **plugin absent
de la build** ne fait pas d'erreur sur le flux, il le rend muet ; c'est `isOnline()` qui reste
tolérant à celui-là.

C'est `enLigne()` qui alimente la ligne 5 du bandeau (UX §2.4) — voir « Composants uniques ».

> `connectivity_plus` fusionne la permission Android `ACCESS_NETWORK_STATE` dans le manifeste.
> Elle est normale et n'affiche aucune invite, mais elle apparaît dans l'APK.
