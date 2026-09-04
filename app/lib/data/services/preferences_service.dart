import 'package:shared_preferences/shared_preferences.dart';

/// Les préférences locales de l'application — **seul fichier à importer
/// `shared_preferences`**, comme `api_client.dart` est le seul à importer
/// `http`.
///
/// Il ne garde que ce qu'un redémarrage doit retrouver, et **rien de
/// sensible** : ni jeton, ni identifiant, ni coordonnée. Le stockage d'Android
/// n'est pas chiffré et une sauvegarde système le recopie ailleurs.
///
/// Le service **stocke, il n'arbitre pas** : c'est la séquence de démarrage
/// qui décide ce que valent ces valeurs — la condition de la ligne 12 du
/// bandeau (« recommandée non atteinte **et** non fermée pour cette version »)
/// lui appartient, comme l'écrit `domain/bandeau/lignes.dart`.
///
/// L'instance de [SharedPreferences] est **reçue**, pas ouverte ici : sa
/// lecture est asynchrone une fois pour toutes, au démarrage, et la racine de
/// composition est le seul endroit du projet où l'attendre. Les lectures qui
/// suivent sont donc synchrones, ce dont le `get` du ViewModel a besoin.
class PreferencesService {
  /// Enveloppe [_prefs], déjà ouvert par la racine de composition.
  const PreferencesService(this._prefs);

  final SharedPreferences _prefs;

  /// Le build recommandé pour lequel le joueur a fermé le bandeau 12.
  static const _cleBuildRecommandeEcarte = 'build_recommande_ecarte';

  /// Le dernier build recommandé dont le bandeau a été fermé, ou `null` si
  /// le joueur n'en a jamais fermé.
  ///
  /// Synchrone : la valeur vient du cache déjà chargé.
  int? buildRecommandeEcarte() => _prefs.getInt(_cleBuildRecommandeEcarte);

  /// Retient que le bandeau de mise à jour a été fermé pour [build].
  ///
  /// Un **seul** entier est gardé, celui de la dernière fermeture : la spec
  /// (§11.2) ne demande pas d'historique, seulement que le bandeau ne
  /// revienne pas pour la même version.
  Future<void> ecarterBuildRecommande(int build) =>
      _prefs.setInt(_cleBuildRecommandeEcarte, build);
}
