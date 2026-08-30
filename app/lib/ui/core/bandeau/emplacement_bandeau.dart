import 'package:flutter/material.dart';

import '../../../domain/bandeau/entree_bandeau.dart';
import '../mise_en_page/pile_de_calques.dart';
import '../theme/mouvement.dart';
import 'bandeau.dart';

/// Le créneau **unique** du bandeau, sous le header — [Calque.bandeau], §2.2.
///
/// Il n'y a qu'un emplacement parce qu'il n'y a qu'un bandeau : le §2.4 le pose
/// comme une règle, et le budget vertical du §2.2 en donne la raison — empiler
/// trois bandeaux ramènerait la carte sous 60 % de l'écran, et la carte est le
/// jeu. Ce widget n'a donc **ni file d'attente ni empilement** : on lui donne
/// l'entrée que `resoudre` a choisie, ou rien.
///
/// [entree] à `null` libère la place, et **la carte la reprend
/// progressivement** — `motion-base` en sortie, jamais un saut (§2.4, « États
/// du composant »). La durée passe par [Mouvement.of], donc un joueur qui a
/// demandé zéro animation obtient une disparition instantanée, sans que ce
/// widget ait à le savoir (§1.6).
///
/// Seule la **hauteur** s'anime : c'est elle que la carte récupère. Un
/// changement de ligne remplace le contenu sans fondu — le §2.4 ne décrit
/// aucune transition entre deux bandeaux, et en inventer une ferait clignoter
/// un message que le joueur est en train de lire. Si un fondu devenait
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
    final mouvement = Mouvement.of(context);
    final entree = this.entree;
    final contenu = entree == null
        ? const SizedBox(width: double.infinity)
        : Bandeau(entree: entree);

    final entreeDuree = mouvement.entree(JetonMouvement.base);
    // Animations coupées : on ne monte **aucun** animateur, plutôt qu'un
    // animateur de durée nulle. `AnimatedSize` ne supporte pas
    // `Duration.zero` — son contrôleur se termine pendant la mise en page et
    // le framework lève « A RenderAnimatedSize was mutated in its own
    // performLayout implementation ». Le résultat visé est de toute façon
    // celui-ci : le changement est immédiat (§1.6).
    if (entreeDuree == Duration.zero) return contenu;

    return AnimatedSize(
      duration: entreeDuree,
      reverseDuration: mouvement.sortie(JetonMouvement.base),
      curve: Mouvement.courbeEntree,
      // La place se libère **par le bas** : le bandeau est ancré sous le
      // header, il ne remonte pas en se rétractant.
      alignment: Alignment.topCenter,
      child: contenu,
    );
  }
}
