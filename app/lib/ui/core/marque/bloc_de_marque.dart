import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../../../l10n/generated/app_localizations.dart';
import '../theme/mesures.dart';
import '../theme/typographie.dart';

/// Le bloc de marque — signe, logotype, accroche — spec UX §4.
///
/// Une seule composition pour les trois écrans sans carte : écran d'attente
/// (§2.1), Connexion (§4) et Accueil (§5). L'accroche reste discrète — jamais
/// à la taille du nom, jamais au-dessus de lui (§4).
///
/// Le signe est l'actif `assets/signe-arpendo.svg`, copié tel quel depuis
/// `documents/assets/` (source unique) et teinté par `ColorFilter.mode(…,
/// srcIn)` : les opacités 0,30 / 0,58 des courbes sont conservées, et le mode
/// sombre vient du thème sans second fichier. Le logotype est composé en
/// Roboto w500 (§1.2, amendement du 3 septembre 2026 — archive §18.8), à la
/// hauteur de capitale que le §4 fixe.
class BlocDeMarque extends StatelessWidget {
  /// Crée le bloc de marque. Sans paramètre : la marque ne se décline pas.
  const BlocDeMarque({super.key});

  /// Côté du signe, en dp — §4.
  static const double _coteSigne = 96;

  /// Hauteur de capitale du logotype, en dp — §4.
  static const double _hauteurCapitale = 24;

  /// Ratio hauteur de capitale / corps de Roboto Medium, **lu dans la fonte**
  /// (`OS/2.sCapHeight` 1456 / `head.unitsPerEm` 2048, Roboto-Medium.ttf du
  /// SDK Android, platform-28). Le §4 fixe la capitale à 24 dp ; le corps s'en
  /// dérive, il ne se pose pas.
  static const double _ratioCapitale = 1456 / 2048;

  /// Corps du logotype — le seul qui rende la capitale à [_hauteurCapitale].
  static const double _corpsLogotype = _hauteurCapitale / _ratioCapitale;

  /// Interlettrage du logotype, en em — identité §1.5.
  static const double _interlettrageLogotype = 0.02;

  @override
  Widget build(BuildContext context) {
    final couleurs = Theme.of(context).colorScheme;
    final textes = AppLocalizations.of(context);
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SvgPicture.asset(
          'assets/signe-arpendo.svg',
          width: _coteSigne,
          height: _coteSigne,
          colorFilter: ColorFilter.mode(couleurs.primary, BlendMode.srcIn),
        ),
        const SizedBox(height: Espacements.x3),
        Text(
          textes.marqueNom,
          style: TextStyle(
            fontSize: _corpsLogotype,
            fontWeight: FontWeight.w500,
            letterSpacing: _corpsLogotype * _interlettrageLogotype,
            // Boîte serrée sur le corps : l'interligne Roboto par défaut
            // gonflerait les écarts `space-3` / `space-2` que le §4 mesure
            // entre les éléments, pas entre des boîtes de ligne.
            height: 1,
            color: couleurs.primary,
          ),
        ),
        const SizedBox(height: Espacements.x2),
        Text(
          textes.marqueAccroche,
          style: Typographie.body.copyWith(color: couleurs.onSurfaceVariant),
        ),
      ],
    );
  }
}
