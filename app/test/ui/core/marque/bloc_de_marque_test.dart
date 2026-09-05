import 'dart:io';

import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/marque/bloc_de_marque.dart';
import 'package:arpendo/ui/core/theme/mesures.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:arpendo/ui/core/theme/typographie.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_test/flutter_test.dart';

/// Hauteur de capitale du logotype, en dp — spec UX §4.
const double _hauteurCapitale = 24;

/// Ratio hauteur de capitale / corps de Roboto Medium, **lu dans la fonte**
/// (`OS/2.sCapHeight` 1456 / `head.unitsPerEm` 2048, Roboto-Medium.ttf,
/// SDK Android platform-28) — jamais de mémoire. La constante du widget est
/// écrite indépendamment : c'est leur confrontation qui constitue le test.
const double _ratioCapitale = 1456 / 2048;

void main() {
  test('la copie du signe est identique à sa source documents/assets/', () {
    // `documents/assets/` est la source unique (README racine) : toute
    // retouche se fait là-bas puis se recopie. Ce test remplace le `md5sum`
    // manuel de la convention — une dérive silencieuse rougit ici.
    final source = File('../documents/assets/signe-arpendo.svg');
    expect(
      source.existsSync(),
      isTrue,
      reason:
          'seul test du dépôt dépendant du répertoire courant : il se lance '
          "depuis app/ (recette just). Lancé d'ailleurs, c'est cette "
          'précondition qui échoue — pas une PathNotFoundException nue',
    );
    expect(
      File('assets/signe-arpendo.svg').readAsBytesSync(),
      source.readAsBytesSync(),
    );
  });

  for (final brightness in Brightness.values) {
    testWidgets('le signe mesure 96 dp et prend primary — $brightness', (
      tester,
    ) async {
      final theme = themeArpendo(brightness);
      await _monter(tester, brightness: brightness);

      final signe = tester.widget<SvgPicture>(find.byType(SvgPicture));
      expect(signe.width, 96);
      expect(signe.height, 96);
      expect(
        signe.colorFilter,
        ColorFilter.mode(theme.colorScheme.primary, BlendMode.srcIn),
        reason:
            'srcIn conserve les opacités 0,26 / 0,52 des courbes du SVG et '
            'donne le mode sombre gratuitement — le fichier, lui, reste teinté '
            'de la valeur claire',
      );
    });
  }

  testWidgets('le logotype compose le nom à 24 dp de hauteur de capitale', (
    tester,
  ) async {
    await _monter(tester);

    final style = _styleRendu(tester, 'Arpendo');
    expect(
      style.fontSize! * _ratioCapitale,
      moreOrLessEquals(_hauteurCapitale),
      reason:
          'le §4 fixe la hauteur de capitale, pas le corps : le corps se '
          'dérive du ratio de la fonte',
    );
    expect(style.fontWeight, FontWeight.w500);
    expect(
      style.letterSpacing,
      moreOrLessEquals(style.fontSize! * 0.02),
      reason: 'interlettrage +0,02 em — identité §1.5, en em donc en × corps',
    );
    expect(
      style.fontFamily,
      'Roboto',
      reason:
          'le §1.2 amendé dit « composé en Roboto w500 ». La famille vient de '
          'la fusion avec la typographie Android de Material — ce test '
          "verrouille cette hypothèse, car le ratio de capitale 1456/2048 "
          "n'est vrai que de Roboto : sans elle, les 24 dp du §4 sont faux",
    );
    expect(
      style.height,
      1,
      reason:
          "boîte serrée sur le corps : l'interligne hérité gonflerait les "
          'écarts space-3 / space-2 que le §4 mesure entre éléments',
    );
    expect(
      style.color,
      themeArpendo(Brightness.light).colorScheme.primary,
      reason: "la teinte du mot dans l'actif `logo-arpendo.svg` est l'accent",
    );
  });

  testWidgets("l'accroche vient de l'ARB, en type-body on-surface-muted", (
    tester,
  ) async {
    await _monter(tester);

    expect(find.text('prends du terrain'), findsOneWidget);
    final style = _styleRendu(tester, 'prends du terrain');
    expect(style.fontSize, Typographie.body.fontSize);
    expect(
      style.color,
      themeArpendo(Brightness.light).colorScheme.onSurfaceVariant,
    );
  });

  testWidgets('les écarts du §4 : space-3 puis space-2', (tester) async {
    await _monter(tester);

    // Les enfants déclarés de la colonne du bloc, et non tout l'arbre :
    // `SvgPicture` pose ses propres `SizedBox` internes, qui ne sont pas des
    // écarts.
    final colonne = tester.widget<Column>(
      find
          .descendant(
            of: find.byType(BlocDeMarque),
            matching: find.byType(Column),
          )
          .first,
    );
    final ecarts = colonne.children
        .whereType<SizedBox>()
        .map((s) => s.height)
        .toList();
    expect(ecarts, [Espacements.x3, Espacements.x2]);
  });
}

/// Monte le bloc sous le thème et les textes de l'app, comme ses écrans.
Future<void> _monter(
  WidgetTester tester, {
  Brightness brightness = Brightness.light,
}) {
  return tester.pumpWidget(
    MaterialApp(
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: themeArpendo(brightness),
      home: const Scaffold(body: Center(child: BlocDeMarque())),
    ),
  );
}

/// Le style tel qu'il est peint — après les fusions de `MaterialApp`, seules
/// juges de ce que l'utilisateur voit (même méthode que `theme_test.dart`).
TextStyle _styleRendu(WidgetTester tester, String texte) =>
    tester.renderObject<RenderParagraph>(find.text(texte)).text.style!;
