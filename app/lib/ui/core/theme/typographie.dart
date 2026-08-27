import 'package:flutter/material.dart';

/// Échelle typographique — spec UX §1.2, avec la contrainte du code de partie
/// (§1.7).
///
/// Famille **Roboto**, la police système Android : aucune police n'est embarquée,
/// et rien n'est donc déclaré ici — c'est déjà le défaut de Flutter sur la
/// plateforme. Seuls les deux styles monospace nomment une famille, parce que
/// celle-là ne s'obtient pas par défaut.
///
/// Les huit styles sont l'unique source de l'échelle. [creneauxMaterial] les range
/// dans les créneaux Material pour que les widgets du framework tombent juste ; les
/// écrans, eux, lisent les membres nommés — `Typographie.body` dit ce qu'il vaut,
/// `bodyLarge` demande de se souvenir de la table de correspondance.
///
/// Aucun style ne porte de couleur : elle vient du `ColorScheme` par le contexte.
abstract final class Typographie {
  /// `type-display` — score du header, chiffre du tableau des scores.
  static const TextStyle display = TextStyle(
    fontSize: 32,
    height: 38 / 32,
    fontWeight: FontWeight.w700,
    letterSpacing: 0,
  );

  /// `type-title` — titre de modale.
  static const TextStyle title = TextStyle(
    fontSize: 24,
    height: 30 / 24,
    fontWeight: FontWeight.w600,
    letterSpacing: 0,
  );

  /// `type-headline` — titre de section, nom d'écran.
  static const TextStyle headline = TextStyle(
    fontSize: 20,
    height: 26 / 20,
    fontWeight: FontWeight.w600,
    letterSpacing: 0,
  );

  /// `type-body` — texte courant, **taille plancher de tout texte lisible**.
  static const TextStyle body = TextStyle(
    fontSize: 16,
    height: 24 / 16,
    fontWeight: FontWeight.w400,
    letterSpacing: 0,
  );

  /// `type-label` — libellé de bouton, ligne de liste secondaire.
  static const TextStyle label = TextStyle(
    fontSize: 14,
    height: 20 / 14,
    fontWeight: FontWeight.w500,
    letterSpacing: 0,
  );

  /// `type-caption` — horodatage, mention de fraîcheur, unité.
  ///
  /// Seul style de l'échelle courante à porter un interlettrage positif :
  /// `+0,01 em`. Les petites tailles se referment au soleil, et c'est le seul
  /// endroit où l'espacement gagne de la lisibilité. [mono] et [monoDisplay] ont
  /// le leur, mais il ne vient pas de là : c'est la lecture du code de partie qui
  /// le dicte (§1.7).
  static const TextStyle caption = TextStyle(
    fontSize: 12,
    height: 16 / 12,
    fontWeight: FontWeight.w400,
    letterSpacing: 12 * 0.01,
  );

  /// `type-mono` — **saisie** du code de partie (§1.7).
  static const TextStyle mono = TextStyle(
    fontSize: 20,
    height: 26 / 20,
    fontWeight: FontWeight.w500,
    fontFamily: _monospace,
    letterSpacing: 20 * _interlettrageCode,
  );

  /// `type-mono-display` — **affichage** du code dans l'onglet Inviter (§7.4).
  static const TextStyle monoDisplay = TextStyle(
    fontSize: 40,
    height: 48 / 40,
    fontWeight: FontWeight.w500,
    fontFamily: _monospace,
    letterSpacing: 40 * _interlettrageCode,
  );

  /// Famille monospace du système Android — alias résolu par la plateforme,
  /// donc sans coût d'APK, comme Roboto.
  static const String _monospace = 'monospace';

  /// Interlettrage du code de partie, **en em** (§1.7).
  ///
  /// `letterSpacing` s'exprime en pixels logiques côté Flutter ; on le dérive
  /// donc de la taille du style. Un `letterSpacing: 4` absolu vaudrait un
  /// cinquième de la chasse à 20 dp et un dixième à 40 dp — le même jeton
  /// produirait deux respirations différentes, ce qu'une échelle typographique
  /// sert précisément à empêcher.
  static const double _interlettrageCode = 0.20;

  /// Les styles rangés dans les créneaux Material qui leur correspondent.
  ///
  /// Sept créneaux pour six styles : [body] en occupe deux, parce que `bodyMedium`
  /// est le style d'un `Text` sans style explicite sous Material et que le §1.2
  /// fait de `type-body` la taille plancher de tout texte lisible. [mono] et
  /// [monoDisplay] n'ont pas d'équivalent Material et ne se lisent que par leur
  /// nom. Les créneaux non listés gardent leur valeur Material — aucun jeton du
  /// projet ne les définit, et en inventer une reviendrait à créer une valeur que
  /// la spécification n'a pas décidée.
  ///
  /// **Chaque style déclare son interlettrage, y compris nul.** `MaterialApp`
  /// fusionne cette table avec la géométrie typographique de la locale
  /// (`ThemeData.localize`), et toute propriété laissée indéfinie vient alors de
  /// Material — 0,5 sur `bodyLarge`, 0,1 sur `labelLarge`. Un jeton muet sur une
  /// propriété ne la rend pas : il l'abandonne.
  static const TextTheme creneauxMaterial = TextTheme(
    headlineLarge: display,
    headlineSmall: title,
    titleLarge: headline,
    bodyLarge: body,
    bodyMedium: body,
    labelLarge: label,
    bodySmall: caption,
  );
}

/// La variante à chiffres tabulaires d'un style — §1.2.
extension ChiffresTabulaires on TextStyle {
  /// Le même style, chiffres à chasse fixe.
  ///
  /// À poser sur le score du header, le timer, les scores de liste et le tableau
  /// des scores. Sans elle, un score qui passe de 12 400 à 12 300 fait danser
  /// toute la ligne — un défaut d'autant plus visible que la valeur se met à jour
  /// en continu.
  ///
  /// C'est une **variante du style**, pas un `fontFeatures` posé à l'appel : la
  /// liste de fonctionnalités n'est écrite qu'ici, et s'applique telle quelle aux
  /// huit jetons.
  TextStyle get tabulaire =>
      copyWith(fontFeatures: const [FontFeature.tabularFigures()]);
}
