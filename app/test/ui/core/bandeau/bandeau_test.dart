import 'package:arpendo/domain/bandeau/entree_bandeau.dart';
import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/bandeau/bandeau.dart';
import 'package:arpendo/ui/core/theme/icones.dart';
import 'package:arpendo/ui/core/theme/mesures.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Écran de référence de conception (spec UX §0) : le cas le plus contraint.
const _ecranDeReference = Size(360, 800);

/// Une entrée dont le test ne fixe que ce qui l'intéresse.
///
/// Le texte est un littéral : ce fichier mesure une **mise en page**, pas la
/// localisation. C'est `fr_xa_test.dart` qui prouve que le bandeau ne rend que
/// des valeurs de l'ARB.
EntreeBandeau _entree({
  Severite severite = Severite.info,
  String texte = 'Court.',
  int actions = 0,
}) => EntreeBandeau(
  priorite: 1,
  severite: severite,
  texte: (_) => texte,
  actions: List.generate(
    actions,
    (rang) => ActionBandeau(libelle: (_) => 'Action $rang', onPressed: () {}),
  ),
);

/// Monte [entree] sur l'écran de référence, dans le thème de l'application.
Future<void> _monter(
  WidgetTester tester,
  EntreeBandeau entree, {
  Brightness brightness = Brightness.light,
}) async {
  tester.view.physicalSize = _ecranDeReference;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: themeArpendo(brightness),
      home: Scaffold(
        body: Align(
          alignment: Alignment.topCenter,
          child: Bandeau(entree: entree),
        ),
      ),
    ),
  );
}

/// La hauteur que le bandeau prend réellement.
double _hauteur(WidgetTester tester) =>
    tester.getSize(find.byType(Bandeau)).height;

/// Le glyphe que le §2.4 attache à chaque sévérité — trois silhouettes.
const _glyphes = {
  Severite.info: Icones.severiteInfo,
  Severite.avertissement: Icones.severiteAvertissement,
  Severite.bloquant: Icones.severiteBloquant,
};

void main() {
  for (final MapEntry(key: severite, value: glyphe) in _glyphes.entries) {
    testWidgets('la sévérité ${severite.name} se lit à sa silhouette', (
      tester,
    ) async {
      await _monter(tester, _entree(severite: severite));

      expect(tester.widget<Icon>(find.byType(Icon)).icon, glyphe);
    });
  }

  testWidgets('la couleur du glyphe suit la sévérité', (tester) async {
    for (final severite in Severite.values) {
      await _monter(tester, _entree(severite: severite));
      final contexte = tester.element(find.byType(Icon));
      final attendue = switch (severite) {
        Severite.info => Theme.of(contexte).colorScheme.primary,
        Severite.avertissement => CouleursChrome.of(contexte).warning,
        Severite.bloquant => Theme.of(contexte).colorScheme.error,
      };

      expect(
        tester.widget<Icon>(find.byType(Icon)).color,
        attendue,
        reason: 'sévérité ${severite.name}',
      );
    }
  });

  testWidgets('le glyphe est dessiné à la taille du §1.8', (tester) async {
    await _monter(tester, _entree());

    expect(tester.getSize(find.byType(Icon)).height, Icones.taille);
  });

  testWidgets('une ligne sans action mesure 56 dp', (tester) async {
    await _monter(tester, _entree());

    expect(_hauteur(tester), 56);
  });

  testWidgets('une seconde ligne ajoute exactement une ligne de type-body', (
    tester,
  ) async {
    // Le saut de ligne explicite plutôt qu'un texte assez long pour déborder :
    // le nombre de lignes ne dépend alors ni des métriques de la police ni de
    // la largeur, et le test mesure ce qu'il prétend mesurer.
    await _monter(tester, _entree(texte: 'Première ligne\nseconde ligne'));

    expect(_hauteur(tester), 80);
  });

  testWidgets('les actions descendent sur une seconde rangée', (tester) async {
    await _monter(tester, _entree(actions: 1));

    expect(tester.getSize(find.byType(TextButton)).height, CiblesTactiles.min);
    // 16 + 24 (une ligne) + 8 (écart) + 48 (cible tactile) + 16.
    expect(_hauteur(tester), 112);
    // La seconde rangée existe pour que le message garde toute la largeur :
    // sur l'écran de référence, deux libellés longs et un message ne tiennent
    // pas côte à côte, et le garde `fr-XA` les allonge encore de 30 %.
    expect(
      tester.getTopLeft(find.byType(TextButton)).dy,
      greaterThan(tester.getBottomLeft(find.byType(Icon)).dy),
    );
  });

  for (final nombre in [0, 1, 2]) {
    testWidgets('$nombre action(s) : autant de boutons rendus', (tester) async {
      await _monter(tester, _entree(actions: nombre));

      expect(find.byType(TextButton), findsNWidgets(nombre));
    });
  }
}
