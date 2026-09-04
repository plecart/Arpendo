import 'package:flutter/material.dart';

import 'mesures.dart';
import 'typographie.dart';

/// Assemble le `ThemeData` de l'application à partir des jetons de la spec UX §1.
///
/// C'est le seul point d'entrée du module : `ArpendoApp` en tire son `theme` et
/// son `darkTheme`, et tout écran lit ensuite ses valeurs par le contexte —
/// `Theme.of(context).colorScheme` pour les rôles Material, [CouleursChrome.of]
/// pour les deux couleurs que Material ne sait pas nommer.
///
/// Le mode sombre est **disponible, jamais imposé** (§1.5) : c'est
/// `themeMode: ThemeMode.system` côté `MaterialApp` qui l'arbitre, et rien
/// d'autre.
///
/// Les thèmes de composant naissent avec le premier composant qui les réclame,
/// avec un écran sous les yeux pour les valider : `FilledButtonThemeData` et
/// `TextButtonThemeData` sont arrivés avec le premier écran (#46) ;
/// `InputDecorationTheme` et leurs semblables suivront le leur.
ThemeData themeArpendo(Brightness brightness) => switch (brightness) {
  Brightness.light => _clair,
  Brightness.dark => _sombre,
};

/// Les deux thèmes, construits une fois pour toutes.
///
/// `ThemeData` compare ses extensions avec `==`, et [CouleursChrome] n'en
/// définit pas : deux instances aux mêmes valeurs se compareraient donc
/// **inégales**. Le `Theme` de l'arbre notifierait alors ses dépendants à chaque
/// reconstruction de la racine, et tout ce qui lit une couleur se reconstruirait
/// pour rien. Rendre le même objet règle le problème sans imposer un `==` et un
/// `hashCode` à écrire à la main sur chaque extension future — et évite au
/// passage de rebâtir deux `ThemeData` à chaque `build`. Les deux
/// `WidgetStateProperty.resolveWith` du bouton rempli sont des fermetures
/// qui se comparent aussi par identité : donner un `==` à l'extension ne
/// suffirait plus à se passer du singleton.
final ThemeData _clair = _construire(_Palette.clair);
final ThemeData _sombre = _construire(_Palette.sombre);

/// Hauteur du bouton principal, en dp (§4, §11.2).
const double _hauteurBoutonPrincipal = 56;

/// Largeur minimale d'un bouton — le plancher Material, conservé tel quel :
/// c'est la mise en page qui décide d'une pleine largeur, pas le thème.
const double _largeurMinimaleBouton = 64;

