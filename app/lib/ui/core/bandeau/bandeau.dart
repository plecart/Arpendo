import 'package:flutter/material.dart';

import '../../../domain/bandeau/entree_bandeau.dart';
import '../../../l10n/generated/app_localizations.dart';
import '../theme/icones.dart';
import '../theme/mesures.dart';
import '../theme/theme.dart';
import '../theme/typographie.dart';

/// Le composant **unique** qui porte tout message d'état — spec UX §2.4.
///
/// Un seul existe dans le projet : permissions (§9.3), réseau (§10),
/// explication d'action sans effet (§4.2, §4.3) et mise à jour recommandée
/// (§14.1) ont la même anatomie et le même emplacement, et le cadrage impose
/// explicitement de n'en faire qu'un.
///
/// **Il ne décide de rien.** Quelle entrée afficher est la réponse de
/// `resoudre` (`lib/domain/bandeau/`) ; ce widget rend celle qu'on lui donne.
/// C'est ce partage qui permet à la notification permanente d'Android (§10.2)
/// d'appliquer la même règle sans widget.
///
/// **Sa hauteur est dictée par son contenu**, jamais fixée (§0 : les
/// conteneurs grandissent, ils ne tronquent pas) : 56 dp sur une ligne sans
/// action, 80 dp dès que le message passe sur deux lignes, 112 dp dès qu'une
/// action est présente. Ce sont des **résultats** du rembourrage
/// [Espacements.x4] appliqué à une ligne de `type-body` (24 dp) ou à une cible
/// tactile ([CiblesTactiles.min]) ; les tests les mesurent, le code ne les
/// pose nulle part.
///
/// **Les actions descendent sur une seconde rangée**, et ce n'est pas un choix
/// de style : sur l'écran de référence de 360 dp, il ne reste que 260 dp après
/// les marges, le rembourrage et l'icône, et les deux actions des priorités 10
/// et 11 les consomment à elles seules. Le message garde donc toute la
/// largeur, ce qui le rend insensible à la longueur des libellés comme à la
/// tolérance de +30 % du §0 (§2.4, amendé le 30 août 2026 — archive §18.7).
class Bandeau extends StatelessWidget {
  /// Crée le bandeau qui rend [entree].
  const Bandeau({required this.entree, super.key});

  /// La ligne à afficher, choisie par `resoudre`.
  final EntreeBandeau entree;

  @override
  Widget build(BuildContext context) {
    final couleurs = Theme.of(context).colorScheme;
    final textes = AppLocalizations.of(context);
    return Padding(
      // Largeur pleine moins une marge d'écran de chaque côté (§2.4).
      padding: const EdgeInsets.symmetric(horizontal: Espacements.x4),
      child: Material(
        color: couleurs.surface,
        elevation: Elevations.e1,
        // Le contour de 1 dp n'est pas décoratif : une ombre portée disparaît
        // sur l'aplat de couleur franche d'un hexagone capturé, et le bandeau
        // flotte au-dessus de la carte (§1.3).
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Rayons.md),
          side: BorderSide(color: couleurs.outline),
        ),
        child: Padding(
          padding: const EdgeInsets.all(Espacements.x4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    _glyphe(entree.severite),
                    color: _couleur(context, entree.severite),
                    size: Icones.taille,
                  ),
                  const SizedBox(width: Espacements.x3),
                  Expanded(
                    child: Text(
                      entree.texte(textes),
                      style: Typographie.body.copyWith(
                        color: couleurs.onSurface,
                      ),
                    ),
                  ),
                ],
              ),
              if (entree.actions.isNotEmpty) ...[
                const SizedBox(height: Espacements.x2),
                // `Wrap` et non `Row` : le §1.2 exige de suivre le réglage de
                // taille de police du système **jusqu'à 200 % sans
                // troncature**, et la locale allongée du garde `fr-XA` ajoute
                // encore 30 %. Deux libellés côte à côte finissent par ne plus
                // tenir sur 360 dp ; ils passent alors l'un sous l'autre au
                // lieu de déborder, ce que le §0 impose.
                Wrap(
                  alignment: WrapAlignment.end,
                  spacing: Espacements.x2,
                  children: [
                    for (final action in entree.actions)
                      TextButton(
                        onPressed: action.onPressed,
                        style: TextButton.styleFrom(
                          // La cible tactile du §1.4 **sur les deux axes** :
                          // « 48 × 48 dp, aucune exception ». Le défaut
                          // Material vaut 64 × 40, donc trop plat. Porté par
                          // le bouton lui-même faute de thème de composant :
                          // celui-ci naîtra avec le premier écran qui puisse
                          // le valider à l'œil (#46).
                          minimumSize: const Size.square(CiblesTactiles.min),
                        ),
                        child: Text(action.libelle(textes)),
                      ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// La silhouette qui **porte** la sévérité — §2.4.
///
/// Cercle, triangle et octogone sont trois formes distinctes, donc lisibles en
/// niveaux de gris, à petite taille et pour un daltonien. La sévérité ne se
/// lit **jamais** à la couleur seule ; le glyphe se dérive donc d'elle, il ne
/// se reçoit pas en paramètre (§2.4, amendé le 30 août 2026).
IconData _glyphe(Severite severite) => switch (severite) {
  Severite.info => Icones.severiteInfo,
  Severite.avertissement => Icones.severiteAvertissement,
  Severite.bloquant => Icones.severiteBloquant,
};

/// La couleur du glyphe, **transcrite de la table du §1.5** — les trois
/// sévérités ne créent aucun jeton, la couleur n'est qu'un renfort pris dans
/// les jetons existants, et le sens reste porté par la forme.
///
/// `on-surface-muted` · `warning` · `danger`, dans cet ordre. Seule
/// `avertissement` n'a pas de rôle Material : elle vient de [CouleursChrome].
/// Ces couleurs ne colorent que du texte et des icônes, jamais un aplat.
Color _couleur(BuildContext context, Severite severite) {
  final couleurs = Theme.of(context).colorScheme;
  return switch (severite) {
    Severite.info => couleurs.onSurfaceVariant,
    Severite.avertissement => CouleursChrome.of(context).warning,
    Severite.bloquant => couleurs.error,
  };
}
