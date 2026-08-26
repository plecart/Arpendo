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
}
