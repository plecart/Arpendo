import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/boutons/bouton_pleine_largeur.dart';
import 'package:arpendo/ui/core/marque/bloc_de_marque.dart';
import 'package:arpendo/ui/core/marque/marque_centree.dart';
import 'package:arpendo/ui/core/theme/mesures.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:arpendo/ui/demarrage/ecran_mise_a_jour.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Écran de référence de conception (spec UX §0) : le cas le plus contraint.
///
/// La fenêtre par défaut de `flutter_test` fait 800 × 600 — plus **large** que
/// haute, ce qu'aucun téléphone n'est. Mesurer une mise en page verticale
/// dessus ne dit rien de l'appareil.
const _ecranDeReference = Size(360, 800);

Future<void> _monter(WidgetTester tester, {VoidCallback? onMettreAJour}) {
  tester.view.physicalSize = _ecranDeReference;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  return tester.pumpWidget(
    MaterialApp(
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: themeArpendo(Brightness.light),
      home: EcranMiseAJour(onMettreAJour: onMettreAJour ?? () {}),
    ),
  );
}

void main() {
  testWidgets('le bloc de marque est centré, comme sur l\'attente', (
    tester,
  ) async {
    // Même composant et même mécanique que l'écran d'attente : le bloc est
    // centré et ce qui paraît dessous ne le déplace pas. C'est ce qui évite
    // au logo de sauter au passage attente → bloquant.
    await _monter(tester);

    final bloc = tester.getRect(find.byType(BlocDeMarque));
    // Même référentiel que l'écran d'attente : la zone au-dessus de la bande
    // basse, réservée des deux côtés. C'est ce qui fait que le logo est au
    // **même pixel** sur les deux écrans.
    final ecran = tester.getRect(find.byType(MaterialApp));
    final centreDeLaZone = (ecran.height - MarqueCentree.hauteurBandeBasse) / 2;
    expect(bloc.center.dy, moreOrLessEquals(centreDeLaZone, epsilon: 0.5));
  });

  testWidgets('porte les trois textes du §11.2', (tester) async {
    await _monter(tester);

    expect(find.text('Mise à jour nécessaire'), findsOneWidget);
    expect(
      find.text(
        "Cette version d'Arpendo n'est plus compatible avec le serveur. "
        'Installe la dernière version pour continuer à jouer.',
      ),
      findsOneWidget,
    );
    expect(
      find.textContaining('progression'),
      findsNothing,
      reason:
          'la conservation des données est implicite à toute mise à jour ; '
          "l'écrire attirait l'attention sur un risque qui n'existe pas",
    );
    expect(find.widgetWithText(BoutonPleineLargeur, 'Mettre à jour'), findsOne);
  });

  testWidgets('le bouton déclenche la seule action de l\'écran', (
    tester,
  ) async {
    var ouvertures = 0;
    await _monter(tester, onMettreAJour: () => ouvertures++);

    await tester.tap(find.text('Mettre à jour'));
    await tester.pumpAndSettle();

    expect(ouvertures, 1);
  });

  testWidgets('le message ne recouvre pas le bouton', (tester) async {
    // `MarqueCentree` peint son contenu hors du flux (`heightFactor: 0`) :
    // le framework ne signalera donc **aucun** débordement. Ce garde remplace
    // celui qu'on perd, comme sur l'écran d'attente — et il compte davantage
    // ici, où le contenu est plus haut (titre + corps de deux lignes, et
    // +30 % sous la locale allongée du §0).
    await _monter(tester);

    expect(
      tester.getRect(find.text('Mise à jour nécessaire')).bottom,
      lessThan(tester.getRect(find.byType(BoutonPleineLargeur)).top),
    );
    expect(
      tester
          .getRect(
            find.textContaining(
              "Cette version d'Arpendo n'est plus compatible",
            ),
          )
          .bottom,
      lessThan(tester.getRect(find.byType(BoutonPleineLargeur)).top),
      reason: 'le corps est le plus bas des deux textes, donc le plus exposé',
    );
  });

  testWidgets('le bouton respecte la barre de gestes Android', (tester) async {
    // Même critère que sur l'écran d'attente, et pour la même raison : les
    // deux écrans posent leur seule action en bande basse. Il est inscrit ici
    // aussi pour que la population entière soit gardée, pas seulement le
    // premier écran où le défaut a été mesuré.
    const inset = 48.0;
    // `FakeViewPadding` est en pixels PHYSIQUES : dpr à 1 pour que l'inset
    // simulé vaille 48 dp logiques, comme sur l'appareil.
    tester.view.devicePixelRatio = 1;
    tester.view.padding = const FakeViewPadding(bottom: inset);
    addTearDown(tester.view.reset);
    await _monter(tester);

    final basBouton = tester.getBottomLeft(find.byType(BoutonPleineLargeur)).dy;
    final hauteurEcran = tester.getSize(find.byType(MaterialApp)).height;
    expect(
      hauteurEcran - basBouton,
      greaterThanOrEqualTo(inset + Espacements.x4),
      reason:
          "sous la barre de gestes, la seule action d'un écran sans sortie "
          'serait inatteignable',
    );
  });

  testWidgets("le retour système ne quitte pas l'écran", (tester) async {
    // Le §11.2 dit « pas de bouton retour, pas de fermeture ». Sur Android le
    // chemin qu'on oublie de fermer est le **geste** de retour, que ce montage
    // exerce : l'écran est empilé sur un autre, donc il y a bien où revenir.
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        theme: themeArpendo(Brightness.light),
        home: Builder(
          builder: (context) => TextButton(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (_) => EcranMiseAJour(onMettreAJour: () {}),
              ),
            ),
            child: const Text('ouvrir'),
          ),
        ),
      ),
    );
    await tester.tap(find.text('ouvrir'));
    await tester.pumpAndSettle();
    expect(find.text('Mise à jour nécessaire'), findsOneWidget);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();

    expect(
      find.text('Mise à jour nécessaire'),
      findsOneWidget,
      reason:
          'un client obsolète qui revient en arrière parlerait à une api '
          'qu\'il ne comprend plus (§2.1, §11.2)',
    );
  });
}
