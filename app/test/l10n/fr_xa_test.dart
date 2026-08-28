import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../tool/allonger_arb.dart' show marqueurDebut, marqueurFin;

/// Les composants dont on vérifie le rendu sous la locale allongée.
///
/// **Toute issue qui ajoute un composant portant du texte l'ajoute ici.** La
/// liste est le seul endroit à tenir : le test qui la parcourt, lui, ne bouge
/// pas, et couvre le nouveau composant sans une ligne de plus.
final composants = <String, WidgetBuilder>{
  "l'accroche de la marque": (context) =>
      Text(AppLocalizations.of(context).demarrageAccroche),
};

/// Écran de référence de conception (spec UX §0) : le cas le plus contraint.
const ecranDeReference = Size(360, 800);

/// Monte [constructeur] sous [locale], avec les deux locales générées reconnues.
///
/// La liste des locales est celle de `gen-l10n`, et non celle de la production
/// (`fr` seul) : c'est ce qui permet au test de pomper `fr-XA` sans que l'app
/// la livre jamais.
Widget sousLocale(Locale locale, WidgetBuilder constructeur) => MaterialApp(
  locale: locale,
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  theme: themeArpendo(Brightness.light),
  home: Scaffold(body: Builder(builder: constructeur)),
);

void main() {
  testWidgets("l'accroche rend le texte cité du cadrage §1", (tester) async {
    await tester.pumpWidget(
      sousLocale(
        const Locale('fr'),
        (context) => Text(AppLocalizations.of(context).demarrageAccroche),
      ),
    );

    expect(find.text('prends du terrain'), findsOneWidget);
  });

  for (final MapEntry(key: nom, value: constructeur) in composants.entries) {
    testWidgets('$nom : tout son texte vient de l\'ARB, sans déborder', (
      tester,
    ) async {
      tester.view.physicalSize = ecranDeReference;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        sousLocale(const Locale('fr', 'XA'), constructeur),
      );

      final textes = tester
          .widgetList<Text>(find.byType(Text))
          .map((t) => t.data);
      expect(
        textes,
        isNotEmpty,
        reason: 'un composant qui ne rend aucun texte ne prouve rien',
      );
      for (final texte in textes) {
        expect(
          texte,
          allOf(startsWith(marqueurDebut), endsWith(marqueurFin)),
          reason:
              "chaîne en dur : seule une valeur passée par l'ARB porte les "
              'marqueurs de la locale allongée',
        );
      }
      expect(
        tester.takeException(),
        isNull,
        reason:
            'la spec UX §0 exige que tout conteneur absorbe +30 % de longueur '
            'sur ${ecranDeReference.width.toInt()} × '
            '${ecranDeReference.height.toInt()} dp',
      );
    });
  }
}
