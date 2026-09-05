import 'package:arpendo/domain/bandeau/entree_bandeau.dart';
import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/bandeau/bandeau.dart';
import 'package:arpendo/ui/core/theme/icones.dart';
import 'package:arpendo/ui/core/theme/mesures.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:arpendo/ui/core/theme/typographie.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Écran de référence de conception (spec UX §0) : le cas le plus contraint.
const _ecranDeReference = Size(360, 800);

/// Une entrée dont le test ne fixe que ce qui l'intéresse.
///
/// Le texte est un littéral : ce fichier mesure une **mise en page**, pas la
/// localisation. C'est `fr_xa_test.dart` qui prouve que le bandeau ne rend que
/// des valeurs de l'ARB.
EntreeBandeau _entree({
  Severite severite = Severite.info,
  String texte = 'Court.',
  int actions = 0,
  String? libelle,
}) => EntreeBandeau(
  priorite: 1,
  severite: severite,
  texte: (_) => texte,
  actions: List.generate(
    actions,
    (rang) => ActionBandeau(
      libelle: (_) => libelle ?? 'Action $rang',
      onPressed: () {},
    ),
  ),
);

/// Monte [entree] sur l'écran de référence, dans le thème de l'application.
Future<void> _monter(WidgetTester tester, EntreeBandeau entree) async {
  tester.view.physicalSize = _ecranDeReference;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: themeArpendo(Brightness.light),
      home: Scaffold(
        body: Align(
          alignment: Alignment.topCenter,
          child: Bandeau(entree: entree),
        ),
      ),
    ),
  );
}

/// Les `Material` sous le bandeau — le sien d'abord, ceux de ses boutons
/// ensuite, dans l'ordre de parcours de l'arbre.
final _materiauDuBandeau = find.descendant(
  of: find.byType(Bandeau),
  matching: find.byType(Material),
);

/// La hauteur que le bandeau prend réellement.
double _hauteur(WidgetTester tester) =>
    tester.getSize(find.byType(Bandeau)).height;

/// Le glyphe que le §2.4 attache à chaque sévérité — trois silhouettes.
const _glyphes = {
  Severite.info: Icones.severiteInfo,
  Severite.avertissement: Icones.severiteAvertissement,
  Severite.bloquant: Icones.severiteBloquant,
};

/// La table des couleurs de glyphe du **§1.5**, transcrite depuis la
/// spécification et non depuis le widget : c'est ce qui l'empêche d'être un
/// miroir de l'implémentation, vert quel que soit le choix fait dans le code.
///
/// Les noms de jetons de la spec sont `on-surface-muted`, `warning` et
/// `danger` ; le module de thème les expose sous les rôles ci-dessous.
final _couleursDu15 = <Severite, Color Function(BuildContext)>{
  Severite.info: (contexte) => Theme.of(contexte).colorScheme.onSurfaceVariant,
  Severite.avertissement: (contexte) => CouleursChrome.of(contexte).warning,
  Severite.bloquant: (contexte) => Theme.of(contexte).colorScheme.error,
};

