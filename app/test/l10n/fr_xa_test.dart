import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../tool/allonger_arb.dart' show marqueurDebut, marqueurFin;

/// L'accroche du bloc marque, seul texte que l'app sache rendre aujourd'hui.
Widget accroche(BuildContext context) =>
    Text(AppLocalizations.of(context).marqueAccroche);

/// Les composants dont on vérifie le rendu sous la locale allongée.
///
/// **Toute issue qui ajoute un composant portant du texte l'ajoute ici.** La
/// liste est le seul endroit à tenir : le test qui la parcourt, lui, ne bouge
/// pas, et couvre le nouveau composant sans une ligne de plus.
///
/// Deux angles morts connus, faute d'un cas réel qui les justifie : un texte
/// coupé par un `ClipRect` ou un `OverflowBox` parent — le paragraphe, lui,
/// n'est pas tronqué — et un littéral dans un `SelectableText`, qui construit
/// un `EditableText` et non un `RichText`. Aucun des deux n'existe dans `lib/`.
final composants = <String, WidgetBuilder>{"l'accroche de la marque": accroche};

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
    await tester.pumpWidget(sousLocale(const Locale('fr'), accroche));

    expect(find.text('prends du terrain'), findsOneWidget);
  });

  for (final MapEntry(key: nom, value: constructeur) in composants.entries) {
    testWidgets("$nom : son texte vient de l'ARB, sans déborder ni couper", (
      tester,
    ) async {
      tester.view.physicalSize = ecranDeReference;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        sousLocale(const Locale('fr', 'XA'), constructeur),
      );

      // Tout texte rendu passe par un `RichText`, `Text` comme `Text.rich` :
      // c'est le seul point de passage qui les voie tous, et son objet de
      // rendu porte à la fois le texte à plat et l'indicateur de troncature.
      final paragraphes = tester.renderObjectList<RenderParagraph>(
        find.byType(RichText),
      );
      expect(
        paragraphes,
        isNotEmpty,
        reason: 'un composant qui ne rend aucun texte ne prouve rien',
      );
      for (final paragraphe in paragraphes) {
        expect(
          paragraphe.text.toPlainText(),
          allOf(startsWith(marqueurDebut), endsWith(marqueurFin)),
          reason:
              "chaîne en dur : seule une valeur passée par l'ARB porte les "
              'marqueurs de la locale allongée',
        );
        expect(
          paragraphe.didExceedMaxLines,
          isFalse,
          reason:
              'texte tronqué : la spec UX §0 veut des conteneurs qui '
              'grandissent, pas qui coupent',
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
