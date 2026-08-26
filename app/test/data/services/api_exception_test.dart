import 'package:arpendo/data/services/api_exception.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
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
