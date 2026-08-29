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
/// Trois angles morts connus, faute d'un cas réel qui les justifie : un
/// littéral posé dans un `RichText` nu ou dans un `SelectableText` — l'app
/// n'écrit ni l'un ni l'autre, elle écrit des `Text` — et un texte simplement
/// clippé par un conteneur trop petit : sans `maxLines` ni `ellipsis`, le
/// paragraphe ne se déclare pas tronqué, il déborde de sa boîte en silence.
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

      // Les `Text` que l'app écrit — `Text` comme `Text.rich`. On lit le texte
      // **visible**, et lui seul : `toPlainText` inclut par défaut le
      // `semanticsLabel` d'un span, qui masquerait un littéral derrière un
      // libellé conforme, et un `U+FFFC` par `WidgetSpan`, qui ferait rougir à
      // tort un texte de l'ARB portant une icône en ligne.
      final textes = tester
          .widgetList<Text>(find.byType(Text))
          .map(
            (t) =>
                t.data ??
                t.textSpan!.toPlainText(
                  includeSemanticsLabels: false,
                  includePlaceholders: false,
                ),
          );
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

      // La troncature ne se lit que sur l'objet de rendu. On vise les
      // `RichText` issus d'un `Text` : `Icon` en rend un aussi
      // (`widgets/icon.dart`), et son glyphe n'a rien à faire ici.
      for (final paragraphe in tester.renderObjectList<RenderParagraph>(
        find.descendant(of: find.byType(Text), matching: find.byType(RichText)),
      )) {
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
