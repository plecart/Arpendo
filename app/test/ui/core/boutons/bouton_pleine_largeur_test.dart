import 'package:arpendo/ui/core/boutons/bouton_pleine_largeur.dart';
import 'package:arpendo/ui/core/theme/mouvement.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('le bouton occupe toute la largeur disponible', (tester) async {
    await _monter(tester);

    expect(
      tester.getSize(find.byType(FilledButton)).width,
      tester.getSize(find.byType(Scaffold)).width,
      reason:
          'la pleine largeur est la responsabilité du widget, pas de chaque '
          'écran qui le pose (§4, §11.2)',
    );
  });

  testWidgets("l'appui ramène l'échelle à 0,98, le relâcher la rend", (
    tester,
  ) async {
    await _monter(tester);
    final gesture = await tester.startGesture(
      tester.getCenter(find.byType(FilledButton)),
    );
    await tester.pumpAndSettle();

    expect(_echelle(tester).scale, Mouvement.echellePression);

    await gesture.up();
    await tester.pumpAndSettle();

    expect(_echelle(tester).scale, 1.0);
  });

  testWidgets(
    "l'appui joue l'entrée de motion-press, le relâcher joue sa sortie",
    (tester) async {
      await _monter(tester);
      final mouvement = await _mouvement(tester);
      final gesture = await tester.startGesture(
        tester.getCenter(find.byType(FilledButton)),
      );
      await tester.pump();

      expect(_echelle(tester).duration, mouvement.entree(JetonMouvement.press));
      expect(_echelle(tester).curve, Mouvement.courbeEntree);

      await gesture.up();
      await tester.pumpAndSettle();

      expect(
        _echelle(tester).duration,
        mouvement.sortie(JetonMouvement.press),
        reason:
            "la sortie dure 75 % de l'entrée (§1.6) — un relâcher aussi lent "
            "que l'appui donne l'impression que l'application réfléchit",
      );
      expect(_echelle(tester).curve, Mouvement.courbeSortie);
    },
  );

  testWidgets('un tap déclenche onPressed une fois', (tester) async {
    var appuis = 0;
    await _monter(tester, onPressed: () => appuis++);

    await tester.tap(find.byType(FilledButton));
    await tester.pumpAndSettle();

    expect(appuis, 1);
  });

  testWidgets('le libellé est rendu tel quel', (tester) async {
    await _monter(tester);

    expect(find.text('Continuer'), findsOneWidget);
  });

  testWidgets('onPressed nul désactive le bouton', (tester) async {
    await _monter(tester, actif: false);

    expect(
      tester.widget<FilledButton>(find.byType(FilledButton)).enabled,
      isFalse,
    );
  });
}

/// Monte le bouton sous le thème de l'app, comme tout écran le fera.
Future<void> _monter(
  WidgetTester tester, {
  VoidCallback? onPressed,
  bool actif = true,
}) {
  return tester.pumpWidget(
    MaterialApp(
      theme: themeArpendo(Brightness.light),
      home: Scaffold(
        body: BoutonPleineLargeur(
          libelle: 'Continuer',
          onPressed: actif ? (onPressed ?? () {}) : null,
        ),
      ),
    ),
  );
}

/// Le `AnimatedScale` que le bouton pilote — sa cible déclarée, pas un rendu.
AnimatedScale _echelle(WidgetTester tester) =>
    tester.widget<AnimatedScale>(find.byType(AnimatedScale));

/// Les jetons de mouvement tels que le bouton monté les lit.
Future<Mouvement> _mouvement(WidgetTester tester) async =>
    Mouvement.of(tester.element(find.byType(FilledButton)));
