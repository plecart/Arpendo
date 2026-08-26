import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'api_exception.dart';
import 'connectivity_service.dart';

/// Où joindre le serveur, et combien de temps l'attendre.
///
/// Porte **seule** ces deux valeurs : rien n'est écrit en dur dans le client.
/// En production, [baseUrl] vient de la racine de composition ; les tests la
/// choisissent librement.
class ApiConfig {
  const ApiConfig({required this.baseUrl, this.delai = delaiParDefaut});

  /// Temps accordé par défaut à une requête complète.
  ///
  /// Dix secondes : assez pour une 4G chargée, assez peu pour que le message
  /// « serveur indisponible » (cadrage §10.3) arrive avant que le joueur ne
  /// conclue au bug et ne ferme l'application — soit exactement ce que ce
  /// paragraphe cherche à éviter.
  static const delaiParDefaut = Duration(seconds: 10);

  static final _barresFinales = RegExp(r'/+$');
  static final _barresInitiales = RegExp(r'^/+');

  /// Racine de l'API, barre finale facultative.
  final String baseUrl;

  /// Temps accordé à une requête complète, connexion et réponse confondues.
  ///
  /// Un seul délai : la bibliothèque HTTP ne distingue pas l'établissement de
  /// la connexion de l'attente de la réponse.
  final Duration delai;

  /// Compose l'url absolue de [chemin] sous [baseUrl].
  ///
  /// Tolère les barres en trop comme les barres manquantes des deux côtés :
  /// `https://h/api/` + `/version` et `https://h/api` + `version` donnent tous
  /// deux `https://h/api/version`. À la différence de [Uri.resolve], aucun
  /// segment de [baseUrl] n'est perdu quand elle n'a pas de barre finale.
  Uri url(String chemin) => Uri.parse(
    '${baseUrl.replaceFirst(_barresFinales, '')}/'
    '${chemin.replaceFirst(_barresInitiales, '')}',
  );
}

/// Seul point de l'application qui parle au serveur.
///
/// **Aucun appelant n'importe `package:http`** : seuls ce client et ses
/// enveloppes connaissent la bibliothèque HTTP. Jetons de session, espacement
/// progressif et idempotence des lots s'ajouteront en enveloppant le
/// [http.Client] passé au constructeur, sans toucher à cette classe.
///
/// Toute panne réseau sort en [ApiException] : ni exception de transport ni
/// dépassement de délai ne traverse cette frontière. Une [ApiConfig] mal
/// formée, elle, est une erreur de configuration et reste une erreur de
/// programmation — c'est la racine de composition qui la refuse au démarrage.
class ApiClient {
  /// [client] n'est fourni que par les tests et les futures enveloppes ; en
  /// production, le client crée le sien.
  ApiClient({
    required this.config,
    required this.clientVersion,
    required this.connectivite,
    http.Client? client,
  }) : _client = client ?? http.Client();

  /// Nom de l'en-tête qui porte la version du client sur chaque requête.
  ///
  /// Contrat lu côté serveur : contrôle de version, journal, métriques.
  static const enTeteVersion = 'X-Client-Version';

  /// Url de base et délai, seule source de ces deux valeurs.
  final ApiConfig config;

  /// Version de l'application, posée en [enTeteVersion] sur chaque requête.
  final String clientVersion;

  /// Lecture de l'état du réseau, consultée à chaque panne de transport.
  final ConnectivityService connectivite;

  final http.Client _client;

  /// Appelle [chemin] en GET et rend le corps JSON décodé.
  ///
  /// [chemin] est relatif à la racine de l'API, avec ou sans barre initiale.
  ///
  /// Lève [HorsLigne] si le téléphone n'a pas de réseau, [ServeurInjoignable]
  /// si le réseau est là mais que le serveur n'a pas répondu à temps,
  /// [ErreurHttp] si le serveur a répondu hors de la plage 2xx, et
  /// [ReponseInvalide] si le corps n'est pas un objet JSON exploitable.
  Future<Map<String, Object?>> getJson(String chemin) async {
    final reponse = await _envoyer(config.url(chemin));
    return _objetJson(reponse.body);
  }

  /// Envoie la requête et n'en rend qu'une réponse de la plage 2xx.
  ///
  /// Pose [enTeteVersion] et applique le délai de la configuration. Toute
  /// panne de transport et tout dépassement de délai deviennent ici un échec
  /// typé ; tout statut hors 2xx devient [ErreurHttp].
  Future<http.Response> _envoyer(Uri url) async {
    final http.Response reponse;
    try {
      reponse = await _client
          .get(url, headers: {enTeteVersion: clientVersion})
          .timeout(config.delai);
    } on http.ClientException {
      throw await _panneDeTransport();
    } on TimeoutException {
      throw await _panneDeTransport();
    }
    if (!_estSucces(reponse.statusCode)) {
      throw ErreurHttp(reponse.statusCode);
    }
    return reponse;
  }

  /// Traduit une panne de transport en échec typé, réseau à l'appui.
  ///
  /// Interroge la connectivité **au moment de l'échec**, jamais avant : c'est
  /// cette lecture tardive qui distingue « pas de réseau » de « serveur en
  /// panne » (cadrage §10.3).
  Future<ApiException> _panneDeTransport() async =>
      classifierPanneDeTransport(enLigne: await connectivite.isOnline());
}

/// Le statut appartient-il à la plage de succès HTTP ?
bool _estSucces(int statut) => statut >= 200 && statut < 300;

/// Décode [corps] en objet JSON.
///
/// Lève [ReponseInvalide] si [corps] n'est pas du JSON, ou si sa racine n'est
/// pas un objet — un tableau, un nombre et un corps vide sont tous invalides
/// ici. Le corps d'une réponse est une frontière de confiance : rien n'entre
/// dans l'application sans avoir la forme attendue.
Map<String, Object?> _objetJson(String corps) {
  final Object? decode;
  try {
    decode = jsonDecode(corps);
  } on FormatException {
    throw const ReponseInvalide();
  }
  if (decode is! Map<String, Object?>) {
    throw const ReponseInvalide();
  }
  return decode;
}
