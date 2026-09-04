import 'package:flutter/material.dart';

import '../theme/mesures.dart';
import 'bloc_de_marque.dart';

/// Le bloc de marque **centré**, et sous lui un contenu qui ne le déplace pas.
///
/// C'est la composition des écrans sans carte de la séquence de démarrage —
/// attente (§2.1) et mise à jour obligatoire (§11.2). Elle existe pour tenir
/// **un invariant, pas pour éviter de retaper dix lignes** : le bloc de marque
/// occupe la même place sur tous les écrans qui l'emploient, donc le logo ne
/// saute jamais quand l'un remplace l'autre. Recopié d'écran en écran, cet
/// invariant se perdrait au premier qu'on écrirait un peu différemment.
///
/// **Le mécanisme.** [sous] est peint par un `Align` de `heightFactor: 0` :
/// il ne compte pas dans la hauteur de la colonne, donc le [Center] ne mesure
/// que le bloc. Le mettre dans le flux ferait remonter le logo de la moitié de
/// ce qui paraît — c'est le défaut mesuré à 52 dp sur l'écran d'attente avant
/// la PR #98.
///
/// Ce qui doit vivre **ailleurs qu'ici** : tout ce qui s'ancre à un bord.
/// L'appelant pose son bouton de bande basse dans un `Stack`, à côté de cette
/// composition — un enfant ancré en bas qui traverserait ce widget
/// reprendrait, par sa hauteur, le déplacement qu'il existe pour empêcher.
class MarqueCentree extends StatelessWidget {
  /// Crée la composition ; [sous] est facultatif — sans lui, le bloc est seul.
  const MarqueCentree({this.sous, super.key});

  /// Ce qui s'écrit sous le bloc de marque, séparé de lui par `space-6`.
  final Widget? sous;

  @override
  Widget build(BuildContext context) {
    final debordant = sous;
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const BlocDeMarque(),
          if (debordant != null)
            Align(
              alignment: Alignment.topCenter,
              heightFactor: 0,
              child: Padding(
                padding: const EdgeInsets.only(top: Espacements.x6),
                child: debordant,
              ),
            ),
        ],
      ),
    );
  }
}
