import 'package:flutter/material.dart';

void main() {
  runApp(const ArpendoApp());
}

/// Racine de l'application.
///
/// Pilotée par l'état (spec UX §2.1) : l'écran affiché dépendra de la séquence
/// de démarrage — contrôle de version, session, partie active. Tant qu'aucune
/// de ces étapes n'existe, elle affiche un écran vide.
class ArpendoApp extends StatelessWidget {
  const ArpendoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(home: Scaffold());
  }
}
