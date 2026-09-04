import 'package:arpendo/ui/core/theme/icones.dart';
import 'package:arpendo/ui/core/theme/mesures.dart';
import 'package:arpendo/ui/core/theme/mouvement.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:arpendo/ui/core/theme/typographie.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
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

    for (final brightness in Brightness.values) {
      testWidgets('les créneaux Material rendent les jetons — $brightness', (
        tester,
      ) async {
        final creneaux = await _creneauxSous(tester, brightness);

        for (final (nom, lire, jeton) in _creneauxJetons) {
          expect(
            _geometrie(lire(creneaux)),
            _geometrie(jeton),
            reason:
                'ThemeData fusionne nos créneaux avec la typographie Material 3 : '
                'ce que $nom laisse indéfini vient donc de Material. Lire un style '
                'par le thème et le lire par son jeton doivent donner le même rendu',
          );
        }
      });
    }

    testWidgets('un texte sans style explicite rend le jeton body', (
      tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: themeArpendo(Brightness.light),
          home: const Scaffold(body: Text('12 400')),
        ),
      );

      final rendu = tester
          .renderObject<RenderParagraph>(find.text('12 400'))
          .text
          .style!;

      expect(
        _geometrie(rendu),
        _geometrie(Typographie.body),
        reason:
            'sous Material, un `Text` nu prend `bodyMedium` — 14/20 tant que le '
            "créneau reste vide, hors des huit jetons du §1.2, alors que `type-body` "
            'est la taille plancher de tout texte lisible',
      );
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

  group('thèmes de composant', () {
    for (final brightness in Brightness.values) {
      test('le fond d\'écran hors carte est surface-dim — $brightness', () {
        final theme = themeArpendo(brightness);

        expect(
          theme.scaffoldBackgroundColor,
          theme.colorScheme.surfaceDim,
          reason:
              'le §1.5 réserve `surface` aux modales et feuilles ; un écran '
              'sans carte se pose sur `surface-dim` (report de #34 soldé)',
        );
      });

      test(
        'FilledButton : fond primary au repos, accentPressed à l\'appui — $brightness',
        () {
          final theme = themeArpendo(brightness);
          final style = theme.filledButtonTheme.style!;

          expect(style.backgroundColor!.resolve({}), theme.colorScheme.primary);
          expect(
            style.backgroundColor!.resolve({WidgetState.pressed}),
            _chromeDe(theme).accentPressed,
            reason:
                "l'appui est le jeton `accent-pressed`, dont l'inversion "
                'clair/sombre est déjà encodée — pas un voile Material',
          );
          expect(
            style.overlayColor!.resolve({WidgetState.pressed}),
            Colors.transparent,
            reason:
                'le state layer Material assombrirait par-dessus '
                '`accent-pressed` : le jeton EST déjà l\'état pressé',
          );
        },
      );

      testWidgets(
        'FilledButton désactivé : le thème s\'efface devant Material — $brightness',
        (tester) async {
          final theme = themeArpendo(brightness);
          final style = theme.filledButtonTheme.style!;

          expect(
            style.backgroundColor!.resolve({WidgetState.disabled}),
            isNull,
            reason:
                'la fusion widget ?? thème ?? défaut se fait sur la VALEUR '
                'RÉSOLUE (button_style_button.dart) : une couleur répondue ici '
                'masquerait le défaut Material, et un bouton désactivé '
                'resterait visuellement actif',
          );

          await tester.pumpWidget(
            MaterialApp(
              theme: theme,
              home: const Scaffold(
                body: Center(
                  child: FilledButton(onPressed: null, child: Text('Go')),
                ),
              ),
            ),
          );
          final materiau = tester.widget<Material>(
            find
                .descendant(
                  of: find.byType(FilledButton),
                  matching: find.byType(Material),
                )
                .first,
          );
          // Le défaut est demandé au bouton lui-même plutôt que recopié : le
          // test prouve « le défaut s'applique », pas une valeur interne.
          final bouton = tester.widget<FilledButton>(find.byType(FilledButton));
          final contexte = tester.element(find.byType(FilledButton));
          expect(
            materiau.color,
            bouton.defaultStyleOf(contexte).backgroundColor!.resolve({
              WidgetState.disabled,
            }),
            reason: 'le défaut Material 3 d\'un bouton rempli désactivé',
          );
        },
      );
    }

    testWidgets(
      'FilledButton : le focus et le hover gardent leur state layer',
      (tester) async {
        final theme = themeArpendo(Brightness.light);
        await tester.pumpWidget(
          MaterialApp(
            theme: theme,
            home: Scaffold(
              body: FilledButton(onPressed: () {}, child: const Text('Go')),
            ),
          ),
        );
        final style = theme.filledButtonTheme.style!;
        final bouton = tester.widget<FilledButton>(find.byType(FilledButton));
        final defaut = bouton.defaultStyleOf(
          tester.element(find.byType(FilledButton)),
        );

        for (final etat in [WidgetState.focused, WidgetState.hovered]) {
          expect(
            style.overlayColor!.resolve({etat}),
            isNull,
            reason:
                'un overlay transparent sur TOUS les états éteindrait aussi '
                'l\'anneau de focus (filled_button.dart : « pressed/focused/'
                'hovered highlights are effectively defeated ») — seule la '
                'surbrillance d\'appui est remplacée par `accent-pressed`',
          );
          // Que le thème s'efface ne suffit pas : un défaut qui répondrait
          // `null` à son tour laisserait l'état invisible. On prouve le relais.
          expect(
            defaut.overlayColor!.resolve({etat}),
            isNotNull,
            reason:
                'le défaut Material fournit le state layer que le thème '
                'laisse passer',
          );
        }
      },
    );

    test('FilledButton : hauteur 56 dp et rayon md déclarés par le thème', () {
      final style = themeArpendo(Brightness.light).filledButtonTheme.style!;

      expect(style.minimumSize!.resolve({})!.height, 56);
      expect(
        style.shape!.resolve({}),
        RoundedRectangleBorder(borderRadius: BorderRadius.circular(Rayons.md)),
        reason:
            'vide de spec comblé au brief de #46 : un bouton pleine largeur '
            'est une surface de contenu, pas « rond par nature » (§7.1) — '
            'rayon à confirmer à l\'œil en HITL',
      );
    });

    testWidgets('un FilledButton rend 56 dp de haut sous le thème', (
      tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: themeArpendo(Brightness.light),
          home: Scaffold(
            body: Center(
              child: FilledButton(onPressed: () {}, child: const Text('Go')),
            ),
          ),
        ),
      );

      expect(tester.getSize(find.byType(FilledButton)).height, 56);
    });

    test('TextButton : la cible tactile du §1.4 sur les deux axes', () {
      final style = themeArpendo(Brightness.light).textButtonTheme.style!;

      expect(
        style.minimumSize!.resolve({}),
        const Size.square(CiblesTactiles.min),
        reason:
            'le défaut Material vaut 64 × 40, trop plat ; la contrainte vit '
            'dans le thème pour que les actions du bandeau (§2.4) comme tout '
            'futur bouton texte la reçoivent sans style local',
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

/// Chaque créneau Material que le projet remplit, avec le jeton qu'il doit rendre.
///
/// La table est écrite ici en regard de celle de `Typographie.creneauxMaterial` :
/// c'est leur confrontation qui constitue le test. Les valeurs, elles, ne sont
/// jamais recopiées — seul le jeton fait foi.
final _creneauxJetons = <(String, TextStyle Function(TextTheme), TextStyle)>[
  ('headlineLarge', (t) => t.headlineLarge!, Typographie.display),
  ('headlineSmall', (t) => t.headlineSmall!, Typographie.title),
  ('titleLarge', (t) => t.titleLarge!, Typographie.headline),
  ('bodyLarge', (t) => t.bodyLarge!, Typographie.body),
  ('bodyMedium', (t) => t.bodyMedium!, Typographie.body),
  ('labelLarge', (t) => t.labelLarge!, Typographie.label),
  ('bodySmall', (t) => t.bodySmall!, Typographie.caption),
];

/// Les créneaux typographiques tels que les lit un écran sous le thème.
///
/// `Theme.of(context)` ne rend pas le `textTheme` de `themeArpendo` : `MaterialApp`
/// y fusionne d'abord la géométrie typographique de la locale
/// (`ThemeData.localize`), et c'est cette seconde fusion — invisible sur le
/// `ThemeData` brut — qui décide du rendu. La lire ailleurs que dans un arbre de
/// widgets laisserait passer précisément le défaut que ce test surveille.
Future<TextTheme> _creneauxSous(
  WidgetTester tester,
  Brightness brightness,
) async {
  late TextTheme creneaux;
  await tester.pumpWidget(
    MaterialApp(
      theme: themeArpendo(brightness),
      home: Builder(
        builder: (context) {
          creneaux = Theme.of(context).textTheme;
          return const SizedBox.shrink();
        },
      ),
    ),
  );
  return creneaux;
}

/// La géométrie d'un style — ce que la fusion Material ne doit pas déplacer.
///
/// Elle pose en plus une couleur, une décoration, un `debugLabel` et la famille
/// Roboto, qu'aucun des créneaux confrontés ici ne déclare : ce sont des
/// propriétés héritées légitimement, et comparer les styles entiers échouerait
/// sur elles. Restent les quatre que le §1.2 fixe créneau par créneau, et qui
/// portent l'échelle typographique.
TextStyle _geometrie(TextStyle style) => TextStyle(
  fontSize: style.fontSize,
  height: style.height,
  fontWeight: style.fontWeight,
  letterSpacing: style.letterSpacing,
);

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
