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

  testWidgets('la place se libère progressivement, jamais par un saut', (
    tester,
  ) async {
    await _monter(tester, _entree);
    final pleine = _hauteur(tester);
    expect(pleine, greaterThan(0));
    // La durée se lit par le point de passage obligé du §1.6, jamais en clair :
    // un test qui recopierait 180 ms cesserait de mesurer le jour où le jeton
    // change, au lieu de rougir.
    final sortie = Mouvement.of(tester.element(find.byType(EmplacementBandeau)))
        .sortie(JetonMouvement.base);

    await _monter(tester, null);
    await tester.pump();
    // À mi-parcours de la sortie, la carte a repris une part de la place, mais
    // pas toute : c'est exactement ce que « jamais un saut » veut dire, et ce
    // qu'une disparition instantanée échouerait à faire.
    await tester.pump(sortie ~/ 2);

    expect(_hauteur(tester), greaterThan(0));
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
