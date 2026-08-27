import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:arpendo/data/services/api_client.dart';
import 'package:arpendo/data/services/api_exception.dart';
import 'package:arpendo/data/services/connectivity_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// Connectivité figée : les tests décident de l'état du réseau sans y toucher.
class _ConnectiviteFigee implements ConnectivityService {
  const _ConnectiviteFigee({required this.enLigne});

  final bool enLigne;

  @override
  Future<bool> isOnline() async => enLigne;
}

ApiClient _client(
  http.Client transport, {
  bool enLigne = true,
  String baseUrl = 'https://exemple.test/api',
  Duration delai = ApiConfig.delaiParDefaut,
}) {
  final client = ApiClient(
    config: ApiConfig(baseUrl: baseUrl, delai: delai),
    clientVersion: '1.2.3',
    connectivite: _ConnectiviteFigee(enLigne: enLigne),
    client: transport,
  );
  // Chaque test exerce ainsi la règle « injecter un client, c'est le céder ».
  addTearDown(client.close);
  return client;
}

/// Transport qui note sa fermeture, et rien d'autre.
class _TransportFermable extends http.BaseClient {
  bool ferme = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest requete) async =>
      http.StreamedResponse(const Stream.empty(), 200);

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
  test("close ferme le client injecté : l'injecter, c'est le céder", () {
    final transport = _TransportFermable();

    _client(transport).close();

    expect(transport.ferme, isTrue);
  });

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

  test("barres en trop ou en moins, l'url se compose sans perte", () async {
    late Uri urlAppelee;
    final client = _client(
      MockClient((requete) async {
        urlAppelee = requete.url;
        return http.Response('{}', 200);
      }),
      baseUrl: 'https://exemple.test/api/',
    );

    await client.getJson('/version');

    expect(urlAppelee.toString(), 'https://exemple.test/api/version');
  });

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

  test('passé le délai, le serveur est injoignable', () async {
    final client = _client(
      MockClient((_) => Completer<http.Response>().future),
      delai: const Duration(milliseconds: 20),
    );

    await expectLater(
      client.getJson('version'),
      throwsA(isA<ServeurInjoignable>()),
    );
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
