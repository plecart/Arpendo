import 'package:flutter/material.dart';

import 'l10n/generated/app_localizations.dart';
import 'ui/core/theme/theme.dart';

void main() {
  runApp(const ArpendoApp());
}

/// Racine de l'application.
///
/// Pilotée par l'état (spec UX §2.1) : l'écran affiché dépendra de la séquence
/// de démarrage — contrôle de version, session, partie active. Tant qu'aucune
/// de ces étapes n'existe, elle affiche un écran vide.
///
/// Elle pose ici les jetons de conception du §1, dans les deux modes. Le mode
/// sombre est **disponible, jamais imposé** : `ThemeMode.system` le fait suivre
/// le réglage de l'appareil, et aucun réglage de l'application ne le force.
class ArpendoApp extends StatelessWidget {
  const ArpendoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      // La liste générée porte déjà les trois délégués `Global*Localizations`
      // du SDK, en plus de celui des textes de l'app.
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      // Une seule locale livrée (cadrage §12.6). `fr-XA`, générée à côté pour
      // la vérification de longueur, est une locale de test : les tests la
      // pompent, l'application ne l'offre jamais.
      supportedLocales: const [Locale('fr')],
      theme: themeArpendo(Brightness.light),
      darkTheme: themeArpendo(Brightness.dark),
      themeMode: ThemeMode.system,
      home: const Scaffold(),
    );
  }
}
