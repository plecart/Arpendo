import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:arpendo/data/services/api_client.dart';
import 'package:arpendo/data/services/api_exception.dart';
import 'package:arpendo/data/services/connectivity_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// Délai des cas qui attendent volontairement qu'il expire — assez court pour
/// que la suite reste rapide, assez long pour ne pas dépendre de la charge.
const _delaiCourt = Duration(milliseconds: 200);

/// Connectivité figée : les tests décident de l'état du réseau sans y toucher.
class _ConnectiviteFigee implements ConnectivityService {
  const _ConnectiviteFigee({required this.enLigne});

  final bool enLigne;

  @override
  Future<bool> isOnline() async => enLigne;
}

/// Les quatre combinaisons de barres que [ApiConfig.url] doit toutes absorber.
///
/// La matrice entière, et pas seulement la barre en trop : la promesse porte
/// aussi sur la barre manquante des deux côtés, où [Uri.resolve] perdrait le
/// segment `/api`.
const _compositionsDUrl = <(String, String)>[
  ('https://exemple.test/api/', '/version'),
  ('https://exemple.test/api/', 'version'),
  ('https://exemple.test/api', '/version'),
  ('https://exemple.test/api', 'version'),
];

/// Configuration des cas qui n'ont d'avis ni sur l'url ni sur le délai.
///
/// Le délai n'est pas nommé : sa valeur par défaut appartient à [ApiConfig], et
/// la redire ici en ferait une seconde source à tenir.
const _configParDefaut = ApiConfig(baseUrl: 'https://exemple.test/api');

/// Construit un client de test.
///
/// [transport] à `null` laisse [ApiClient] construire son client par défaut —
/// le seul moyen d'exercer ce qu'il borne, puisqu'il est privé au module.
ApiClient _client(
  http.Client? transport, {
  bool enLigne = true,
  ApiConfig config = _configParDefaut,
}) {
  final client = ApiClient(
    config: config,
    clientVersion: '1.2.3',
    connectivite: _ConnectiviteFigee(enLigne: enLigne),
    client: transport,
  );
  // Chaque test exerce ainsi la règle « injecter un client, c'est le céder ».
  addTearDown(client.close);
  return client;
}

/// Serveur local qui n'écrit que ce que [repondre] veut bien écrire.
///
/// Rend l'url de base à donner à [ApiConfig] ; le serveur se ferme avec le
/// test. Un [MockClient] ne conviendrait pas ici : ces cas portent sur ce que
/// le client **par défaut** borne, donc sur un vrai transport.
Future<String> _serveurLocal(
  void Function(HttpRequest requete) repondre,
) async {
  final serveur = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
  addTearDown(() => serveur.close(force: true));
  serveur.listen(repondre);
  return 'http://${serveur.address.host}:${serveur.port}';
}

/// Transport qui note sa fermeture, et rien d'autre.
class _TransportFermable extends http.BaseClient {
  bool ferme = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest requete) =>
      throw UnsupportedError("ce transport ne sert qu'à observer close");

  @override
  void close() => ferme = true;
}

/// Transport qui lève [erreur] avant d'avoir joint le serveur.
http.Client _transportQuiLeve(Object erreur) =>
    MockClient((_) async => throw erreur);

/// Les familles de panne de transport que le client doit toutes classer.
///
/// `http` n'en enveloppe qu'une : `IOClient.send` convertit [SocketException]
/// et [HttpException] en [http.ClientException], et laisse passer le reste —
/// dont [HandshakeException], le cas du portail captif. En ajouter une famille
/// est une ligne de plus ici.
final _famillesDePanne = <(String, Object)>[
  ('http', http.ClientException('transport')),
  ('tls', const HandshakeException('poignée de main')),
];