/// Le `ThemeData` d'une palette.
///
/// La palette porte son mode ; la fabrique n'a donc qu'un paramètre, et il n'y a
/// pas d'appel à écrire qui apparierait la palette claire à [Brightness.dark].
ThemeData _construire(_Palette palette) {
  return ThemeData(
    colorScheme: ColorScheme(
      brightness: palette.brightness,
      surface: palette.surface,
      surfaceDim: palette.surfaceDim,
      onSurface: palette.onSurface,
      onSurfaceVariant: palette.onSurfaceMuted,
      outline: palette.outline,
      scrim: palette.scrim,
      primary: palette.accent,
      onPrimary: palette.surAplat,
      primaryContainer: palette.accentLight,
      onPrimaryContainer: palette.onSurface,
      secondary: palette.accent,
      onSecondary: palette.surAplat,
      error: palette.danger,
      onError: palette.surAplat,
    ),
    textTheme: Typographie.creneauxMaterial,
    // Fond d'écran hors carte (§1.5) : `surface` est réservée aux modales et
    // aux feuilles. Solde le report documenté par #34/#60.
    scaffoldBackgroundColor: palette.surfaceDim,
    filledButtonTheme: FilledButtonThemeData(
      style: ButtonStyle(
        // L'appui est le jeton `accent-pressed`, dont l'inversion clair/sombre
        // est déjà encodée (§1.5) — pas un voile Material par-dessus.
        //
        // La fusion `widget ?? thème ?? défaut` se joue sur la **valeur
        // résolue**, état par état (`button_style_button.dart`) : chaque
        // résolveur ne répond que pour les états qu'il décide, et rend `null`
        // partout ailleurs pour laisser vivre le défaut Material — dont le
        // fond `onSurface` à 12 % du bouton désactivé, sans lequel un bouton
        // inactif resterait visuellement actif.
        backgroundColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.disabled)) return null;
          return states.contains(WidgetState.pressed)
              ? palette.accentPressed
              : palette.accent;
        }),
        // Seule la surbrillance d'appui est remplacée par `accent-pressed` ;
        // un transparent sur tous les états éteindrait aussi le focus et le
        // hover (`filled_button.dart` : « pressed/focused/hovered highlights
        // are effectively defeated »).
        overlayColor: WidgetStateProperty.resolveWith(
          (states) =>
              states.contains(WidgetState.pressed) ? Colors.transparent : null,
        ),
        // 56 dp de haut — la hauteur du bouton principal, partout où il
        // apparaît (§4, §11.2). La largeur garde le plancher Material : c'est
        // la mise en page qui décide d'une pleine largeur, pas le thème.
        minimumSize: const WidgetStatePropertyAll(
          Size(_largeurMinimaleBouton, _hauteurBoutonPrincipal),
        ),
        // Vide de spec comblé au brief de #46 : un bouton pleine largeur est
        // une surface de contenu, pas « rond par nature » (§7.1) — `radius-md`,
        // à confirmer à l'œil en HITL.
        shape: WidgetStatePropertyAll(
          RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(Rayons.md),
          ),
        ),
      ),
    ),
    // La cible tactile du §1.4 sur les deux axes — « 48 × 48 dp, aucune
    // exception », là où le défaut Material vaut 64 × 40. Dans le thème pour
    // que les actions du bandeau (§2.4) comme tout futur bouton texte la
    // reçoivent sans style local — un style de widget masquerait celui-ci.
    textButtonTheme: const TextButtonThemeData(
      style: ButtonStyle(
        minimumSize: WidgetStatePropertyAll(Size.square(CiblesTactiles.min)),
      ),
    ),
    extensions: [
      CouleursChrome(
        accentPressed: palette.accentPressed,
        warning: palette.warning,
      ),
    ],
  );
}

/// Les couleurs de chrome du §1.5 qui n'ont pas de rôle Material 3.
///
/// `accent-pressed` et `warning` sont les deux seules à ne correspondre à aucun
/// créneau de `ColorScheme` ; les neuf autres y sont rangées par [_construire].
/// Elles voyagent donc dans cette extension plutôt que d'être posées en dur au
/// point d'usage.
@immutable
class CouleursChrome extends ThemeExtension<CouleursChrome> {
  const CouleursChrome({required this.accentPressed, required this.warning});

  /// `accent-pressed` — l'accent sous le doigt.
  ///
  /// **S'inverse selon le mode** : il fonce en clair, il éclaircit en sombre.
  /// Ce n'est pas une préférence — foncer un accent pâle en mode sombre le fait
  /// retomber dans la bande de clarté des couleurs joueur, mesuré à ΔE 11 à 12,
  /// sous le plancher de 15. C'est la méthode des *state layers* de Material 3,
  /// appliquée ici par nécessité.
  final Color accentPressed;

  /// `warning` — avertissement non bloquant.
  ///
  /// **Couleur de texte et d'icône seulement**, jamais de remplissage sur la
  /// couche carte : `danger` est à ΔE 3,1 du brique joueur, et cette règle
  /// d'emploi est ce qui tient lieu de correction (§1.5). Il n'existe pas de
  /// jeton `success` en regard : un état positif se porte par le glyphe et le
  /// texte, et prend `accent` là où une couleur est nécessaire.
  final Color warning;

  /// Les couleurs de chrome du thème ambiant.
  static CouleursChrome of(BuildContext context) {
    final chrome = Theme.of(context).extension<CouleursChrome>();
    assert(
      chrome != null,
      'Thème construit hors de themeArpendo() : les couleurs de chrome manquent.',
    );
    return chrome!;
  }

  @override
  CouleursChrome copyWith({Color? accentPressed, Color? warning}) =>
      CouleursChrome(
        accentPressed: accentPressed ?? this.accentPressed,
        warning: warning ?? this.warning,
      );

