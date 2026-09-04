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
/// L'ouverture passe par [ouvrir], et **c'est ce qui garde le plugin ici** :
/// la racine attend la fabrique, pas `SharedPreferences.getInstance()`, donc
/// elle n'importe pas `shared_preferences`. Une seule attente, au démarrage —
/// `getInstance` rend un singleton de processus adossé à un cache mémoire, si
/// bien que toutes les lectures qui suivent sont **synchrones**, ce dont le
/// `get` du ViewModel a besoin.
class PreferencesService {
  /// Enveloppe une instance déjà ouverte — le chemin des tests, qui posent
  /// leur propre magasin par `SharedPreferences.setMockInitialValues`.
  const PreferencesService(this._prefs);

  /// Ouvre les préférences de la plateforme. À attendre **une fois**, par la
  /// racine de composition.
  static Future<PreferencesService> ouvrir() async =>
      PreferencesService(await SharedPreferences.getInstance());

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
  ///
  /// Rend `false` si la plateforme a refusé d'écrire. Le cache mémoire, lui,
  /// est déjà à jour : le bandeau reste masqué pour cette session et
  /// reviendrait au redémarrage. Aucun appelant n'en fait rien aujourd'hui —
  /// il n'y a pas d'action à proposer au joueur pour un `commit()` refusé —
  /// mais le rendre plutôt que le jeter laisse le choix au suivant.
  Future<bool> ecarterBuildRecommande(int build) =>
      _prefs.setInt(_cleBuildRecommandeEcarte, build);
}
