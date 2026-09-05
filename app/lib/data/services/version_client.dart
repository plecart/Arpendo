import 'api_client.dart';
import 'api_exception.dart';

/// Les deux seuils de build publiés par `GET /version` (cadrage §14.1).
///
/// Des **numéros de build** — l'entier monotone de `version: x.y.z+N` du
/// pubspec —, jamais du semver : c'est le seul champ dont l'ordre est total et
/// déjà garanti par le magasin.
class Versions {
  /// Crée la paire de seuils. `minBuild <= recommendedBuild` est garanti par
  /// le serveur (validateur de `Settings`) ; le client ne le revérifie pas.
  const Versions({required this.minBuild, required this.recommendedBuild});

  /// En deçà : écran bloquant vers le magasin (spec UX §11.2).
  final int minBuild;

  /// En deçà : bandeau de mise à jour fermable (spec UX §2.4, ligne 12).
  final int recommendedBuild;
}

/// Lit les seuils de version du serveur — premier appelant réel d'[ApiClient].
///
/// Ne réinterprète aucun échec : les [ApiException] du transport traversent
/// telles quelles, c'est la séquence de démarrage qui les classe (« Le serveur
/// ne répond pas. », bandeau réseau…).
class VersionClient {
  /// Crée le client au-dessus d'[api], qui reste possédé par l'appelant.
  const VersionClient(this._api);

  final ApiClient _api;

  /// Appelle `GET /version` et décode la réponse.
  ///
  /// Lève [ReponseInvalide] si l'un des deux champs manque ou n'est pas un
  /// entier — le corps d'une réponse est une frontière de confiance, même
  /// venant de notre propre serveur.
  Future<Versions> lire() async {
    final corps = await _api.getJson('/version');
    final min = corps['min_build'];
    final recommande = corps['recommended_build'];
    if (min is! int || recommande is! int) {
      throw const ReponseInvalide();
    }
    return Versions(minBuild: min, recommendedBuild: recommande);
  }
}
