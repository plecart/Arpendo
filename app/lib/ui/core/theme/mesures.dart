/// Mesures du socle de conception — espacements (spec UX §1.1), rayons et
/// élévations (§1.3).
///
/// Ce sont les seules familles de jetons qui ne dépendent ni du mode clair /
/// sombre ni d'un `BuildContext` : des longueurs en dp, identiques partout.
/// Elles s'écrivent donc en constantes, sans passer par `ThemeData`.
///
/// La spécification fait autorité ; ce fichier n'en est que la transcription.
/// Chaque membre rappelle le nom du jeton d'origine et son emploi.
library;

/// Échelle d'espacement — §1.1.
///
/// Base **4 dp**, sans valeur intermédiaire. Le nom porte le multiplicateur :
/// [x4] vaut quatre fois la base, soit 16 dp. Un espacement hors de cette
/// échelle n'existe pas.
abstract final class Espacements {
  /// `space-1` — écart intra-composant (icône ↔ libellé).
  static const double x1 = 4;

  /// `space-2` — écart minimal entre deux cibles tactiles (§1.4).
  static const double x2 = 8;

  /// `space-3` — rembourrage interne d'une carte.
  static const double x3 = 12;

  /// `space-4` — marge d'écran standard, gauche et droite, partout.
  static const double x4 = 16;

  /// `space-6` — séparation entre blocs.
  static const double x6 = 24;

  /// `space-8` — séparation entre sections d'une modale.
  static const double x8 = 32;

  /// `space-12` — respiration avant une action destructive.
  static const double x12 = 48;
}

/// Rayons d'angle — §1.3.
abstract final class Rayons {
  /// `radius-sm` — champ de saisie, pastille de couleur.
  static const double sm = 8;

  /// `radius-md` — carte, bandeau.
  static const double md = 16;

  /// `radius-lg` — feuille modale, coins hauts uniquement.
  static const double lg = 28;

  /// `radius-full` — pastille de delta, FAB, pastille d'alerte.
  ///
  /// La spécification note ce rayon « ∞ ». Il se transcrit par une valeur finie
  /// très grande, **jamais** par [double.infinity] : `RRect` met à l'échelle les
  /// rayons qui débordent de leur rectangle, et le facteur calculé contre
  /// l'infini vaut zéro — les coins redeviendraient carrés. Un rayon simplement
  /// plus grand que la moitié de la plus petite dimension suffit à produire le
  /// côté parfaitement arrondi attendu.
  static const double complet = 9999;
}

/// Élévations Material, en dp — §1.3.
///
/// Sur la carte, l'élévation ne suffit pas : une ombre portée disparaît sur un
/// aplat de couleur franche. Tout élément qui flotte au-dessus de la carte porte
/// **en plus** un contour de 1 dp dans le neutre sombre. C'est une règle de
/// composant : elle s'applique là où le composant naît, pas ici.
abstract final class Elevations {
  /// `elev-0` — contenu à plat.
  static const double e0 = 0;

  /// `elev-1` — puces de header, bandeau.
  static const double e1 = 1;

  /// `elev-3` — bouton flottant sur la carte.
  static const double e3 = 3;

  /// `elev-6` — feuille modale, modale de confirmation.
  static const double e6 = 6;
}
