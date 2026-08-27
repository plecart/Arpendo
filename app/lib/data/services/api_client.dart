import 'dart:async';
import 'dart:convert';
import 'dart:io';

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
  ///
  /// **Fournir [client], c'est en céder la possession** : [close] ferme le
  /// [http.Client] que ce client tient, qu'il l'ait créé ou reçu. Une seule
  /// règle, sans drapeau de propriété — un appelant qui doit garder son client
  /// vivant ne le donne pas, il en donne une enveloppe dont `close` ne fait
  /// rien.
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
  /// Le corps est décodé en UTF-8 depuis ses octets, sans consulter
  /// `Content-Type` : JSON est UTF-8 par définition (RFC 8259).
  ///
  /// Lève [HorsLigne] si le téléphone n'a pas de réseau, [ServeurInjoignable]
  /// si le réseau est là mais que le serveur n'a pas répondu à temps,
  /// [ErreurHttp] si le serveur a répondu hors de la plage 2xx, et
  /// [ReponseInvalide] si le corps n'est pas un objet JSON exploitable.
  Future<Map<String, Object?>> getJson(String chemin) async {
    final reponse = await _envoyer(config.url(chemin));
    return _objetJson(reponse.bodyBytes);
  }

  /// Libère le [http.Client] détenu ; ce client n'est plus utilisable ensuite.
  ///
  /// Sans cet appel, les connexions persistantes du client restent ouvertes et
  /// le processus Dart peut refuser de se terminer. À appeler par qui possède
  /// le [ApiClient] — la racine de composition, ou le `tearDown` d'un test.
  void close() => _client.close();

  /// Envoie la requête et n'en rend qu'une réponse de la plage 2xx.
  ///
  /// Pose [enTeteVersion] et applique le délai de la configuration. Toute
  /// panne de transport et tout dépassement de délai deviennent ici un échec
  /// typé ; tout statut hors 2xx devient [ErreurHttp].
  ///
  /// Les trois familles d'échec de transport se rattrapent séparément parce
  /// qu'aucune n'hérite des autres : [http.ClientException] pour ce que la
  /// bibliothèque enveloppe elle-même, [IOException] pour ce qu'elle laisse
  /// passer — [SocketException] hors de son chemin, et surtout [TlsException]
  /// et [HandshakeException], le cas du portail captif —, [TimeoutException]
  /// pour le délai. Sans la clause [IOException], une erreur de certificat
  /// traverserait la frontière en exception brute.
  Future<http.Response> _envoyer(Uri url) async {
    final http.Response reponse;
    try {
      reponse = await _client
          .get(url, headers: {enTeteVersion: clientVersion})
          .timeout(config.delai);
    } on http.ClientException {
      throw await _panneDeTransport();
    } on IOException {
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

/// Décode [octets] en objet JSON, UTF-8 puis JSON.
///
/// Prend les **octets** du corps et non son texte : `Content-Type` ne décide
/// pas du jeu de caractères, JSON est UTF-8 par définition (RFC 8259). Lu par
/// [http.Response.body], un corps servi sans `charset` sous un type autre que
/// `application/json` serait décodé en latin1, et « Réessayer » arriverait en
/// « RÃ©essayer ».
///
/// Lève [ReponseInvalide] si [octets] n'est pas de l'UTF-8 valide, si le texte
/// obtenu n'est pas du JSON, ou si sa racine n'est pas un objet — un tableau,
/// un nombre et un corps vide sont tous invalides ici. Les deux décodages
/// échouent sur la même [FormatException], et c'est voulu : le corps d'une
/// réponse est une frontière de confiance, et l'appelant n'a rien à faire de
/// la couche qui a rejeté les octets.
Map<String, Object?> _objetJson(List<int> octets) {
  final Object? decode;
  try {
    decode = jsonDecode(utf8.decode(octets));
  } on FormatException {
    throw const ReponseInvalide();
  }
  if (decode is! Map<String, Object?>) {
    throw const ReponseInvalide();
  }
  return decode;
}
