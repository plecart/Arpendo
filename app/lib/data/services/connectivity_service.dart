import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/services.dart';

/// Lit l'état du réseau du téléphone.
///
/// **Seul point de l'application qui connaît `connectivity_plus`.** Tout le
/// reste dépend de cette classe, jamais du plugin : [isOnline] répond
/// ponctuellement, [enLigne] suit les changements, et l'importation du plugin
/// reste unique.
///
/// Ne sonde pas Internet, seulement les interfaces radio : derrière un portail
/// captif, le téléphone est « en ligne » et le serveur reste injoignable. C'est
/// assumé — le message « serveur indisponible » reste juste dans ce cas.
class ConnectivityService {
  /// Le téléphone a-t-il au moins une interface réseau active ?
  ///
  /// Renvoie `true` dès qu'une interface est active, quel que soit son type
  /// (Wi-Fi, mobile, Ethernet, VPN…), `false` si le téléphone n'en a aucune.
  ///
  /// N'échoue pas sur un **incident de plateforme** — canal natif en erreur
  /// ([PlatformException]) ou plugin absent de la build
  /// ([MissingPluginException]) : la méthode suppose alors le réseau
  /// **présent**. C'est le choix le moins nuisible du cadrage §10.3 —
  /// « serveur indisponible » invite à garder l'application ouverte, là où
  /// « pas de connexion » enverrait le joueur vérifier une connexion qui
  /// marche, et donc fermer l'application.
  ///
  /// Toute **autre** erreur remonte. Rattraper `Exception` en bloc ferait
  /// répondre « en ligne » à un bogue de cette classe aussi bien qu'à un
  /// incident natif, et le mensonge serait indiscernable de la vérité. Ces
  /// incidents ne laissent encore aucune trace : elle viendra avec le Sentry
  /// de l'app (#46), et surtout pas par un `print`.
  Future<bool> isOnline() async {
    try {
      return (await Connectivity().checkConnectivity()).hasConnectivity;
    } on PlatformException {
      return true;
    } on MissingPluginException {
      return true;
    }
  }

  /// Le téléphone est-il en ligne, et le reste-t-il ? Un événement par
  /// changement d'état, et rien tant que l'état ne change pas.
  ///
  /// C'est ce qui alimente la ligne 5 du bandeau (spec UX §2.4) et, plus tard,
  /// la reprise de capture. Le flux n'émet **pas** l'état courant à
  /// l'abonnement : il ne rapporte que des changements. Un appelant qui a
  /// besoin de savoir où il en est au démarrage lit [isOnline] d'abord.
  ///
  /// Le `distinct` est le nôtre et il est nécessaire : celui que le plugin
  /// applique déjà compare des **listes d'interfaces**, si bien qu'un passage
  /// du Wi-Fi aux données mobiles le traverse — deux événements pour un même
  /// état en ligne. Le nôtre compare l'état, donc il les réduit à un.
  ///
  /// Même tolérance aux **incidents de plateforme** que [isOnline] : une
  /// [PlatformException] ou une [MissingPluginException] sur le flux se
  /// traduit par un « en ligne », sans rompre l'abonnement — les événements
  /// suivants continuent d'arriver. Toute autre erreur remonte, pour la raison
  /// qu'expose [isOnline] : un mensonge indiscernable de la vérité est pire
  /// qu'une panne visible. Conséquence assumée : un incident survenant alors
  /// que le dernier état connu était « hors ligne » fait **basculer** le flux
  /// en ligne. C'est le sens du choix du cadrage §10.3 — mieux vaut afficher
  /// « serveur indisponible » que renvoyer le joueur vérifier une connexion
  /// qui marche.
  ///
  /// Chaque appel rend un flux dérivé neuf ; l'état du `distinct` est propre à
  /// chaque abonnement.
  Stream<bool> enLigne() => Connectivity().onConnectivityChanged
      .map((interfaces) => interfaces.hasConnectivity)
      .transform(
        StreamTransformer<bool, bool>.fromHandlers(
          handleError: (erreur, trace, sortie) {
            if (erreur is PlatformException ||
                erreur is MissingPluginException) {
              sortie.add(true);
            } else {
              sortie.addError(erreur, trace);
            }
          },
        ),
      )
      .distinct();
}
