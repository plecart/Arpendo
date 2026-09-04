import 'package:arpendo/domain/bandeau/lignes.dart';
import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/boutons/bouton_pleine_largeur.dart';
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
  testWidgets("l'indicateur est absent à 599 ms et présent à 600 ms", (
    tester,
  ) async {
    await _monter(tester, const Verification());

    await tester.pump(const Duration(milliseconds: 599));
    expect(
      find.byType(CircularProgressIndicator),
      findsNothing,
      reason:
          'en dessous de 600 ms, l\'indicateur clignote et donne une '
          'impression de lenteur là où il n\'y en a pas (§2.1)',
    );

    await tester.pump(const Duration(milliseconds: 1));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('Pret : écran neutre, aucun indicateur même après 600 ms', (
    tester,
  ) async {
    await _monter(tester, const Pret(miseAJourRecommandee: false));

    await tester.pump(const Duration(seconds: 1));

    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.text('Arpendo'), findsOneWidget);
  });

  testWidgets('Injoignable : message, Réessayer, pas d\'indicateur', (
    tester,
  ) async {
    var relances = 0;
    await _monter(tester, const Injoignable(), onReessayer: () => relances++);
    await tester.pump(const Duration(seconds: 1));

    expect(find.text('Le serveur ne répond pas.'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    await tester.tap(find.text('Réessayer'));
    await tester.pumpAndSettle();
    expect(relances, 1);
  });

  testWidgets('revenir en Verification réarme le délai de 600 ms', (
    tester,
  ) async {
    await _monter(tester, const Injoignable());
    await tester.pump(const Duration(seconds: 1));

    await _monter(tester, const Verification());
    await tester.pump(const Duration(milliseconds: 599));
    expect(find.byType(CircularProgressIndicator), findsNothing);
    await tester.pump(const Duration(milliseconds: 1));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
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
    await tester.pump(const Duration(seconds: 1));

    expect(find.byType(BoutonPleineLargeur), findsOneWidget);
  });
}
