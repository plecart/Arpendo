import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:arpendo/ui/core/theme/typographie.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('typographie', () {
    test("la variante tabulaire pose les chiffres à chasse fixe et ne touche à rien d'autre", () {
      const base = Typographie.display;

      final tabulaire = base.tabulaire;

      expect(
        tabulaire.fontFeatures,
        contains(const FontFeature.tabularFigures()),
      );
      expect(
        base.fontFeatures,
        isNull,
        reason: 'le style de base reste sans variante',
      );
      expect(tabulaire.fontSize, base.fontSize);
      expect(tabulaire.fontWeight, base.fontWeight);
      expect(tabulaire.height, base.height);
    });
  });

  group('couleurs de chrome', () {
    test("l'état pressé fonce en mode clair et éclaircit en mode sombre", () {
      final clair = themeArpendo(Brightness.light);
      final sombre = themeArpendo(Brightness.dark);

      expect(
        _chromeDe(clair).accentPressed.computeLuminance(),
        lessThan(clair.colorScheme.primary.computeLuminance()),
        reason: "en clair, l'appui fonce l'accent",
      );
      expect(
        _chromeDe(sombre).accentPressed.computeLuminance(),
        greaterThan(sombre.colorScheme.primary.computeLuminance()),
        reason:
            "en sombre, l'appui éclaircit l'accent : le foncer ferait "
            'retomber un accent pâle dans la bande de clarté des couleurs joueur',
      );
    });
  });
}

/// Les couleurs de chrome d'un thème, sans passer par un arbre de widgets.
CouleursChrome _chromeDe(ThemeData theme) => theme.extension<CouleursChrome>()!;
