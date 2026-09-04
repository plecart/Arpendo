import 'dart:async';

import 'package:arpendo/data/services/api_client.dart';
import 'package:arpendo/data/services/connectivity_service.dart';
import 'package:arpendo/data/services/magasin_service.dart';
import 'package:arpendo/main.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:arpendo/ui/demarrage/ecran_attente.dart';
import 'package:arpendo/ui/demarrage/ecran_mise_a_jour.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// Réseau toujours présent, flux muet : la racine n'en teste pas plus ici.
class _ConnectiviteFigee implements ConnectivityService {
  @override
  Future<bool> isOnline() async => true;

  @override
  Stream<bool> enLigne() => const Stream.empty();
}

/// Transport qui note sa fermeture, en répondant normalement.
class _TransportFermable extends http.BaseClient {
  _TransportFermable(this._interne);

  final http.Client _interne;
  bool ferme = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest requete) =>
      _interne.send(requete);

  @override
  void close() => ferme = true;
}

http.Client _serveurNominal() => MockClient(
  (_) async => http.Response('{"min_build":1,"recommended_build":1}', 200),
);

/// Les liens que la racine a réellement demandé d'ouvrir.
late List<Uri> liensOuverts;

/// Serveur qui publie [min] et [recommande] — les deux verdicts du §11.2.
http.Client _serveurQuiPublie({required int min, required int recommande}) =>
    MockClient(
      (_) async => http.Response(
        '{"min_build":$min,"recommended_build":$recommande}',
        200,
      ),
    );

/// La racine telle que `main()` la construit, transport et réseau de test.
ArpendoApp _app({http.Client? transport, int buildActuel = 4}) {
  final connectivite = _ConnectiviteFigee();
  return ArpendoApp(
    client: ApiClient(
      config: const ApiConfig(baseUrl: 'https://exemple.test/api'),
      clientVersion: '1.2.3+4',
      connectivite: connectivite,
      client: transport ?? _serveurNominal(),
    ),
    connectivite: connectivite,
    buildActuel: buildActuel,
    // Le lanceur enregistre au lieu d'ouvrir : c'est lui qui prouve que le
    // fil bouton → service est réellement branché par la racine.
    magasin: MagasinService(
      identifiantApplication: 'com.arpendo.game',
      lancer: (uri) async {
        liensOuverts.add(uri);
        return true;
      },
    ),
  );
}