void main() {
  for (final MapEntry(key: severite, value: glyphe) in _glyphes.entries) {
    testWidgets('la sévérité ${severite.name} se lit à sa silhouette', (
      tester,
    ) async {
      await _monter(tester, _entree(severite: severite));

      expect(tester.widget<Icon>(find.byType(Icon)).icon, glyphe);
    });
  }

  for (final MapEntry(key: severite, value: attendue)
      in _couleursDu15.entries) {
    testWidgets('la sévérité ${severite.name} prend la couleur du §1.5', (
      tester,
    ) async {
      await _monter(tester, _entree(severite: severite));

      expect(
        tester.widget<Icon>(find.byType(Icon)).color,
        attendue(tester.element(find.byType(Icon))),
      );
    });
  }

  testWidgets('les trois couleurs de sévérité sont distinctes', (tester) async {
    await _monter(tester, _entree());
    final contexte = tester.element(find.byType(Icon));

    final rendues = _couleursDu15.values.map((lire) => lire(contexte)).toSet();

    expect(rendues, hasLength(_couleursDu15.length));
  });

  testWidgets("l'anatomie du §2.4 est celle de la spécification", (
    tester,
  ) async {
    await _monter(tester, _entree());
    final contexte = tester.element(find.byType(Bandeau));
    final couleurs = Theme.of(contexte).colorScheme;
    // `.first` : le `Material` le plus externe est celui du bandeau. Chaque
    // bouton d'action en construit un autre, plus profond dans l'arbre.
    final materiau = tester.widget<Material>(_materiauDuBandeau.first);

    expect(materiau.color, couleurs.surface, reason: 'fond opaque');
    expect(materiau.elevation, Elevations.e1);
    expect(
      materiau.shape,
      RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(Rayons.md),
        // Le contour du §1.3 : sans lui, un bandeau clair disparaît sur un
        // hexagone clair, et l'ombre portée n'y suffit pas. Sa largeur de
        // **1 dp** est écrite ici parce qu'elle vient de la spécification ;
        // que ce soit aussi le défaut du SDK est une coïncidence, et le jour
        // où ce défaut changerait, ce test le dirait.
        side: BorderSide(color: couleurs.outline, width: 1),
      ),
    );
  });

  testWidgets('le bandeau laisse une marge d\'écran de chaque côté', (
    tester,
  ) async {
    await _monter(tester, _entree());

    // Une largeur, donc mesurée sur la **géométrie du conteneur** et non sur
    // du texte : la police de `flutter_test` fausse la mesure d'un glyphe,
    // jamais celle d'un rembourrage.
    final materiau = tester.getRect(_materiauDuBandeau.first);

    expect(materiau.left, Espacements.x4);
    expect(_ecranDeReference.width - materiau.right, Espacements.x4);
  });

  testWidgets('la cible tactile des actions vient du thème, sans style local', (
    tester,
  ) async {
    await _monter(tester, _entree(actions: 1));

    expect(
      tester.widget<TextButton>(find.byType(TextButton)).style,
      isNull,
      reason:
          'un style de widget l\'emporte sur le thème : un `minimumSize` '
          'local rendrait le `TextButtonThemeData` de #46 sans effet sur le '
          'composant pour lequel il est écrit, et le défaut serait invisible',
    );
    // La **contrainte déclarée**, pas la géométrie : une largeur rendue sous
    // la police de test ne dit rien de la largeur réelle.
    final theme = Theme.of(tester.element(find.byType(TextButton)));
    expect(
      theme.textButtonTheme.style!.minimumSize!.resolve({}),
      const Size.square(CiblesTactiles.min),
    );
  });

  testWidgets('le glyphe est dessiné à la taille du §1.8', (tester) async {
    await _monter(tester, _entree());

    expect(tester.getSize(find.byType(Icon)).height, Icones.taille);
  });

  testWidgets('une ligne sans action mesure 56 dp', (tester) async {
    await _monter(tester, _entree());

    expect(_hauteur(tester), 56);
  });

  testWidgets('une seconde ligne ajoute exactement une ligne de type-body', (
    tester,
  ) async {
    // Le saut de ligne explicite plutôt qu'un texte assez long pour déborder :
    // le nombre de lignes ne dépend alors ni des métriques de la police ni de
    // la largeur, et le test mesure ce qu'il prétend mesurer.
    await _monter(tester, _entree(texte: 'Première ligne\nseconde ligne'));

    expect(_hauteur(tester), 80);
  });

  group('message tapable (§2.4)', () {
    EntreeBandeau lien(void Function() onTape) => EntreeBandeau(
      priorite: 1,
      severite: Severite.info,
      texte: (_) => 'Court.',
      onTexteTape: onTape,
    );

    testWidgets('taper le bandeau déclenche le geste du message', (
      tester,
    ) async {
      var tapes = 0;
      await _monter(tester, lien(() => tapes++));

      // La cible est le **bandeau entier** (56 dp), pas la ligne de texte
      // (24 dp) : c'est ce qui satisfait les 48 dp du §1.4 sans hauteur en
      // plus. Le tap porte donc n'importe où sur la surface.
      await tester.tap(find.byType(Bandeau));
      await tester.pumpAndSettle();

      expect(tapes, 1);
    });

    testWidgets('le message tapable est en graisse 500, sans virer de couleur', (
      tester,
    ) async {
      await _monter(tester, lien(() {}));
      final contexte = tester.element(find.byType(Bandeau));

      final style = tester.widget<Text>(find.text('Court.')).style!;

      expect(style.fontWeight, FontWeight.w500);
      expect(
        style.color,
        Theme.of(contexte).colorScheme.onSurface,
        reason:
            'le §1.5 interdit de porter une information par la couleur seule ; '
            'la graisse est le signal, le lien ne vire pas à l\'accent',
      );
    });

    testWidgets('un message sans geste garde la graisse du corps', (
      tester,
    ) async {
      await _monter(tester, _entree());

      expect(
        tester.widget<Text>(find.text('Court.')).style!.fontWeight,
        // Comparée au **jeton**, pas à une constante recopiée : c'est le §1.2
        // qui fixe la graisse du corps, et le test doit suivre s'il change.
        Typographie.body.fontWeight,
        reason: 'sinon toutes les lignes auraient l\'air cliquables',
      );
    });

    testWidgets('la cible tactile atteint les 48 dp du §1.4', (tester) async {
      await _monter(tester, lien(() {}));

      expect(
        tester.getSize(find.byType(Bandeau)).height,
        greaterThanOrEqualTo(CiblesTactiles.min),
      );
    });
  });

  testWidgets('une action unique partage la rangée du message', (tester) async {
    await _monter(tester, _entree(actions: 1));

    // Sur la même rangée : le bouton commence avant que l'icône ne finisse.
    expect(
      tester.getTopLeft(find.byType(TextButton)).dy,
      lessThan(tester.getBottomLeft(find.byType(Icon)).dy),
    );
    // La cible tactile du §1.4 est un **plancher**, pas une égalité : le
    // bouton grandit quand son libellé se replie, ce qui est précisément ce
    // qui lui permet de tenir sans déborder (§0).
    expect(
      tester.getSize(find.byType(TextButton)).height,
      greaterThanOrEqualTo(CiblesTactiles.min),
    );
  });

  testWidgets('l\'action partagée ne déborde jamais de la rangée', (
    tester,
  ) async {
    // Le cas qui a fait rougir le garde `fr-XA` : un libellé long ne peut pas
    // pousser le bandeau hors de l'écran. Mesuré ici sur un libellé
    // volontairement démesuré, pour que le garde tienne sans dépendre de la
    // locale allongée.
    await _monter(
      tester,
      _entree(actions: 1, libelle: 'Un libellé d\'action anormalement long'),
    );

    expect(
      tester.getBottomRight(find.byType(TextButton)).dx,
      lessThanOrEqualTo(tester.getSize(find.byType(Bandeau)).width),
    );
  });

  testWidgets('deux actions descendent sur une seconde rangée', (tester) async {
    await _monter(tester, _entree(actions: 2));

    // 16 + 24 (une ligne) + 8 (écart) + 48 (cible tactile) + 16.
    expect(_hauteur(tester), 112);
    // La seconde rangée existe pour que le message garde toute la largeur :
    // sur l'écran de référence, **deux** libellés longs et un message ne
    // tiennent pas côte à côte, et le garde `fr-XA` les allonge de 30 %. Un
    // libellé seul, lui, y tient — d'où la règle à deux cas.
    expect(
      tester.getTopLeft(find.byType(TextButton).first).dy,
      greaterThan(tester.getBottomLeft(find.byType(Icon)).dy),
    );
  });

  for (final nombre in [0, 1, 2]) {
    testWidgets('$nombre action(s) : autant de boutons rendus', (tester) async {
      await _monter(tester, _entree(actions: nombre));

      expect(find.byType(TextButton), findsNWidgets(nombre));
    });
  }
}
