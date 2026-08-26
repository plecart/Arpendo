import 'package:flutter/material.dart';

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
/// Aucun thème de composant n'est posé ici. `FilledButtonThemeData`,
/// `InputDecorationTheme` et leurs semblables naissent avec le premier composant
/// qui les réclame, avec un écran sous les yeux pour les valider.
ThemeData themeArpendo(Brightness brightness) {
  final palette = switch (brightness) {
    Brightness.light => _Palette.clair,
    Brightness.dark => _Palette.sombre,
  };

  return ThemeData(
    colorScheme: ColorScheme(
      brightness: brightness,
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
/// créneau de `ColorScheme` ; les neuf autres y sont rangées par
/// [themeArpendo]. Elles voyagent donc dans cette extension plutôt que d'être
/// posées en dur au point d'usage.
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
/// rôles Material dans [themeArpendo] — le mapping n'est donc écrit qu'une fois.
@immutable
class _Palette {
  const _Palette({
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
