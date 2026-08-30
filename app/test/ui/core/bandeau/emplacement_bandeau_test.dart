import 'package:arpendo/domain/bandeau/entree_bandeau.dart';
import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/bandeau/bandeau.dart';
import 'package:arpendo/ui/core/bandeau/emplacement_bandeau.dart';
import 'package:arpendo/ui/core/theme/mouvement.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Une entrée d'une ligne, la plus courte possible : ce fichier mesure une
/// transition, pas une mise en page.
final _entree = EntreeBandeau(
  priorite: 5,
  severite: Severite.avertissement,
  texte: (_) => 'Court.',
  actions: const [],
);

/// La hauteur qu'occupe l'emplacement, bandeau compris.
double _hauteur(WidgetTester tester) =>
    tester.getSize(find.byType(EmplacementBandeau)).height;

/// Monte l'emplacement portant [entree], animations coupées si [immobile].
Future<void> _monter(
  WidgetTester tester,
  EntreeBandeau? entree, {
  bool immobile = false,
}) => tester.pumpWidget(
  MaterialApp(
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    theme: themeArpendo(Brightness.light),
    home: MediaQuery(
      data: MediaQueryData(disableAnimations: immobile),
      child: Scaffold(
        body: Align(
          alignment: Alignment.topCenter,
          child: EmplacementBandeau(entree: entree),
        ),
      ),
    ),
  ),
);

void main() {
  testWidgets("sans entrée, l'emplacement ne prend aucune place", (
    tester,
  ) async {
    await _monter(tester, null);

    expect(find.byType(Bandeau), findsNothing);
    expect(_hauteur(tester), 0);
  });

  testWidgets('la sortie dure 75 % de l\'entrée, pas autant qu\'elle', (
    tester,
  ) async {
    await _monter(tester, _entree);
    final pleine = _hauteur(tester);
    expect(pleine, greaterThan(0));
    // Les durées se lisent par le point de passage obligé du §1.6, jamais en
    // clair : un test qui recopierait 180 ms cesserait de mesurer le jour où
    // le jeton change, au lieu de rougir.
    final mouvement = Mouvement.of(
      tester.element(find.byType(EmplacementBandeau)),
    );
    final sortie = mouvement.sortie(JetonMouvement.base);
    final entree = mouvement.entree(JetonMouvement.base);
    expect(sortie, lessThan(entree), reason: 'le jeton lui-même');

    await _monter(tester, null);
    await tester.pump();
    // Juste avant la fin de la sortie : la place n'est pas encore rendue.
    await tester.pump(sortie - const Duration(milliseconds: 1));
    expect(_hauteur(tester), greaterThan(0));

    // Un souffle plus tard, elle l'est — c'est ce qui distingue une sortie de
    // 75 % d'une sortie qui durerait aussi longtemps que l'entrée : à cet
    // instant, une animation calée sur l'entrée serait encore en cours.
    await tester.pump(const Duration(milliseconds: 2));
    expect(_hauteur(tester), 0);
  });

  testWidgets('la place se libère progressivement, jamais par un saut', (
    tester,
  ) async {
    await _monter(tester, _entree);
    final pleine = _hauteur(tester);
    final sortie = Mouvement.of(tester.element(find.byType(EmplacementBandeau)))
        .sortie(JetonMouvement.base);

    await _monter(tester, null);
    await tester.pump();
    await tester.pump(sortie ~/ 2);

    // À mi-parcours, la sortie a **peu** avancé : la courbe d'entrée jouée à
    // l'envers est le miroir temporel de `easeInCubic`, donc elle démarre
    // lentement. Une courbe de sortie posée en plus produirait l'inverse —
    // moins de 20 % de hauteur restante ici — et le test le verrait.
    expect(_hauteur(tester), greaterThan(pleine / 2));
    expect(_hauteur(tester), lessThan(pleine));

    await tester.pumpAndSettle();
    expect(_hauteur(tester), 0);
  });

  testWidgets('animations coupées, la place se libère immédiatement', (
    tester,
  ) async {
    await _monter(tester, _entree, immobile: true);
    expect(_hauteur(tester), greaterThan(0));

    await _monter(tester, null, immobile: true);
    await tester.pump();

    expect(_hauteur(tester), 0);
  });
}
