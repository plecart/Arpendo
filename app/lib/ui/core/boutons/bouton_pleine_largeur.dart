import 'package:flutter/material.dart';

import '../theme/mouvement.dart';

/// Le bouton principal des écrans sans carte — 56 dp, pleine largeur (§4, §11.2).
///
/// Un `FilledButton` qui prend toute la largeur disponible et porte le retour
/// d'appui `motion-press` du §1.6 : échelle [Mouvement.echellePression] à
/// l'entrée du doigt, retour à 1 au relâcher, durées et courbes des jetons.
/// L'assombrissement de surface, lui, vient du `FilledButtonThemeData`
/// (`accent-pressed`) — ce widget n'ajoute que ce que `ButtonStyle` ne sait
/// pas faire : `ButtonStyle` n'a aucune propriété d'échelle, et ses
/// `ButtonLayerBuilder` sont clippés par la forme du `Material`
/// (SDK 3.47.1, `button_style.dart`).
///
/// La pleine largeur est la responsabilité du widget, pas de chaque écran qui
/// le pose : les marges d'écran (`space-4`) restent à l'appelant.
class BoutonPleineLargeur extends StatefulWidget {
  /// Crée le bouton portant [libelle], déclenchant [onPressed] au tap.
  const BoutonPleineLargeur({
    required this.libelle,
    required this.onPressed,
    super.key,
  });

  /// Le texte du bouton — une valeur d'ARB entière, jamais une composition
  /// (garde `fr-XA`).
  final String libelle;

  /// L'action du tap ; `null` désactive le bouton, rendu par le thème.
  final VoidCallback? onPressed;

  @override
  State<BoutonPleineLargeur> createState() => _BoutonPleineLargeurState();
}

class _BoutonPleineLargeurState extends State<BoutonPleineLargeur> {
  /// Les états du bouton, écoutés pour connaître l'appui.
  ///
  /// C'est le `FilledButton` qui décide de son état pressé — appui, relâcher,
  /// annulation par glissement — et ce widget s'y abonne, plutôt que de
  /// dupliquer cette logique avec un `Listener` qui divergerait sur les cas
  /// limites.
  final WidgetStatesController _etats = WidgetStatesController();

  bool _presse = false;

  @override
  void initState() {
    super.initState();
    _etats.addListener(_surChangementDEtats);
  }

  @override
  void dispose() {
    _etats.dispose();
    super.dispose();
  }

  void _surChangementDEtats() {
    final presse = _etats.value.contains(WidgetState.pressed);
    if (presse != _presse) {
      setState(() => _presse = presse);
    }
  }

  @override
  Widget build(BuildContext context) {
    final mouvement = Mouvement.of(context);
    return AnimatedScale(
      scale: _presse ? Mouvement.echellePression : 1.0,
      // Chaque changement de cible est une animation vers l'avant : l'appui
      // joue l'entrée du jeton, le relâcher joue sa sortie — jamais un
      // rembobinage, dont la courbe produirait l'effet inverse.
      duration: _presse
          ? mouvement.entree(JetonMouvement.press)
          : mouvement.sortie(JetonMouvement.press),
      curve: _presse ? Mouvement.courbeEntree : Mouvement.courbeSortie,
      child: SizedBox(
        width: double.infinity,
        child: FilledButton(
          statesController: _etats,
          onPressed: widget.onPressed,
          child: Text(widget.libelle),
        ),
      ),
    );
  }
}
