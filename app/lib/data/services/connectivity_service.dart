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
  /// la reprise de capture.
  ///
  /// **Ne pas se fier au premier événement pour connaître l'état initial.** Sur
  /// Android, le plugin émet l'état courant dès l'abonnement — délibérément
  /// (`ConnectivityBroadcastReceiver.onListen`, « Need to emit first event
  /// with connectivity types without waiting for first change in system ») —
  /// mais pas à chaque abonnement : le canal d'événements est mis en cache par
  /// le plugin, et `EventChannel.receiveBroadcastStream` n'appelle `onListen`
  /// qu'au passage de zéro à un auditeur. Un second abonné **simultané** n'aura
  /// donc que les changements. Un appelant qui a besoin de
  /// savoir où il en est lit [isOnline], et traite un premier événement
  /// identique comme un doublon sans conséquence.
  ///
  /// Le `distinct` est le nôtre et il est nécessaire : celui que le plugin
  /// applique déjà compare des **listes d'interfaces**, si bien qu'un passage
  /// du Wi-Fi aux données mobiles le traverse — deux événements pour un même
  /// état en ligne. Le nôtre compare l'état, donc il les réduit à un.
  ///
  /// Un **incident de plateforme** ([PlatformException]) se traduit par un « en
  /// ligne », comme dans [isOnline], sans rompre l'abonnement : les événements
  /// suivants continuent d'arriver. Conséquence assumée : un incident survenant
  /// alors que le dernier état connu était « hors ligne » fait **basculer** le
  /// flux en ligne. C'est le sens du choix du cadrage §10.3 — mieux vaut
  /// afficher « serveur indisponible » que renvoyer le joueur vérifier une
  /// connexion qui marche. Toute autre erreur remonte, pour la raison qu'expose
  /// [isOnline] : un mensonge indiscernable de la vérité est pire qu'une panne
  /// visible.
  ///
  /// La parité avec [isOnline] s'arrête là, et pas par choix : un **plugin
  /// absent de la build** ne produit aucune erreur sur ce chemin. Son
  /// [MissingPluginException] naît de l'`invokeMethod('listen')` de
  /// `EventChannel.receiveBroadcastStream`, qui la remet à
  /// `FlutterError.reportError` et jamais au flux
  /// (`services/platform_channel.dart`). Le vrai mode de panne est donc le
  /// **silence** : aucun événement, jamais, et rien à rattraper ici. C'est
  /// [isOnline] qui reste le chemin tolérant à ce cas.
  ///
  /// Chaque appel rend un flux dérivé neuf ; l'état du `distinct` est propre à
  /// chaque abonnement.
  Stream<bool> enLigne() => Connectivity().onConnectivityChanged
      .map((interfaces) => interfaces.hasConnectivity)
      .transform(
        StreamTransformer<bool, bool>.fromHandlers(
          handleError: (erreur, trace, sortie) {
            if (erreur is PlatformException) {
              sortie.add(true);
            } else {
              sortie.addError(erreur, trace);
            }
          },
        ),
      )
      .distinct();
}
