import 'package:flutter/material.dart';

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
      theme: themeArpendo(Brightness.light),
      darkTheme: themeArpendo(Brightness.dark),
      themeMode: ThemeMode.system,
      home: const Scaffold(),
    );
  }
}