void main() {
  setUp(() => liensOuverts = []);
  testWidgets("l'application démarre sur l'écran d'attente", (tester) async {
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();

    expect(find.byType(EcranAttente), findsOneWidget);
  });

  testWidgets('build sous le minimal : la racine bascule sur le bloquant', (
    tester,
  ) async {
    // Le seul état qui **remplace** l'écran d'attente au lieu de l'habiller
    // (§11.2). C'est ici que ça se vérifie, et pas dans le test de l'écran :
    // l'écran ne sait pas quand il s'affiche, le `switch` de la racine si.
    await tester.pumpWidget(
      _app(transport: _serveurQuiPublie(min: 9, recommande: 9)),
    );
    await tester.pumpAndSettle();

    expect(find.byType(EcranMiseAJour), findsOneWidget);
    expect(
      find.byType(EcranAttente),
      findsNothing,
      reason: 'les deux à l\'écran laisseraient une sortie au joueur',
    );
  });

  testWidgets('écran bloquant : « Mettre à jour » atteint le magasin', (
    tester,
  ) async {
    // Le fil bouton → service. Ni le test de l'écran (callback feint) ni celui
    // du service (appelé à la main) ne le voient : seule la racine les relie,
    // donc c'est ici qu'il se casserait en silence.
    await tester.pumpWidget(
      _app(transport: _serveurQuiPublie(min: 9, recommande: 9)),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Mettre à jour'));
    await tester.pumpAndSettle();

    expect(liensOuverts, [Uri.parse('market://details?id=com.arpendo.game')]);
  });

  testWidgets('build sous le recommandé : le bandeau 12 atteint l\'écran', (
    tester,
  ) async {
    // La couture `modele.entreeBandeau` → `EcranAttente`. Sans ce test, la
    // racine peut passer `null` et toute la suite reste verte — mesuré.
    await tester.pumpWidget(
      _app(transport: _serveurQuiPublie(min: 1, recommande: 9)),
    );
    await tester.pumpAndSettle();

    expect(find.byType(EcranAttente), findsOneWidget);
    expect(find.text('Une nouvelle version est disponible.'), findsOneWidget);
    expect(find.text('Mettre à jour'), findsOneWidget);
    expect(
      find.text('Fermer'),
      findsNothing,
      reason:
          'le bandeau 12 n\'est pas fermable : la fermeture et la persistance '
          'qu\'elle suppose sont repoussées après le MVP (cadrage §20)',
    );
  });

  testWidgets('bandeau 12 : son action unique est branchée', (tester) async {
    await tester.pumpWidget(
      _app(transport: _serveurQuiPublie(min: 1, recommande: 9)),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Mettre à jour'));
    await tester.pumpAndSettle();

    expect(liensOuverts, [Uri.parse('market://details?id=com.arpendo.game')]);
  });

  testWidgets('la première requête est GET /version, seule et versionnée', (
    tester,
  ) async {
    final requetes = <http.BaseRequest>[];
    final reponse = Completer<http.Response>();
    await tester.pumpWidget(
      _app(
        transport: MockClient((requete) {
          requetes.add(requete);
          return reponse.future;
        }),
      ),
    );
    await tester.pump();

    expect(
      requetes,
      hasLength(1),
      reason: 'aucune autre requête avant sa réponse (§2.1)',
    );
    expect(requetes.single.method, 'GET');
    expect(requetes.single.url.path, endsWith('/version'));
    expect(
      requetes.single.headers[ApiClient.enTeteVersion],
      '1.2.3+4',
      reason: "l'en-tête porte x.y.z+N, la comparaison se fait sur N",
    );

    reponse.complete(
      http.Response('{"min_build":1,"recommended_build":1}', 200),
    );
    await tester.pumpAndSettle();
    expect(requetes, hasLength(1));
  });

  testWidgets('le démontage de la racine ferme le client', (tester) async {
    final transport = _TransportFermable(_serveurNominal());
    await tester.pumpWidget(_app(transport: transport));
    await tester.pumpAndSettle();
    expect(transport.ferme, isFalse);

    await tester.pumpWidget(const SizedBox.shrink());

    expect(
      transport.ferme,
      isTrue,
      reason:
          'le `dispose` du Provider possède le client : sans lui, les '
          'connexions persistantes survivraient à l\'application',
    );
  });

  test('une API_BASE_URL vide est refusée avec un message explicite', () {
    expect(
      () => baseUrlValidee(''),
      throwsA(
        isA<StateError>().having(
          (e) => e.message,
          'message',
          contains('API_BASE_URL'),
        ),
      ),
    );
    expect(baseUrlValidee('https://exemple.test'), 'https://exemple.test');
  });

  test('un buildNumber non entier est refusé avec un message explicite', () {
    // Sur Android, `buildNumber` est `versionCode`, toujours entier ; sur iOS
    // (phase 2), package_info_plus peut y mettre la VERSION (`1.2.3`) quand
    // aucun build n'est déclaré. Même traitement que `API_BASE_URL` : une
    // frontière de plateforme se valide, elle ne se suppose pas.
    expect(
      () => numeroDeBuildValide('1.2.3'),
      throwsA(
        isA<StateError>().having(
          (e) => e.message,
          'message',
          contains('buildNumber'),
        ),
      ),
    );
    expect(numeroDeBuildValide('7'), 7);
  });

  testWidgets('les couleurs de chrome sont lisibles depuis un écran', (
    tester,
  ) async {
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();
    final ecran = tester.element(find.byType(Scaffold).first);

    expect(
      CouleursChrome.of(ecran),
      themeArpendo(Theme.of(ecran).brightness).extension<CouleursChrome>(),
      reason:
          "un écran doit lire les couleurs de chrome du mode appliqué : `of` lève "
          "déjà si l'extension manque, mais rien ne dirait qu'elle vient d'un autre "
          'thème que celui de la racine',
    );
  });

  testWidgets('la production ne livre que le français', (tester) async {
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();

    expect(
      tester.widget<MaterialApp>(find.byType(MaterialApp)).supportedLocales,
      const [Locale('fr')],
      reason:
          '`fr-XA` est une locale de test : elle est générée et pompée par les '
          "tests, jamais livrée — seul le français l'est (cadrage §12.6)",
    );
  });

  for (final systeme in Brightness.values) {
    testWidgets('le mode sombre suit le réglage système : $systeme', (
      tester,
    ) async {
      tester.platformDispatcher.platformBrightnessTestValue = systeme;
      addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);

      await tester.pumpWidget(_app());
      await tester.pumpAndSettle();

      expect(
        Theme.of(tester.element(find.byType(Scaffold).first)).brightness,
        systeme,
        reason:
            'le mode sombre est disponible, jamais imposé : il suit le '
            'réglage système et rien d\'autre',
      );
    });
  }
}
