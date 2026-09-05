import 'dart:convert';

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

  group('assainir — la population entière des emplacements', () {
    // Le garde qui tient la classe plutôt que ses occurrences : un événement
    // dont CHAQUE emplacement porteur de texte est rempli de données
    // interdites, sérialisé comme le SDK le sérialise. Ajouter un champ au
    // fixture sans l'assainir fait rougir ce test — un `expect` par champ ne
    // l'aurait pas fait.
    SentryEvent evenementSature() => SentryEvent(
      message: SentryMessage('vu à 48.858370, 2.294481'),
      transaction: 'GET /joueur@exemple.fr',
      culprit: 'appel Bearer abc.def_ghi',
      logger: 'arpendo.joueur@exemple.fr',
      // Séparateur `, ` et non `-` : le motif partagé avec le serveur exclut
      // `-` d'entre les deux nombres, pour ne pas confondre un séparateur avec
      // le signe de la seconde composante. Lacune connue et commune aux deux
      // langages — voir la doc de `_motifs`.
      serverName: 'hote 48.858370, 2.294481',
      fingerprint: ['joueur@exemple.fr'],
      modules: {'paquet': 'joueur@exemple.fr'},
      tags: {'compte': 'joueur@exemple.fr'},
      // ignore: deprecated_member_use
      extra: {'position': 'lat=48.858370&lon=2.294481'},
      user: SentryUser(
        id: '1',
        email: 'joueur@exemple.fr',
        username: 'pseudo joueur@exemple.fr',
        name: 'joueur@exemple.fr',
        data: {'derniere': '48.858370, 2.294481'},
      ),
      request: SentryRequest(
        url: 'https://api.test/p?lat=48.858370&lon=2.294481',
        queryString: 'compte=joueur@exemple.fr',
        cookies: 'session=Bearer abc.def_ghi',
        headers: {'Authorization': 'Bearer abc.def_ghi'},
        env: {'CONTACT': 'joueur@exemple.fr'},
      ),
      exceptions: [
        SentryException(
          type: 'ApiException',
          value: '401 sur Bearer abc.def_ghi',
          mechanism: Mechanism(
            type: 'reseau',
            description: 'refus pour joueur@exemple.fr',
            data: {'compte': 'joueur@exemple.fr'},
          ),
        ),
      ],
      threads: [SentryThread(id: 1, name: 'isolat joueur@exemple.fr')],
      breadcrumbs: [
        Breadcrumb(
          message: 'ping joueur@exemple.fr',
          data: {'url': 'lat=48.858370&lon=2.294481'},
        ),
      ],
      contexts: Contexts()
        ..['partie'] = <String, dynamic>{'hote': 'joueur@exemple.fr'},
    );

    for (final interdit in ['exemple.fr', 'Bearer abc', '48.858370']) {
      test('aucun emplacement ne laisse passer « $interdit »', () {
        final sature = evenementSature();
        expect(
          jsonEncode(sature.toJson()),
          contains(interdit),
          reason: 'le fixture doit vraiment porter la donnée interdite',
        );

        expect(
          jsonEncode(assainir(sature).toJson()),
          isNot(contains(interdit)),
        );
      });
    }
  });

  group('assainir — les bornes recopiées du pendant serveur', () {
    test('le marqueur est celui de core/sentry.py', () {
      expect(retire, '[retiré]');
    });

    test('le jeton porteur est reconnu quelle que soit la casse', () {
      final evenement = SentryEvent(
        message: SentryMessage('refus pour BEARER abc.def_ghi'),
      );

      expect(
        assainir(evenement).message!.formatted,
        isNot(contains('abc.def_ghi')),
      );
    });

    test('trois décimales ne localisent pas, quatre oui', () {
      final trop = SentryEvent(message: SentryMessage('48.858, 2.294'));
      final assez = SentryEvent(message: SentryMessage('48.8583, 2.2944'));

      expect(assainir(trop).message!.formatted, '48.858, 2.294');
      expect(assainir(assez).message!.formatted, retire);
    });

    test('le seuil de décimales vaut aussi pour les nombres', () {
      // Le motif porte son `\d{4,}` en dur ; la règle des nombres, elle, lit
      // `_decimalesMinimales`. Deux chemins, deux gardes.
      final evenement = SentryEvent(
        // ignore: deprecated_member_use
        extra: {'a': 48.858, 'b': 2.294},
      );

      final assaini = assainir(evenement);

      // ignore: deprecated_member_use
      expect(assaini.extra!['a'], 48.858);
    });

    test('une paire de nombres hors des bornes d\'un degré reste', () {
      final evenement = SentryEvent(
        // ignore: deprecated_member_use
        extra: {'a': 1810.123456, 'b': 2420.654321},
      );

      final assaini = assainir(evenement);

      // ignore: deprecated_member_use
      expect(assaini.extra!['a'], 1810.123456);
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

    test('laisse son type à un contexte typé que rien ne concerne', () {
      final evenement = SentryEvent(
        contexts: Contexts()
          ..runtimes = [SentryRuntime(name: 'Dart', version: '3.13.1')],
      );

      final assaini = assainir(evenement);

      // Traverser un conteneur sans rien y changer ne doit pas le recopier :
      // le SDK range ici des objets typés, et une `List<dynamic>` rendue à sa
      // place serait une dégradation silencieuse d'une structure tierce.
      expect(
        assaini.contexts[SentryRuntime.listType],
        isA<List<SentryRuntime>>(),
      );
      expect(assaini.contexts.runtimes, hasLength(1));
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

  group('configurerSentry', () {
    test('pose le DSN reçu', () {
      final options = SentryFlutterOptions();

      configurerSentry(options, 'https://cle@sentry.test/1');

      expect(options.dsn, 'https://cle@sentry.test/1');
    });

    test('refuse les données personnelles par défaut du SDK', () {
      final options = SentryFlutterOptions();

      configurerSentry(options, 'https://cle@sentry.test/1');

      expect(options.sendDefaultPii, isFalse);
    });

    test('branche l\'assainissement sur le chemin de sortie', () async {
      final options = SentryFlutterOptions();
      configurerSentry(options, 'https://cle@sentry.test/1');

      final assaini = await options.beforeSend!(
        SentryEvent(message: SentryMessage('compte joueur@exemple.fr')),
        Hint(),
      );

      expect(assaini!.message!.formatted, isNot(contains('exemple.fr')));
    });

    test('ne demande aucune mesure de performance', () {
      final options = SentryFlutterOptions();

      configurerSentry(options, 'https://cle@sentry.test/1');

      expect(options.tracesSampleRate, isNull);
    });
  });

  group('signalerIncident', () {
    test('confie l\'erreur au rapport', () {
      final capturees = <Object>[];
      final panne = StateError('canal natif absent');

      signalerIncident(
        'sonde réseau refusée',
        source: 'arpendo.reseau',
        erreur: panne,
        capturer: (erreur, _) => capturees.add(erreur),
      );

      expect(capturees, [panne]);
    });

    test('ne rapporte rien quand il n\'y a pas d\'erreur à rapporter', () {
      var captures = 0;

      signalerIncident(
        'aucun lien du magasin ouvrable',
        source: 'arpendo.magasin',
        capturer: (_, _) => captures++,
      );

      expect(captures, 0);
    });

    test('ne lève pas quand Sentry n\'est pas initialisé', () {
      // Le capteur réel : `Sentry.captureException` sur un hub encore
      // `NoOpHub` — l'état du processus tant qu'aucun `init` n'a eu lieu, et
      // celui de tout poste de développement.
      expect(
        () => signalerIncident(
          'incident sans Sentry',
          source: 'arpendo.test',
          erreur: StateError('panne'),
        ),
        returnsNormally,
      );
    });
  });

  group('demarrerAvecRapport', () {
    test('sans DSN, lance l\'application sans toucher au SDK', () async {
      var initialisations = 0;
      var lancements = 0;

      await demarrerAvecRapport(
        dsn: '',
        lancer: () => lancements++,
        initialiser: (_, _) async => initialisations++,
      );

      expect(initialisations, 0);
      expect(lancements, 1);
    });

    test('avec un DSN, confie le lancement à l\'initialisation', () async {
      String? dsnRecu;
      var lancements = 0;

      await demarrerAvecRapport(
        dsn: 'https://cle@sentry.test/1',
        lancer: () => lancements++,
        initialiser: (dsn, lancer) async {
          dsnRecu = dsn;
          await lancer();
        },
      );

      expect(dsnRecu, 'https://cle@sentry.test/1');
      expect(lancements, 1);
    });

    test(
      'lance quand même l\'application si l\'initialisation échoue',
      () async {
        var lancements = 0;

        await demarrerAvecRapport(
          dsn: 'https://cle@sentry.test/1',
          lancer: () => lancements++,
          initialiser: (_, _) async => throw StateError('canal natif absent'),
        );

        expect(lancements, 1);
      },
    );

    test('ne lance pas deux fois si l\'échec suit le lancement', () async {
      var lancements = 0;

      await demarrerAvecRapport(
        dsn: 'https://cle@sentry.test/1',
        lancer: () => lancements++,
        initialiser: (_, lancer) async {
          await lancer();
          throw StateError('incident après le lancement');
        },
      );

      expect(lancements, 1);
    });
  });
}
