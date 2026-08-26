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

**Les durées ne se lisent que par `Mouvement.of(context)`**, jamais depuis `JetonMouvement`
directement : c'est ce passage obligé qui applique `MediaQuery.disableAnimations`, sans exception
(§1.6). La sortie d'un jeton vaut toujours 75 % de son entrée et n'est jamais saisie à la main.

### Ajouter un jeton

1. **Vérifier qu'il est décidé dans la spec.** Le module transcrit, il n'arbitre pas. Une valeur
   absente du §1 est une décision à prendre là-bas d'abord — voir `.claude/rules/decisions-vs-doc.md`.
2. L'ajouter au fichier de sa famille, avec son nom de jeton d'origine et son emploi en doc.
3. **Ne pas écrire de test qui recopie la valeur.** Les tests de `test/ui/core/theme_test.dart`
   portent sur des *comportements* — l'inversion de l'état pressé, la coupure des animations, le
   rapport de sortie. Un test qui compare une constante à la spec ne prouve que la copie.

**Le thème de composant n'existe pas encore.** `FilledButtonThemeData`, `InputDecorationTheme` et
leurs semblables naissent avec le premier composant qui les réclame, écran sous les yeux — de même
que `scaffoldBackgroundColor`, qui vaudra `surfaceDim` (« fond d'écran hors carte », §1.5).

## Réseau

Tout ce qui parle au serveur passe par `lib/data/services/api_client.dart`. **Aucun appelant
n'importe `package:http`** : seuls le client et ses futures enveloppes le connaissent, et
`lib/data/services/connectivity_service.dart` est le seul fichier à importer
`package:connectivity_plus`. Deux règles vérifiables d'un `grep`, et qui sont la raison d'être du
module : le jour où la bibliothèque HTTP change, la liste des fichiers à toucher est courte et
connue d'avance.

`ApiClient` reçoit sa configuration (`ApiConfig` : url de base et délai), la version du client et
le service de connectivité. Il ne connaît aucune valeur en dur. Tout échec sort en `ApiException`
scellée — `HorsLigne`, `ServeurInjoignable`, `ErreurHttp`, `ReponseInvalide` — jamais en exception
de transport, et sans jamais porter de texte destiné à l'écran (UX §13.3). La distinction entre
« pas de réseau » et « serveur en panne » qu'impose le cadrage §10.3 se décide à un seul endroit,
`classifierPanneDeTransport`, testé sans réseau.

**L'étendre, c'est l'envelopper, pas le modifier.** Jetons de session, espacement progressif et
idempotence des lots viendront comme des `BaseClient` passés au paramètre `client` du
constructeur. Ajouter un verbe (POST, flux SSE) est une méthode de plus, qui naît avec son
premier appelant — pas avant.

Le client n'a pas encore d'appelant de production : sa suite de tests est son seul usage, sur le
serveur simulé `MockClient` de `package:http/testing.dart`. L'url de base et la source de la
version du client arriveront avec la racine de composition.

> `connectivity_plus` fusionne la permission Android `ACCESS_NETWORK_STATE` dans le manifeste.
> Elle est normale et n'affiche aucune invite, mais elle apparaît dans l'APK.