  @override
  CouleursChrome lerp(covariant CouleursChrome? other, double t) {
    if (other == null) return this;
    return CouleursChrome(
      accentPressed: Color.lerp(accentPressed, other.accentPressed, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
    );
  }
}

/// Les onze couleurs de chrome d'un mode, sous les noms de jetons du §1.5.
///
/// Deux instances, une par mode, et une seule table de correspondance vers les
/// rôles Material dans [_construire] — le mapping n'est donc écrit qu'une fois.
@immutable
class _Palette {
  const _Palette({
    required this.brightness,
    required this.surface,
    required this.surfaceDim,
    required this.onSurface,
    required this.onSurfaceMuted,
    required this.outline,
    required this.scrim,
    required this.accent,
    required this.accentPressed,
    required this.accentLight,
    required this.danger,
    required this.warning,
    required this.surAplat,
  });

  /// Le mode dont cette palette est la lecture.
  ///
  /// Il appartient à la palette et non à l'appelant : c'est ce qui empêche
  /// d'apparier les couleurs claires à [Brightness.dark].
  final Brightness brightness;

  /// Fond de modale, de feuille.
  final Color surface;

  /// Fond d'écran hors carte, fond de la carte masquée.
  final Color surfaceDim;

  /// Texte principal.
  final Color onSurface;

  /// Texte secondaire, horodatage.
  final Color onSurfaceMuted;

  /// Contours, séparateurs.
  final Color outline;

  /// Voile derrière une modale, **opacité comprise** : le jeton de la spec est
  /// une couleur déjà voilée, pas une couleur à voiler au point d'usage.
  final Color scrim;

  /// Action principale.
  final Color accent;

  /// État pressé — voir [CouleursChrome.accentPressed].
  final Color accentPressed;

  /// Fond teinté : sélection, encart.
  final Color accentLight;

  /// Action destructive, erreur bloquante. Texte et icône seulement.
  final Color danger;

  /// Avertissement non bloquant. Texte et icône seulement.
  final Color warning;

  /// Texte et icône posés **sur** un aplat d'[accent].
  ///
  /// Le §1.5 mesure le blanc sur l'accent clair à 12,27:1. En sombre l'accent
  /// est pâle : la spécification est muette sur ce qui se pose dessus, et le
  /// neutre le plus sombre reprend exactement le rapport qu'elle mesure dans
  /// l'autre sens — `accent` sombre à 15,62:1 **sur** `surface-dim`.
  ///
  /// Sert aussi de `onError`, que `ColorScheme` exige. Ce rôle ne s'affiche
  /// jamais : `danger` ne remplit aucune surface (§1.5), il ne colore que du
  /// texte et des icônes posés sur `surface`.
  final Color surAplat;

  /// Mode clair — le défaut.
  static const clair = _Palette(
    brightness: Brightness.light,
    surface: Color(0xFFFDFBF6),
    surfaceDim: Color(0xFFF1EDE2),
    onSurface: Color(0xFF1A1D18),
    onSurfaceMuted: Color(0xFF5C6157),
    outline: Color(0xFFC7C3B5),
    // `on-surface` à 40 % — 0x66 sur 0xFF.
    scrim: Color(0x661A1D18),
    accent: Color(0xFF123D1E),
    accentPressed: Color(0xFF052D11),
    accentLight: Color(0xFFE8EFE9),
    danger: Color(0xFFB3261E),
    warning: Color(0xFF7A4F00),
    surAplat: Color(0xFFFFFFFF),
  );

  /// Mode sombre — disponible, jamais imposé : il suit le réglage système.
  static const sombre = _Palette(
    brightness: Brightness.dark,
    surface: Color(0xFF1A1E1A),
    surfaceDim: Color(0xFF101310),
    onSurface: Color(0xFFEDEAE0),
    onSurfaceMuted: Color(0xFF9CA096),
    outline: Color(0xFF3A403A),
    // Noir à 55 % — 0x8C sur 0xFF. Un voile de 40 % ne sépare rien sur fond
    // sombre.
    scrim: Color(0x8C000000),
    accent: Color(0xFFC9F7BE),
    accentPressed: Color(0xFFD2F8C8),
    accentLight: Color(0xFF23331F),
    danger: Color(0xFFF2B8B5),
    warning: Color(0xFFF5C77E),
    surAplat: Color(0xFF101310),
  );
}
