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
        fragment: 'joueur@exemple.fr',
        data: {'corps': 'vu à 48.858370, 2.294481'},
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

    test('rend le conteneur reçu lui-même quand rien n\'a bougé', () {
      // Ce qui fait tenir la préservation de type : une chaîne inchangée est
      // rendue **identique**, donc le conteneur qui la porte l'est aussi.
      // Sans cette identité, chaque carte traversée serait recopiée pour rien.
      // ignore: deprecated_member_use
      final evenement = SentryEvent(extra: {'note': 'rien de sensible ici'});
      // Et non la carte passée au constructeur : `SentryEvent` la recopie
      // (`Map.from`, mesuré). C'est la carte que l'événement PORTE dont
      // l'identité se juge.
      // ignore: deprecated_member_use
      final avant = evenement.extra;

      // ignore: deprecated_member_use
      expect(identical(assainir(evenement).extra, avant), isTrue);
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

    test('pose le taux d\'échantillonnage reçu', () {
      final options = SentryFlutterOptions();

      configurerSentry(options, 'https://cle@sentry.test/1', tauxEnvoi: 0.25);

      expect(options.sampleRate, 0.25);
    });

    test('envoie tout quand le taux n\'est pas configuré', () {
      // Cadrage §16 : l'échantillonnage est un garde-fou de **coût**, pas un
      // interrupteur. Un taux absent ne doit donc pas éteindre la collecte —
      // il la laisse entière, comme le `1.0` du poste.
      final options = SentryFlutterOptions();

      configurerSentry(options, 'https://cle@sentry.test/1', tauxEnvoi: null);

      expect(options.sampleRate, 1.0);
    });

    test('refuse un taux hors des bornes plutôt que de le subir', () {
      // Mêmes bornes que le `SampleRate` de l'api, et pour les deux mêmes
      // raisons : zéro n'est pas « moins d'événements » mais aucun — un Sentry
      // configuré, facturé et muet — et au-dessus de 1 le SDK ne rogne pas, il
      // retient la valeur telle quelle et se comporte comme à 1.
      for (final horsBornes in [0.0, -0.5, 1.5]) {
        expect(
          () => configurerSentry(
            SentryFlutterOptions(),
            'https://cle@sentry.test/1',
            tauxEnvoi: horsBornes,
          ),
          throwsArgumentError,
          reason: '$horsBornes doit être refusé',
        );
      }
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

  group('tauxEnvoiValide', () {
    test('une variable absente veut dire « tout envoyer »', () {
      expect(tauxEnvoiValide(''), isNull);
    });

    test('lit un taux', () {
      expect(tauxEnvoiValide('0.25'), 0.25);
    });

    test('refuse une valeur qui n\'est pas un nombre', () {
      // Le mode de panne visé : quelqu'un pose un plafond de coût, se trompe
      // de forme, et l'application envoie 100 % sans que rien ne le dise.
      expect(() => tauxEnvoiValide('un quart'), throwsArgumentError);
    });
  });

  group('demarrerAvecRapport', () {
    test('transmet le taux d\'envoi à l\'initialisation', () async {
      double? tauxRecu;

      await demarrerAvecRapport(
        dsn: 'https://cle@sentry.test/1',
        tauxEnvoi: 0.25,
        lancer: () {},
        initialiser: (_, taux, lancer) async {
          tauxRecu = taux;
          await lancer();
        },
      );

      expect(tauxRecu, 0.25);
    });

    test('sans DSN, lance l\'application sans toucher au SDK', () async {
      var initialisations = 0;
      var lancements = 0;

      await demarrerAvecRapport(
        dsn: '',
        lancer: () => lancements++,
        initialiser: (_, _, _) async => initialisations++,
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
        initialiser: (dsn, _, lancer) async {
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
          initialiser: (_, _, _) async =>
              throw StateError('canal natif absent'),
        );

        expect(lancements, 1);
      },
    );

    test('laisse remonter une panne du lancement, pas du SDK', () async {
      // Le SDK appelle `lancer` lui-même : une exception de l'application
      // traverse donc `initialiser` et arrive au même `catch` qu'une panne de
      // Sentry. Les confondre annulerait en silence le refus de démarrer sans
      // `API_BASE_URL` — et en production seulement, où un DSN est posé.
      final panne = StateError('API_BASE_URL absente');

      await expectLater(
        demarrerAvecRapport(
          dsn: 'https://cle@sentry.test/1',
          lancer: () => throw panne,
          initialiser: (_, _, lancer) => lancer() as Future<void>,
        ),
        throwsA(same(panne)),
      );
    });

    test('ne lance qu\'une fois même sur deux appels concurrents', () async {
      // La garde tient parce que `lance` est posé **avant** l'attente. Le
      // déplacer après laisserait les deux appels franchir le test ensemble —
      // deux `runApp`, et rien pour le voir.
      var lancements = 0;

      await demarrerAvecRapport(
        dsn: 'https://cle@sentry.test/1',
        lancer: () async {
          await Future<void>.delayed(Duration.zero);
          lancements++;
        },
        initialiser: (_, _, lancer) async =>
            Future.wait([lancer() as Future<void>, lancer() as Future<void>]),
      );

      expect(lancements, 1);
    });

    test('ne lance pas deux fois si l\'échec suit le lancement', () async {
      var lancements = 0;

      // L'application est montée, puis le SDK échoue : la panne remonte —
      // quelque chose a bel et bien cassé — mais elle ne relance rien. Une
      // exception après `runApp` ne défait pas l'arbre de widgets déjà
      // attaché ; un second lancement, lui, le ferait.
      await expectLater(
        demarrerAvecRapport(
          dsn: 'https://cle@sentry.test/1',
          lancer: () => lancements++,
          initialiser: (_, _, lancer) async {
            await lancer();
            throw StateError('incident après le lancement');
          },
        ),
        throwsStateError,
      );

      expect(lancements, 1);
    });
  });
}
