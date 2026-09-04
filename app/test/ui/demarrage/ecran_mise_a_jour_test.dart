import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/boutons/bouton_pleine_largeur.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:arpendo/ui/demarrage/ecran_mise_a_jour.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> _monter(WidgetTester tester, {VoidCallback? onMettreAJour}) {
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
  testWidgets('porte les quatre textes du §11.2', (tester) async {
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
      find.text('Ta partie et ta progression sont conservées.'),
      findsOneWidget,
      reason: 'sans elle le joueur croit tout perdre et hésite (§11.2)',
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
