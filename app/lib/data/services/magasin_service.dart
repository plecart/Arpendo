import 'dart:developer' as developer;

import 'package:url_launcher/url_launcher.dart';

/// Ouvre un lien hors de l'application. Injecté pour que le service se teste
/// sans plateforme — aucun canal de méthode dans un test de widget.
typedef LanceurUrl = Future<bool> Function(Uri uri);

/// Emmène le joueur vers la fiche de l'application dans le magasin — **seul
/// fichier à importer `url_launcher`**.
///
/// Deux liens, essayés dans cet ordre :
///
/// 1. `market://details?id=…` — l'application du magasin ouvre la fiche
///    directement ;
/// 2. `https://play.google.com/store/apps/details?id=…` — le repli, pour un
///    appareil sans magasin installé (émulateur sans Play Services, appareil
///    dégooglisé), où le navigateur prend le relais.
///
/// **Si aucun des deux ne s'ouvre, rien ne se passe à l'écran** — spec UX
/// §11.2 : l'écran bloquant ne change pas, aucun message n'apparaît, et le
/// bouton reste tapable. C'est l'exception motivée à la règle du §13.3
/// (« toute erreur récupérable porte "Réessayer" ») : il n'y a rien à
/// récupérer dans l'application, le seul geste utile se fait dehors. L'échec
/// part au journal — le lot 3 de #46 y branchera Sentry.
class MagasinService {
  /// Crée le service pour [identifiantApplication] — le `packageName` que la
  /// racine lit dans `PackageInfo`, jamais une constante écrite en dur : c'est
  /// l'identifiant réellement installé qui doit être ouvert.
  MagasinService({required this.identifiantApplication, LanceurUrl? lancer})
    : _lancer = lancer ?? launchUrl;

  /// L'`applicationId` Android de l'application installée.
  final String identifiantApplication;

  final LanceurUrl _lancer;

  /// Les deux liens, dans l'ordre de préférence.
  Iterable<Uri> get _liens sync* {
    yield Uri.parse('market://details?id=$identifiantApplication');
    yield Uri.parse(
      'https://play.google.com/store/apps/details?id=$identifiantApplication',
    );
  }

  /// Ouvre la fiche du magasin, ou ne fait rien de visible.
  ///
  /// Ne lève jamais : un échec de plateforme sur le premier lien ne doit pas
  /// empêcher d'essayer le second, et l'échec des deux est un état prévu, pas
  /// une erreur à faire remonter à l'écran.
  Future<void> ouvrirFiche() async {
    for (final lien in _liens) {
      try {
        if (await _lancer(lien)) return;
      } on Exception catch (erreur) {
        developer.log(
          'lien du magasin refusé par la plateforme',
          name: 'arpendo.magasin',
          error: erreur,
        );
      }
    }
    developer.log(
      'aucun lien du magasin ouvrable — écran inchangé (§11.2)',
      name: 'arpendo.magasin',
    );
  }
}
