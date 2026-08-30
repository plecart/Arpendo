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
/// volontaire. [Mouvement.courbeEntree] et [Mouvement.courbeSortie] sont des
/// **miroirs temporels** l'une de l'autre — `easeInCubic(t) = 1 −
/// easeOutCubic(1 − t)`. Jouer la courbe d'entrée à l'envers **produit** donc
/// le mouvement de sortie attendu. Poser `reverseCurve: courbeSortie`
/// appliquerait un second miroir et rendrait la sortie brutale au début puis
/// traînante — exactement ce que le §1.6 refuse. [Mouvement.courbeSortie] ne
/// sert qu'aux animations de sortie jouées **en avant**, jamais à un
/// contrôleur qu'on rembobine.
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
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Les durées se relisent à chaque changement de dépendances : le réglage
    // d'accessibilité peut basculer pendant que l'application tourne, et
    // `Mouvement.of` le suit (§1.6).
    final mouvement = Mouvement.of(context);
    _controleur
      ..duration = mouvement.entree(widget.jeton)
      ..reverseDuration = mouvement.sortie(widget.jeton);
  }

  @override
  void didUpdateWidget(ApparitionAnimee ancien) {
    super.didUpdateWidget(ancien);
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

  @override
  Widget build(BuildContext context) => SizeTransition(
    sizeFactor: _facteur,
    // La place se libère **par le bas** : l'enfant est ancré en haut de son
    // créneau, il ne remonte pas en se rétractant.
    alignment: Alignment.topCenter,
    child: _dernier,
  );
}
