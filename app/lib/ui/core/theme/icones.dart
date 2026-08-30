import 'package:flutter/widgets.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

/// Table sémantique des icônes — spec UX §1.8.
///
/// **Seul fichier du projet à importer `phosphor_icons`.** Les écrans nomment
/// un *usage* (`parametres`, `recentrer`), jamais un glyphe : changer le dessin
/// d'une action se fait ici, en un point, sans toucher un écran.
///
/// Jeu retenu : **Phosphor, graisse `Regular`**, une seule famille et une seule
/// graisse. Le paquet est `phosphor_icons` et non `phosphor_flutter` : ce
/// dernier sous-classe `IconData`, devenu `final class` en Flutter 3.43+, et ne
/// compile plus (spec UX §1.8, archive §18.2). L'identité « Relevé » est portée par le trait — contour d'hexagone
/// de 1 dp, contour de pastille de 1 dp — et Phosphor est un jeu à trait
/// uniforme, donc il parle la même langue que le reste de l'interface.
///
/// Emploi (§1.8) : dessin à **24 dp**, zone tactile à **48 dp** (§1.4). La
/// couleur est **héritée du contexte**, jamais posée en dur. Une icône ne
/// remplace jamais un libellé sur une action nommée ; elle l'accompagne, ou elle
/// est seule là où la convention Android l'autorise — Paramètres, Recentrer.
///
/// N'y figure pas la silhouette d'hexagone de la notification permanente
/// (§10.1) : c'est une ressource Android monochrome livrée avec l'identité, pas
/// un glyphe Phosphor.
abstract final class Icones {
  /// Taille de **dessin** d'une icône, en dp — §1.8.
  ///
  /// À ne pas confondre avec la zone tactile, qui vaut `CiblesTactiles.min`
  /// (`mesures.dart`) et s'étend *autour* du dessin (§1.4).
  static const double taille = 24;

  /// Bandeau, sévérité `info` — §2.4.
  ///
  /// Les trois glyphes de sévérité sont **non substituables** : cercle,
  /// triangle et octogone sont trois *silhouettes* différentes, donc lisibles en
  /// niveaux de gris, à petite taille et pour un daltonien. Remplacer l'un des
  /// trois par une variante de même contour annulerait la règle du §2.4, qui
  /// fait porter la sévérité par la forme et non par la couleur.
  static const IconData severiteInfo = PhosphorIconsRegular.info;

  /// Bandeau, sévérité `avertissement` — triangle, §2.4.
  static const IconData severiteAvertissement = PhosphorIconsRegular.warning;

  /// Bandeau, sévérité `bloquant` — octogone, §2.4.
  static const IconData severiteBloquant = PhosphorIconsRegular.warningOctagon;

  /// Paramètres — §5, §7.4.
  static const IconData parametres = PhosphorIconsRegular.gear;

  /// Recentrer la carte — §7.2.
  static const IconData recentrer = PhosphorIconsRegular.crosshairSimple;

  /// Bouton d'action « Partie » — §7.4.
  static const IconData actionPartie = PhosphorIconsRegular.usersThree;

  /// Delta de score à la hausse — §7.1.
  static const IconData deltaHausse = PhosphorIconsRegular.arrowUp;

  /// Delta de score à la baisse — §7.1.
  ///
  /// Hausse et baisse ont exactement le même traitement : la pastille est neutre
  /// dans les deux sens, et la direction est portée par la flèche et le signe
  /// seuls (§1.5).
  static const IconData deltaBaisse = PhosphorIconsRegular.arrowDown;

  /// Pseudo disponible — §4.1.
  ///
  /// Un état positif se porte par le glyphe et le texte ; là où une couleur est
  /// nécessaire, c'est `accent`, faute de jeton `success` (§1.5).
  static const IconData pseudoDisponible = PhosphorIconsRegular.checkCircle;

  /// Pseudo invalide — §4.1.
  static const IconData pseudoInvalide = PhosphorIconsRegular.xCircle;

  /// Copier le code de partie — §7.4.
  static const IconData copierCode = PhosphorIconsRegular.copy;

  /// Partager — §7.4.
  static const IconData partager = PhosphorIconsRegular.shareNetwork;

  /// Ligne « Permissions » des paramètres — §8.1.
  static const IconData permissions = PhosphorIconsRegular.shieldCheck;

  /// Ligne « Historique des parties » — §8.2.
  static const IconData historiqueParties =
      PhosphorIconsRegular.clockCounterClockwise;

  /// « Se déconnecter de Google » — §8.
  static const IconData seDeconnecter = PhosphorIconsRegular.signOut;
}
