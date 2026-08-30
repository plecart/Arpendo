import 'package:flutter/material.dart';

import '../theme/mouvement.dart';

/// Fait apparaître et disparaître un enfant **en lui rendant sa place**, aux
/// durées du jeton de mouvement demandé — spec UX §1.6.
///
/// [enfant] à `null` déclenche la disparition ; le widget garde le dernier
/// enfant non nul le temps de l'animation, de sorte qu'un appelant n'a rien à
/// mémoriser et reste sans état.
///
/// Seule la **hauteur** s'anime : c'est la place que le voisin récupère. Aucun
/// fondu n'est appliqué — en ajouter un ferait clignoter un contenu que
/// l'utilisateur est peut-être en train de lire, et aucun § ne le demande.
///
/// ## Pourquoi ce widget existe, et pourquoi pas `AnimatedSize`
///
/// `AnimatedSize` ne joue **jamais** son contrôleur à l'envers — son rendu
/// n'appelle que `forward()` (`rendering/animated_size.dart`). Sa
/// `reverseDuration` est donc inerte, et une disparition dure aussi longtemps
/// qu'une apparition. Le §1.6 exige l'inverse, sans exception : « la sortie
/// dure 75 % de l'entrée », parce qu'un élément qui part aussi lentement qu'il
/// arrive donne l'impression que l'application réfléchit.
///
/// ## Le piège de la courbe, à ne pas « corriger »
///
/// La courbe posée ici est celle d'**entrée**, dans les deux sens, et c'est
/// volontaire. Rembobiner une courbe *ease-out* produit un mouvement *ease-in*
/// — départ lent, fin rapide — c'est-à-dire ce que le §1.6 demande d'une
/// sortie. Poser `reverseCurve:` [Mouvement.courbeSortie] appliquerait un
/// **second** retournement et rendrait la sortie brutale au début puis
/// traînante, l'inverse exact de la consigne. [Mouvement.courbeSortie] ne sert
/// donc qu'aux animations de sortie jouées **en avant**, jamais à un
/// contrôleur qu'on rembobine.
///
/// La correspondance est **approchée, pas exacte**, et il faut le savoir avant
/// de vouloir la rendre exacte. Elle le serait entre les polynômes `t³` et
/// `1 − (1 − t)³` ; les jetons du §1.6 sont les `Curves` de Flutter, des Bézier
/// qui approchent ces polynômes à quelques pour cent près et dont les points de
/// contrôle ne sont pas miroirs — `Cubic(0.55, 0.055, 0.675, 0.19)` contre
/// `Cubic(0.215, 0.61, 0.355, 1.0)`. L'écart entre la sortie jouée ici et une
/// `easeInCubic` jouée en avant culmine à **5 % de la course**, soit moins de
/// 6 dp sur le plus haut bandeau, étalés sur 180 ms — très en deçà de ce que
/// coûterait une seconde mécanique d'animation pour le supprimer.
class ApparitionAnimee extends StatefulWidget {
  /// Anime [enfant] à la cadence de [jeton] ; `null` le fait disparaître.
  const ApparitionAnimee({
    required this.jeton,
    required this.enfant,
    super.key,
  });

  /// Le jeton dont les durées d'entrée et de sortie règlent l'animation.
  final JetonMouvement jeton;

  /// Ce qu'il faut afficher, ou `null` pour libérer la place.
  final Widget? enfant;

  @override
  State<ApparitionAnimee> createState() => _EtatApparitionAnimee();
}

class _EtatApparitionAnimee extends State<ApparitionAnimee>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controleur = AnimationController(
    vsync: this,
    value: widget.enfant == null ? 0 : 1,
  );
  late final CurvedAnimation _facteur = CurvedAnimation(
    parent: _controleur,
    curve: Mouvement.courbeEntree,
  );

  /// Le dernier enfant non nul, gardé le temps de la disparition.
  Widget? _dernier;

  @override
  void initState() {
    super.initState();
    _dernier = widget.enfant;
    _controleur.addStatusListener(_oublierUneFoisParti);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _relireLesDurees();
  }

  @override
  void didUpdateWidget(ApparitionAnimee ancien) {
    super.didUpdateWidget(ancien);
    // Le jeton fait partie de l'état à relire : `didChangeDependencies` ne se
    // déclenche que sur un `InheritedWidget`, jamais sur un paramètre.
    if (widget.jeton != ancien.jeton) _relireLesDurees();
    if (widget.enfant != null) _dernier = widget.enfant;
    final visible = widget.enfant != null;
    if (visible == (ancien.enfant != null)) return;
    visible ? _controleur.forward() : _controleur.reverse();
  }

  @override
  void dispose() {
    _facteur.dispose();
    _controleur.dispose();
    super.dispose();
  }

  /// Recale les durées sur le jeton et sur le réglage d'accessibilité.
  ///
  /// Les deux peuvent changer pendant que l'application tourne — le second par
  /// le système, le premier par un appelant qui change de jeton — et
  /// [Mouvement.of] les suit tous deux (§1.6).
  void _relireLesDurees() {
    final mouvement = Mouvement.of(context);
    _controleur
      ..duration = mouvement.entree(widget.jeton)
      ..reverseDuration = mouvement.sortie(widget.jeton);
  }

  /// Libère le sous-arbre une fois la sortie terminée.
  ///
  /// Sans cela l'enfant congédié resterait **monté** : mis en page, abonné au
  /// `Theme`, au `MediaQuery` et à la localisation, donc reconstruit à chaque
  /// changement de mode ou de locale, et retenant les fermetures de ses
  /// actions. Un bandeau dont le contenu se rafraîchit — le décompte de la
  /// ligne 8, le compte de captures de la ligne 13 — continuerait de vivre
  /// invisible.
  void _oublierUneFoisParti(AnimationStatus etat) {
    if (etat != AnimationStatus.dismissed || _dernier == null) return;
    setState(() => _dernier = null);
  }

  @override
  Widget build(BuildContext context) => SizeTransition(
    sizeFactor: _facteur,
    // La place se libère **par le bas** : l'enfant est ancré en haut de son
    // créneau, il ne remonte pas en se rétractant.
    alignment: Alignment.topCenter,
    child: _dernier,
  );
}
