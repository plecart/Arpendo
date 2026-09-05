import 'package:arpendo/data/services/rapport_erreurs.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

void main() {
  group('assainir — le message', () {
    test('retire une paire de coordonnées', () {
      final evenement = SentryEvent(
        message: SentryMessage('échec à 48.858370, 2.294481'),
      );

      final assaini = assainir(evenement);

      expect(assaini.message!.formatted, isNot(contains('48.858370')));
      expect(assaini.message!.formatted, isNot(contains('2.294481')));
    });

    test('retire un jeton porteur', () {
      final evenement = SentryEvent(
        message: SentryMessage('refus pour Bearer eyJhbGci.OiJIUzI1NiJ9_x'),
      );

      final assaini = assainir(evenement);

      expect(assaini.message!.formatted, isNot(contains('eyJhbGci')));
      expect(assaini.message!.formatted, contains(retire));
    });

    test('retire une adresse e-mail', () {
      final evenement = SentryEvent(
        message: SentryMessage('compte joueur.un+test@exemple.fr introuvable'),
      );

      final assaini = assainir(evenement);

      expect(assaini.message!.formatted, isNot(contains('exemple.fr')));
      expect(assaini.message!.formatted, contains('introuvable'));
    });

    test('assainit aussi le gabarit et ses paramètres', () {
      final evenement = SentryEvent(
        message: SentryMessage(
          'compte introuvable',
          template: 'compte %s introuvable',
          params: ['joueur@exemple.fr'],
        ),
      );

      final assaini = assainir(evenement);

      expect(assaini.message!.params, [retire]);
      expect(assaini.message!.template, 'compte %s introuvable');
    });
  });

  group('assainir — les autres emplacements', () {
    test('retire un motif de la valeur d\'une exception', () {
      final evenement = SentryEvent(
        exceptions: [
          SentryException(
            type: 'ApiException',
            value: '401 sur Bearer abc.def_ghi',
          ),
        ],
      );

      final assaini = assainir(evenement);

      expect(assaini.exceptions!.single.value, isNot(contains('abc.def_ghi')));
      // Le type est le nom d'une classe : du code, jamais une donnée.
      expect(assaini.exceptions!.single.type, 'ApiException');
    });

    test('retire un motif du texte et des données d\'un fil d\'Ariane', () {
      final evenement = SentryEvent(
        breadcrumbs: [
          Breadcrumb(
            message: 'ping joueur@exemple.fr',
            data: {'url': 'https://api.test/p?lat=48.858370&lon=2.294481'},
          ),
        ],
      );

      final assaini = assainir(evenement);
      final fil = assaini.breadcrumbs!.single;

      expect(fil.message, isNot(contains('exemple.fr')));
      expect(fil.data!['url'], isNot(contains('48.858370')));
    });

    test('retire une paire de coordonnées écrite en nombres', () {
      final evenement = SentryEvent(
        // ignore: deprecated_member_use
        extra: {
          'position': <String, dynamic>{'lat': 48.85837, 'lon': 2.294481},
        },
      );

      final assaini = assainir(evenement);
      // ignore: deprecated_member_use
      final position = assaini.extra!['position'] as Map<String, dynamic>;

      expect(position['lat'], retire);
      expect(position['lon'], retire);
    });

    test('assainit les contextes, successeur d\'`extra`', () {
      final evenement = SentryEvent(
        contexts: Contexts()
          ..['partie'] = <String, dynamic>{'hote': 'joueur@exemple.fr'},
      );

      final assaini = assainir(evenement);
      final partie = assaini.contexts['partie'] as Map<String, dynamic>;

      expect(partie['hote'], retire);
    });

    test('assainit la valeur d\'une étiquette', () {
      final evenement = SentryEvent(tags: {'compte': 'joueur@exemple.fr'});

      final assaini = assainir(evenement);

      expect(assaini.tags!['compte'], retire);
    });
  });

  group('assainir — ce qu\'il ne touche pas', () {
    test('laisse un horodatage, qui a la forme décimale d\'un degré', () {
      final evenement = SentryEvent(
        message: SentryMessage('échec à 2026-09-05T12:35.751365Z'),
      );

      final assaini = assainir(evenement);

      expect(assaini.message!.formatted, contains('35.751365'));
    });

    test('laisse un flottant fin qui n\'a pas de voisin de même forme', () {
      final evenement = SentryEvent(
        // ignore: deprecated_member_use
        extra: {'duree': 12.345678, 'appels': 3},
      );

      final assaini = assainir(evenement);

      // ignore: deprecated_member_use
      expect(assaini.extra!['duree'], 12.345678);
    });

    test('laisse intacts le reste du message et les champs voisins', () {
      final identifiant = SentryId.newId();
      final evenement = SentryEvent(
        eventId: identifiant,
        level: SentryLevel.warning,
        message: SentryMessage('démarrage refusé : 3 tentatives'),
      );

      final assaini = assainir(evenement);

      expect(assaini.message!.formatted, 'démarrage refusé : 3 tentatives');
      expect(assaini.eventId, identifiant);
      expect(assaini.level, SentryLevel.warning);
    });
  });
}
