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
/// il ne compte pas dans la hauteur de la colonne, donc le centrage ne voit
/// que le bloc. Le mettre dans le flux ferait remonter le logo de la moitié de
/// ce qui paraît — c'est le défaut mesuré à 52 dp sur l'écran d'attente avant
/// la PR #98.
///
/// **La bande basse est toujours réservée**, que [bandeBasse] la remplisse ou
/// non, et le bloc se centre dans ce qui reste. Les deux raisons sont
/// indissociables : réserver **toujours** est ce qui empêche le bloc de bouger
/// quand un bouton apparaît ou disparaît d'un état à l'autre ; réserver **tout
/// court** est ce qui empêche [sous] de venir recouvrir ce bouton — mesuré à
/// 31 dp de recouvrement sur l'écran de référence 360 × 800 avant cette
/// réservation. Comme [sous] est hors du flux, aucun défilement ne peut le
/// sauver : c'est la place qu'on lui laisse, ou rien.
///
/// **Ce qu'elle ne couvre pas**, faute d'un mécanisme qui le puisse ici : un
/// réglage système de taille de police très élevé (§1.2 en admet jusqu'à
/// 200 %) finit par ramener le recouvrement. Les écrans qui l'emploient
/// gardent donc chacun un test de non-recouvrement — c'est lui qui le dira.
class MarqueCentree extends StatelessWidget {
  /// Crée la composition. [sous] et [bandeBasse] sont facultatifs ; la place
  /// de la seconde est réservée même quand elle est absente.
  const MarqueCentree({this.sous, this.bandeBasse, super.key});

  /// Ce qui s'écrit sous le bloc de marque, séparé de lui par `space-6`.
  final Widget? sous;

  /// L'action de bande basse — un bouton pleine largeur, ou `null`.
  final Widget? bandeBasse;

  /// La hauteur réservée en bas, remplie ou non : le bouton et sa marge.
  static const hauteurBandeBasse =
      CiblesTactiles.boutonPrincipal + Espacements.x6;

  @override
  Widget build(BuildContext context) {
    final debordant = sous;
    final bande = bandeBasse;
    return Stack(
      children: [
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          bottom: hauteurBandeBasse,
          child: Center(
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
          ),
        ),
        if (bande != null)
          Positioned(left: 0, right: 0, bottom: Espacements.x6, child: bande),
      ],
    );
  }
}
