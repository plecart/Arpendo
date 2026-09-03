import 'package:flutter/material.dart';

/// Les jetons de mouvement — spec UX §1.6.
///
/// Chaque valeur ne porte que sa durée d'**entrée** : la sortie s'en déduit
/// ([Mouvement.sortie]), elle n'est jamais saisie deux fois.
///
/// L'énumération est aussi ce qui rend la règle « aucune exception » du §1.6
/// vérifiable : un test parcourt [values] et constate que *tous* les jetons
/// tombent à zéro quand le système coupe les animations. Un jeton ajouté ici
/// plus tard est couvert d'office, sans que personne ait à penser à l'ajouter
/// au test.
enum JetonMouvement {
  /// `motion-press` — retour d'appui sur toute cible tactile.
  ///
  /// Échelle 0,98 plus assombrissement de la surface de 6 %. Aucun changement
  /// d'élévation, aucune ombre, aucun enfoncement visible : l'identité retenue
  /// exclut le relief.
  press(120),

  /// `motion-fast` — apparition d'une pastille.
  fast(120),

  /// `motion-base` — ouverture et fermeture de feuille, bandeau.
  base(240),

  /// `motion-map` — transition de couleur d'un hexagone capturé.
  map(300),

  /// `motion-camera` — recentrage, glissement vers la tuile d'un joueur.
  camera(600),

  /// `motion-stagger` — décalage par ligne à l'arrivée d'une liste (§7.4),
  /// plafonné par [Mouvement.staggerLignesMax].
  ///
  /// Seule son entrée a un emploi : un décalage d'arrivée n'a pas de
  /// contrepartie en sortie. Il figure néanmoins ici, et non à part, pour que
  /// la coupure des animations le concerne comme les autres — c'est le prix de
  /// « aucune exception ».
  stagger(30);

  const JetonMouvement(this._msEntree);

  /// Durée d'entrée du jeton, en millisecondes.
  final int _msEntree;
}

/// Les durées de mouvement telles qu'un contexte donné doit les jouer.
///
/// Point de passage **unique** : les durées ne sont accessibles que par ici,
/// jamais depuis [JetonMouvement] directement. C'est ce qui garantit que le
/// réglage d'accessibilité s'applique partout sans qu'aucun appelant ait à y
/// penser — un joueur qui a demandé zéro mouvement obtient zéro mouvement, y
/// compris sur le vol de caméra du §7.4, qui devient un saut instantané.
///
/// ```dart
/// final mouvement = Mouvement.of(context);
/// AnimatedOpacity(
///   duration: mouvement.entree(JetonMouvement.base),
///   curve: Mouvement.courbeEntree,
///   opacity: visible ? 1 : 0,
///   child: child,
/// );
/// ```
@immutable
class Mouvement {
  const Mouvement._(this._anime);

  /// Faux quand le système demande zéro animation.
  final bool _anime;

  /// Les durées à jouer sous [context], réglage d'accessibilité compris.
  static Mouvement of(BuildContext context) =>
      Mouvement._(!MediaQuery.disableAnimationsOf(context));

  /// Durée d'entrée de [jeton] — `Duration.zero` si les animations sont coupées.
  Duration entree(JetonMouvement jeton) =>
      _anime ? Duration(milliseconds: jeton._msEntree) : Duration.zero;

  /// Durée de sortie de [jeton], soit 75 % de son entrée.
  ///
  /// C'est ce rapport qui fait qu'une interface paraît vive : un élément qui
  /// part aussi lentement qu'il arrive donne l'impression que l'application
  /// réfléchit. Dérivée de [entree], elle tombe donc à zéro avec elle.
  Duration sortie(JetonMouvement jeton) => entree(jeton) * _rapportSortie;

  /// La sortie dure 75 % de l'entrée — §1.6.
  static const double _rapportSortie = 0.75;

  /// Échelle de la cible sous le doigt — `motion-press`, §1.6.
  ///
  /// Une **cible**, pas une durée : la coupure des animations rend le
  /// changement instantané ([entree] tombe à zéro), elle ne le supprime pas —
  /// l'état pressé reste visible, comme l'assombrissement `accent-pressed`.
  /// Elle vit ici et non dans `ButtonStyle`, qui n'a aucune propriété
  /// d'échelle : c'est `BoutonPleineLargeur` qui l'applique.
  static const double echellePression = 0.98;

  /// Courbe d'entrée — un élément entre par l'endroit où il va vivre.
  static const Curve courbeEntree = Curves.easeOutCubic;

  /// Courbe de sortie.
  static const Curve courbeSortie = Curves.easeInCubic;

  /// Nombre de lignes au-delà duquel l'arrivée d'une liste cesse d'être décalée.
  ///
  /// Un compte, pas une durée : la coupure des animations ne le concerne pas —
  /// c'est [JetonMouvement.stagger] qui tombe alors à zéro, et le décalage
  /// disparaît de lui-même.
  static const int staggerLignesMax = 8;
}
