import 'package:flutter/material.dart';

import '../../../domain/bandeau/entree_bandeau.dart';
import '../mise_en_page/apparition_animee.dart';
import '../theme/mouvement.dart';
import 'bandeau.dart';

/// Le créneau **unique** du bandeau — à poser dans le calque `bandeau` (§2.2).
///
/// Il n'y a qu'un emplacement parce qu'il n'y a qu'un bandeau : le §2.4 le pose
/// comme une règle, et le budget vertical du §2.2 en donne la raison — empiler
/// trois bandeaux ramènerait la carte sous 60 % de l'écran, et la carte est le
/// jeu. Ce widget n'a donc **ni file d'attente ni empilement** : on lui donne
/// l'entrée que `resoudre` a choisie, ou rien.
///
/// [entree] à `null` libère la place, et **la carte la reprend
/// progressivement** — jamais un saut (§2.4, « États du composant »). Tout ce
/// qui touche aux durées, aux courbes et au réglage d'accessibilité est délégué
/// à [ApparitionAnimee] : c'est le point unique où le §1.6 s'applique, et il
/// n'a aucune raison d'être réécrit ici.
///
/// Un changement de ligne remplace le contenu sans transition — le §2.4 n'en
/// décrit aucune entre deux bandeaux, et en inventer une ferait clignoter un
/// message que le joueur est en train de lire. Si un fondu devenait
/// souhaitable, la clé à employer serait `entree.priorite` : deux entrées
/// construites depuis la même ligne ne sont pas égales, et comparer les objets
/// rejouerait la transition à chaque reconstruction.
class EmplacementBandeau extends StatelessWidget {
  /// Crée le créneau, portant [entree] ou vide si elle est `null`.
  const EmplacementBandeau({this.entree, super.key});

  /// L'unique entrée à afficher, ou `null` quand aucune condition n'est vraie.
  final EntreeBandeau? entree;

  @override
  Widget build(BuildContext context) {
    final entree = this.entree;
    return ApparitionAnimee(
      jeton: JetonMouvement.base,
      enfant: entree == null ? null : Bandeau(entree: entree),
    );
  }
}
