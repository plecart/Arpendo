import 'package:arpendo/data/services/api_exception.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('chaque échec se nomme dans une trace', () {
    // Sans `toString`, un journal ou un rapport Sentry (#42) ne montrerait que
    // « Instance of 'HorsLigne' » — le nom du cas noyé dans du bruit.
    expect(const HorsLigne().toString(), 'HorsLigne');
    expect(const ServeurInjoignable().toString(), 'ServeurInjoignable');
    expect(const ReponseInvalide().toString(), 'ReponseInvalide');
    expect(const ErreurHttp(503).toString(), 'ErreurHttp(503)');
  });

  group('classifierPanneDeTransport', () {
    test('sans réseau, une panne de transport est un échec hors ligne', () {
      expect(classifierPanneDeTransport(enLigne: false), isA<HorsLigne>());
    });

    test(
      'avec du réseau, une panne de transport rend le serveur injoignable',
      () {
        expect(
          classifierPanneDeTransport(enLigne: true),
          isA<ServeurInjoignable>(),
        );
      },
    );
  });
}
