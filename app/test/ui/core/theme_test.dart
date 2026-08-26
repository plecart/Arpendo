import 'package:arpendo/ui/core/theme/icones.dart';
import 'package:arpendo/ui/core/theme/mouvement.dart';
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

    test('deux appels rendent un thème égal', () {
      expect(
        themeArpendo(Brightness.light),
        themeArpendo(Brightness.light),
        reason:
            'ThemeData compare ses extensions par == ; deux thèmes inégaux '
            "font notifier l'InheritedWidget Theme et reconstruire tout ce qui "
            'en dépend, pour rien',
      );
    });
  });

  group('mouvement', () {
    testWidgets('la sortie de chaque jeton vaut 75 % de son entrée', (
      tester,
    ) async {
      final mouvement = await _mouvementSous(tester, animationsCoupees: false);

      for (final jeton in JetonMouvement.values) {
        expect(
          mouvement.entree(jeton),
          greaterThan(Duration.zero),
          reason: '$jeton doit durer, sans quoi le rapport ne prouve rien',
        );
        expect(
          mouvement.sortie(jeton),
          mouvement.entree(jeton) * 0.75,
          reason:
              "$jeton : un élément qui part aussi lentement qu'il arrive donne "
              "l'impression que l'application réfléchit",
        );
      }
    });

    testWidgets('MediaQuery.disableAnimations ramène chaque jeton à 0 ms', (
      tester,
    ) async {
      final mouvement = await _mouvementSous(tester, animationsCoupees: true);

      for (final jeton in JetonMouvement.values) {
        expect(mouvement.entree(jeton), Duration.zero, reason: '$jeton');
        expect(mouvement.sortie(jeton), Duration.zero, reason: '$jeton');
      }
    });
  });

  group('icônes', () {
    // Ce test référence [Icones], et c'est là son second rôle : sans un point
    // d'appel atteignable, `icones.dart` n'est compilé par rien — ni par
    // `flutter analyze`, qui ignore les sources d'un paquet tiers, ni par le
    // build, qui ne compile pas une bibliothèque hors du graphe de `main()`.
    // Une table de constantes que personne n'importe laisse passer un paquet
    // cassé au vert. Ne pas le supprimer sans le remplacer.
    test('les trois glyphes de sévérité sont trois silhouettes distinctes', () {
      final severites = <IconData>{
        Icones.severiteInfo,
        Icones.severiteAvertissement,
        Icones.severiteBloquant,
      };

      expect(
        severites,
        hasLength(3),
        reason:
            'cercle, triangle et octogone sont non substituables : la '
            'sévérité se lit à la forme, donc en niveaux de gris et pour un '
            'daltonien (§2.4). Deux glyphes identiques annuleraient la règle',
      );
    });
  });
}

/// Les couleurs de chrome d'un thème, sans passer par un arbre de widgets.
CouleursChrome _chromeDe(ThemeData theme) => theme.extension<CouleursChrome>()!;

/// Les jetons de mouvement tels que les lit un contexte donné.
Future<Mouvement> _mouvementSous(
  WidgetTester tester, {
  required bool animationsCoupees,
}) async {
  late Mouvement mouvement;
  await tester.pumpWidget(
    MediaQuery(
      data: MediaQueryData(disableAnimations: animationsCoupees),
      child: Builder(
        builder: (context) {
          mouvement = Mouvement.of(context);
          return const SizedBox.shrink();
        },
      ),
    ),
  );
  return mouvement;
}
