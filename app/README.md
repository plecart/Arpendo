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
| `just test-app` | tests de widget et unitaires |
| `just test-one-app test/app_test.dart` | un seul fichier, pour la boucle TDD |
| `just lint-app` | `flutter analyze`, modes stricts activés dans `analysis_options.yaml` |
| `just fmt-app` / `just fmt-check-app` | `dart format` — la première écrit, la seconde vérifie seulement |
| `just build` | `flutter build appbundle` |

## Structure

`lib/main.dart` porte `ArpendoApp`, racine pilotée par l'état (UX §2.1) : l'écran affiché
dépendra de la séquence de démarrage. Elle applique le thème dans les deux modes, en
`ThemeMode.system`. Les couches UI (vues + ViewModels) et Data (repositories + services) naissent
avec leur premier contenu, sous `lib/ui/` et `lib/data/` — aucun dossier n'est créé avant :
`lib/ui/core/theme/` existe depuis le thème, `lib/data/services/` depuis le client HTTP.

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

> `connectivity_plus` fusionne la permission Android `ACCESS_NETWORK_STATE` dans le manifeste.
> Elle est normale et n'affiche aucune invite, mais elle apparaît dans l'APK.
