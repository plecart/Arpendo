import 'package:arpendo/data/services/api_client.dart';
import 'package:arpendo/data/services/api_exception.dart';
import 'package:arpendo/data/services/connectivity_service.dart';
import 'package:arpendo/data/services/version_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// Construit le client de version au-dessus d'un transport de test.
VersionClient _client(http.Client transport) {
  final api = ApiClient(
    config: const ApiConfig(baseUrl: 'https://exemple.test/api'),
    clientVersion: '1.2.3',
    connectivite: _ConnectiviteFigee(),
    client: transport,
  );
  addTearDown(api.close);
  return VersionClient(api);
}

/// Réseau toujours présent : ces cas ne portent pas sur la connectivité.
class _ConnectiviteFigee implements ConnectivityService {
  @override
  Future<bool> isOnline() async => true;

  @override
  Stream<bool> enLigne() => const Stream.empty();
}

void main() {
  test('décode min_build et recommended_build en Versions', () async {
    final client = _client(
      MockClient(
        (_) async =>
            http.Response('{"min_build":3,"recommended_build":7}', 200),
      ),
    );

    final versions = await client.lire();

    expect(versions.minBuild, 3);
    expect(versions.recommendedBuild, 7);
  });

  test('interroge bien /version', () async {
    late Uri url;
    final client = _client(
      MockClient((requete) async {
        url = requete.url;
        return http.Response('{"min_build":1,"recommended_build":1}', 200);
      }),
    );

    await client.lire();

    expect(url.path, endsWith('/version'));
  });

  for (final (nom, corps) in <(String, String)>[
    ('champ manquant', '{"min_build":3}'),
    ('type inattendu', '{"min_build":"3","recommended_build":7}'),
    ('booléen', '{"min_build":true,"recommended_build":7}'),
  ]) {
    test('un corps invalide — $nom — lève ReponseInvalide', () async {
      final client = _client(
        MockClient((_) async => http.Response(corps, 200)),
      );

      await expectLater(client.lire(), throwsA(isA<ReponseInvalide>()));
    });
  }

  test("une panne d'ApiClient traverse telle quelle", () async {
    final client = _client(
      MockClient((_) async => http.Response('indisponible', 503)),
    );

    // Le client de version ne réinterprète pas les échecs : la séquence de
    // démarrage les classe elle-même (HorsLigne, ServeurInjoignable…).
    await expectLater(client.lire(), throwsA(isA<ErreurHttp>()));
  });
}
