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
/// action, 80 dp dès que le message passe sur deux lignes **ou** qu'une action
/// unique partage sa rangée, 112 dp quand deux actions descendent. Ce sont des
/// **résultats** du rembourrage [Espacements.x4] appliqué à une ligne de
/// `type-body` (24 dp) ou à une cible tactile ([CiblesTactiles.min]) ; les
/// tests les mesurent, le code ne les pose nulle part.
///
/// **C'est le nombre d'actions qui décide de la rangée**, pas leur présence.
/// Une action **seule** partage la rangée du message ; **deux** descendent —
/// sur l'écran de référence de 360 dp, il ne reste que 252 dp après les marges,
/// le rembourrage et l'icône, et les deux actions des priorités 10 et 11 les
/// consomment à elles seules.
///
/// L'action partagée **se replie plutôt que de déborder** : elle est bornée à
/// sa part de la rangée, et son libellé passe sur deux lignes quand il ne tient
/// pas. Ce n'est pas une précaution théorique — la locale allongée du garde
/// `fr-XA` porte « Mettre à jour » à **290 dp** pour 252 disponibles, et un
/// bouton incompressible débordait de 38 px (mesuré). Le §0 est tenu par le
/// repli, jamais par un pari sur la longueur des textes
/// (§2.4, amendé le 30 août 2026 puis le 4 septembre 2026 — archive §18.7).
class Bandeau extends StatelessWidget {
  /// Crée le bandeau qui rend [entree].
  const Bandeau({required this.entree, super.key});

  /// La ligne à afficher, choisie par `resoudre`.
  final EntreeBandeau entree;

  /// L'action qui tient sur la rangée du message, ou `null` — spec UX §2.4.
  ///
  /// Une seule y tient. Deux passent en seconde rangée : c'est le nombre, pas
  /// la présence, qui décide.
  ActionBandeau? get _actionSurLaRangee =>
      entree.actions.length == 1 ? entree.actions.single : null;

  /// Les actions reléguées sous le message — deux, ou aucune.
  List<ActionBandeau> get _actionsEnSecondeRangee =>
      entree.actions.length > 1 ? entree.actions : const [];

  @override
  Widget build(BuildContext context) {
    final couleurs = Theme.of(context).colorScheme;
    final textes = AppLocalizations.of(context);
    // Liée à une locale : un `get` ne se promeut pas, même testé juste avant.
    final actionSeule = _actionSurLaRangee;
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
                // Sans action sur la rangée, l'icône s'aligne sur la première
                // ligne du message — inchangé pour les lignes 5, 10 et 11.
                // Avec, la rangée mêle un libellé de 24 dp et une cible
                // tactile de 48 : les centrer est le seul alignement qui ne
                // fasse pas flotter le message en haut de son bouton.
                crossAxisAlignment: actionSeule == null
                    ? CrossAxisAlignment.start
                    : CrossAxisAlignment.center,
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
                  // Une action **seule** partage la rangée du message : la
                  // mesure du §2.4 qui les en chasse porte sur **deux**
                  // libellés, qui consomment à eux seuls les 260 dp restants.
                  //
                  // `Flexible` et non un enfant nu : à 360 dp, la locale
                  // allongée du garde `fr-XA` porte ce libellé à **290 dp**
                  // pour 296 disponibles — mesuré —, et un bouton
                  // incompressible déborderait de 38 px. Borné, il rend son
                  // libellé sur deux lignes plutôt que de déborder ou de
                  // tronquer, ce que le §0 impose. En français il reprend sa
                  // largeur naturelle : la rangée reste unique.
                  if (actionSeule != null) ...[
                    const SizedBox(width: Espacements.x2),
                    Flexible(
                      child: TextButton(
                        onPressed: actionSeule.onPressed,
                        child: Text(actionSeule.libelle(textes)),
                      ),
                    ),
                  ],
                ],
              ),
              if (_actionsEnSecondeRangee.isNotEmpty) ...[
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
                    for (final action in _actionsEnSecondeRangee)
                      // La cible tactile du §1.4 vient du `TextButtonThemeData`
                      // du thème (#46) — aucun style local : il masquerait le
                      // thème, qui l'emporterait en silence.
                      TextButton(
                        onPressed: action.onPressed,
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
