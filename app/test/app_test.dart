import 'package:arpendo/main.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets("l'application démarre sur un écran vide", (tester) async {
    await tester.pumpWidget(const ArpendoApp());

    expect(find.byType(Scaffold), findsOneWidget);
  });

  testWidgets('les couleurs de chrome sont lisibles depuis un écran', (
    tester,
  ) async {
    await tester.pumpWidget(const ArpendoApp());
    final ecran = tester.element(find.byType(Scaffold));

    expect(
      CouleursChrome.of(ecran),
      themeArpendo(Theme.of(ecran).brightness).extension<CouleursChrome>(),
      reason:
          "un écran doit lire les couleurs de chrome du mode appliqué : `of` lève "
          "déjà si l'extension manque, mais rien ne dirait qu'elle vient d'un autre "
          'thème que celui de la racine',
    );
  });

  for (final systeme in Brightness.values) {
    testWidgets('le mode sombre suit le réglage système : $systeme', (
      tester,
    ) async {
      tester.platformDispatcher.platformBrightnessTestValue = systeme;
      addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);

      await tester.pumpWidget(const ArpendoApp());

      expect(
        Theme.of(tester.element(find.byType(Scaffold))).brightness,
        systeme,
        reason:
            'le mode sombre est disponible, jamais imposé : il suit le '
            'réglage système et rien d\'autre',
      );
    });
  }
}
