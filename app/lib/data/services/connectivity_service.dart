import 'package:connectivity_plus/connectivity_plus.dart';

/// Lit l'état du réseau du téléphone.
///
/// **Seul point de l'application qui connaît `connectivity_plus`.** Tout le
/// reste dépend de cette classe, jamais du plugin : le flux d'événements de
/// connectivité dont auront besoin les bandeaux sera une méthode de plus ici,
/// et l'importation du plugin restera unique.
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
  /// N'échoue jamais sur un incident de plateforme (canal natif absent ou en
  /// erreur) : la méthode suppose alors le réseau **présent**. C'est le choix
  /// le moins nuisible du cadrage §10.3 — « serveur indisponible » invite à
  /// garder l'application ouverte, là où « pas de connexion » enverrait le
  /// joueur vérifier une connexion qui marche, et donc fermer l'application.
  Future<bool> isOnline() async {
    try {
      return (await Connectivity().checkConnectivity()).hasConnectivity;
    } on Exception {
      return true;
    }
  }
}
