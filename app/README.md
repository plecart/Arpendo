# Arpendo — application mobile

Application Flutter, Android d'abord (`applicationId` `com.arpendo.game`). La spécification
d'interface est `documents/reference/02-specification-ux.md` ; ses jetons de conception (§1)
arrivent avec le thème, ses écrans avec leur domaine. Aujourd'hui l'app démarre sur un écran vide.

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
| `just fmt-app` / `just fmt-check-app` | `dart format` |
| `just build` | `flutter build appbundle` |

## Structure

`lib/main.dart` porte `ArpendoApp`, racine pilotée par l'état (UX §2.1) : l'écran affiché
dépendra de la séquence de démarrage. Les couches UI (vues + ViewModels) et Data (repositories +
services) naissent avec leur premier contenu, sous `lib/ui/` et `lib/data/` — aucun dossier n'est
créé avant. `lib/data/services/` existe depuis le client HTTP ; `lib/ui/` pas encore.

## Réseau

Tout ce qui parle au serveur passe par `lib/data/services/api_client.dart`. **C'est le seul
fichier de `lib/` qui importe `package:http`**, et `lib/data/services/connectivity_service.dart`
le seul qui importe `package:connectivity_plus` — deux règles vérifiables d'un `grep`, et qui
sont la raison d'être du module : le jour où la bibliothèque HTTP change, un seul fichier bouge.

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
