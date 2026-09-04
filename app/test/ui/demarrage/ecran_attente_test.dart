import 'package:arpendo/domain/bandeau/lignes.dart';
import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/boutons/bouton_pleine_largeur.dart';
import 'package:arpendo/ui/core/marque/bloc_de_marque.dart';
import 'package:arpendo/ui/core/marque/marque_centree.dart';
import 'package:arpendo/ui/core/theme/mesures.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:arpendo/ui/demarrage/ecran_attente.dart';
import 'package:arpendo/ui/demarrage/etat_demarrage.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> _monter(
  WidgetTester tester,
  EtatDemarrage etat, {
  bool avecBandeau = false,
  VoidCallback? onReessayer,
}) {
  return tester.pumpWidget(
    MaterialApp(
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: themeArpendo(Brightness.light),
      home: EcranAttente(
        etat: etat,
        entreeBandeau: avecBandeau ? ligneReseauAbsent() : null,
        onReessayer: onReessayer ?? () {},
      ),
    ),
  );
}

void main() {
  testWidgets(
    'le bloc de marque occupe la même position dans les trois états',
    (tester) async {
      // L'invariant du §2.1 : ce qui paraît sous le bloc — message, bouton —
      // prend sa place SANS le déplacer. Le défaut corrigé ici valait 52 dp de
      // dérive entre l'attente et l'échec.
      final positions = <String, Rect>{};
      for (final (nom, etat) in const <(String, EtatDemarrage)>[
        ('Verification', Verification()),
        ('Pret', Pret(miseAJourRecommandee: false)),
        ('Injoignable', Injoignable()),
      ]) {
        await _monter(tester, etat);
        positions[nom] = tester.getRect(find.byType(BlocDeMarque));
      }

      expect(
        positions.values.toSet(),
        hasLength(1),
        reason:
            'un logo qui remonte à chaque changement d\'état se lit comme une '
            'instabilité de l\'application (§2.1) — mesuré : $positions',
      );
    },
  );

  testWidgets('le bloc de marque est centré au-dessus de la bande basse', (
    tester,
  ) async {
    await _monter(tester, const Injoignable());

    final bloc = tester.getRect(find.byType(BlocDeMarque));
    // Centré dans **ce qui reste au-dessus de la bande basse**, et non sur la
    // hauteur totale : c'est cette réservation constante qui empêche à la fois
    // le bloc de bouger d'un état à l'autre et le contenu de recouvrir le
    // bouton (§2.1, §11.2). Un demi-pixel de tolérance : un bloc de hauteur
    // impaire ne peut pas tomber sur un centre entier.
    final ecran = tester.getRect(find.byType(MaterialApp));
    final centreDeLaZone = (ecran.height - MarqueCentree.hauteurBandeBasse) / 2;
    expect(
      bloc.center.dy,
      moreOrLessEquals(centreDeLaZone, epsilon: 0.5),
      reason:
          'le §2.1 centre le bloc dans la zone utile, et non en bande haute '
          'comme au §4 : cet écran n\'a pas de contenu à dégager en haut',
    );
  });

  testWidgets('aucun indicateur de progression, quel que soit l\'état', (
    tester,
  ) async {
    // Le bloc de marque tient ce rôle, et le délai du client HTTP borne
    // l'attente (§2.1, §13.2). Garde de non-régression de la décision.
    for (final etat in const <EtatDemarrage>[
      Verification(),
      Pret(miseAJourRecommandee: false),
      MiseAJourRequise(),
      Injoignable(),
    ]) {
      await _monter(tester, etat);
      await tester.pump(const Duration(seconds: 10));
      expect(
        // `bySubtype` et non `byType` : ce dernier compare le type exact et
        // laisserait passer n'importe quelle sous-classe de `ProgressIndicator`.
        find.bySubtype<ProgressIndicator>(),
        findsNothing,
        reason: 'état $etat',
      );
    }
    expect(find.text('Arpendo'), findsOneWidget);
  });

  testWidgets('Injoignable : message et Réessayer, qui relance', (
    tester,
  ) async {
    var relances = 0;
    await _monter(tester, const Injoignable(), onReessayer: () => relances++);

    expect(find.text('Le serveur ne répond pas.'), findsOneWidget);
    // La zone d'état est peinte hors du flux (`heightFactor: 0`), donc aucun
    // débordement ne sera plus signalé par le framework : ce garde remplace
    // celui qu'on perd en sortant du flux.
    expect(
      tester.getRect(find.text('Le serveur ne répond pas.')).bottom,
      lessThan(tester.getRect(find.byType(BoutonPleineLargeur)).top),
      reason: 'le message ne doit pas recouvrir la seule action de l\'écran',
    );

    await tester.tap(find.text('Réessayer'));
    await tester.pumpAndSettle();
    expect(relances, 1);
  });

  testWidgets('une entrée de bandeau est rendue sur son calque', (
    tester,
  ) async {
    await _monter(tester, const Verification(), avecBandeau: true);
    await tester.pumpAndSettle();

    expect(
      find.text('Pas de réseau. La reprise est automatique.'),
      findsOneWidget,
    );
  });

  testWidgets('le bouton Réessayer est le bouton pleine largeur du §4', (
    tester,
  ) async {
    await _monter(tester, const Injoignable());

    expect(find.byType(BoutonPleineLargeur), findsOneWidget);
  });

  testWidgets('le bouton Réessayer respecte la barre de gestes Android', (
    tester,
  ) async {
    // 48 dp d'inset bas — la navigation gestuelle. L'exemption de safe area
    // du calque `carte` (§2.3) vaut pour une carte qui court sous l'encoche,
    // jamais pour un contrôle : un bouton collé au bord entre en conflit
    // avec les gestes système (§1.4, marge de bord 16 dp minimum).
    const inset = 48.0;
    // `FakeViewPadding` est en pixels PHYSIQUES : dpr à 1 pour que l'inset
    // simulé vaille 48 dp logiques, comme sur l'appareil.
    tester.view.devicePixelRatio = 1;
    tester.view.padding = const FakeViewPadding(bottom: inset);
    addTearDown(tester.view.reset);
    await _monter(tester, const Injoignable());

    final basBouton = tester.getBottomLeft(find.byType(BoutonPleineLargeur)).dy;
    final hauteurEcran = tester.getSize(find.byType(MaterialApp)).height;
    expect(
      hauteurEcran - basBouton,
      greaterThanOrEqualTo(inset + Espacements.x4),
      reason:
          'sous la barre de gestes, la seule action de l\'écran de panne '
          'serait inatteignable',
    );
  });
}