void main() {
  test('une réponse 200 rend le corps JSON décodé', () async {
    final client = _client(
      MockClient((_) async => http.Response('{"version":"1.0.0"}', 200)),
    );

    expect(await client.getJson('version'), {'version': '1.0.0'});
  });

  test("le corps est décodé en utf-8, quel que soit l'en-tête", () async {
    final client = _client(
      MockClient(
        (_) async =>
            http.Response.bytes(utf8.encode('{"nom":"Réessayer"}'), 200),
      ),
    );

    expect(await client.getJson('version'), {'nom': 'Réessayer'});
  });

  test('toute requête porte la version du client', () async {
    late http.BaseRequest requeteRecue;
    final client = _client(
      MockClient((requete) async {
        requeteRecue = requete;
        return http.Response('{}', 200);
      }),
    );

    await client.getJson('version');

    expect(requeteRecue.headers['X-Client-Version'], '1.2.3');
  });

  for (final (base, chemin) in _compositionsDUrl) {
    test("« $base » + « $chemin » se composent sans perte", () async {
      late Uri urlAppelee;
      final client = _client(
        MockClient((requete) async {
          urlAppelee = requete.url;
          return http.Response('{}', 200);
        }),
        config: ApiConfig(baseUrl: base),
      );

      await client.getJson(chemin);

      expect(urlAppelee.toString(), 'https://exemple.test/api/version');
    });
  }

  test('une réponse 500 devient une erreur http portant son statut', () async {
    final client = _client(MockClient((_) async => http.Response('', 500)));

    await expectLater(
      client.getJson('version'),
      throwsA(isA<ErreurHttp>().having((e) => e.statut, 'statut', 500)),
    );
  });

  for (final (famille, panne) in _famillesDePanne) {
    test('sans réseau, une panne $famille laisse hors ligne', () async {
      final client = _client(_transportQuiLeve(panne), enLigne: false);

      await expectLater(client.getJson('version'), throwsA(isA<HorsLigne>()));
    });

    test(
      'avec du réseau, une panne $famille rend le serveur injoignable',
      () async {
        final client = _client(_transportQuiLeve(panne));

        await expectLater(
          client.getJson('version'),
          throwsA(isA<ServeurInjoignable>()),
        );
      },
    );
  }

  test("close ferme le client injecté : l'injecter, c'est le céder", () {
    final transport = _TransportFermable();

    _client(transport).close();

    expect(transport.ferme, isTrue);
  });

  test('close atteint le client par défaut, pas que son enveloppe', () async {
    // Un serveur qui répond vraiment : sans lui, une requête d'après-fermeture
    // échouerait de toute façon en délai dépassé, et le test passerait au vert
    // sans rien prouver.
    final client = _client(
      null,
      config: ApiConfig(
        baseUrl: await _serveurLocal((requete) {
          requete.response.write('{}');
          unawaited(requete.response.close());
        }),
      ),
    );
    expect(await client.getJson('version'), <String, Object?>{});

    client.close();

    // Un client `dart:io` fermé refuse toute requête suivante : c'est la seule
    // trace observable, de l'extérieur, que la fermeture a bien traversé le
    // client borné jusqu'au vrai transport.
    await expectLater(
      client.getJson('version'),
      throwsA(isA<ServeurInjoignable>()),
    );
  });

  test("le client par défaut borne l'attente des en-têtes", () async {
    final client = _client(
      null,
      config: ApiConfig(
        baseUrl: await _serveurLocal((_) {}),
        delai: _delaiCourt,
      ),
    );

    await expectLater(
      client.getJson('version'),
      throwsA(isA<ServeurInjoignable>()),
    );
  });

  test("le client par défaut borne aussi l'attente du corps", () async {
    final client = _client(
      null,
      config: ApiConfig(
        baseUrl: await _serveurLocal((requete) {
          // En-têtes et un premier morceau, puis plus rien : sans borne sur le
          // flux, l'application attendrait ce corps indéfiniment.
          requete.response.write('{"nom":');
          unawaited(requete.response.flush());
        }),
        delai: _delaiCourt,
      ),
    );

    await expectLater(
      client.getJson('version'),
      throwsA(isA<ServeurInjoignable>()),
    );
  });

  test("le délai ne coupe pas une enveloppe injectée qui réessaie", () async {
    // Une enveloppe d'espacement progressif tient jusqu'à ~30 s (Territoire) :
    // le délai borne ses tentatives, jamais la séquence qu'elle enchaîne.
    final client = _client(
      MockClient((_) async {
        await Future<void>.delayed(_delaiCourt * 4);
        return http.Response('{}', 200);
      }),
      config: const ApiConfig(
        baseUrl: 'https://exemple.test/api',
        delai: _delaiCourt,
      ),
    );

    expect(await client.getJson('version'), <String, Object?>{});
  });

  test('un corps 200 aux octets utf-8 invalides est invalide', () async {
    final client = _client(
      MockClient((_) async => http.Response.bytes([0x7b, 0xff, 0x7d], 200)),
    );

    await expectLater(
      client.getJson('version'),
      throwsA(isA<ReponseInvalide>()),
    );
  });

  test('un corps 200 illisible devient une réponse invalide', () async {
    final client = _client(
      MockClient((_) async => http.Response('pas du json', 200)),
    );

    await expectLater(
      client.getJson('version'),
      throwsA(isA<ReponseInvalide>()),
    );
  });

  test("un corps 200 qui n'est pas un objet est invalide", () async {
    final client = _client(
      MockClient((_) async => http.Response('[1,2]', 200)),
    );

    await expectLater(
      client.getJson('version'),
      throwsA(isA<ReponseInvalide>()),
    );
  });
}
