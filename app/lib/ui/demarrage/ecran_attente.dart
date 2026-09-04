import 'package:flutter/material.dart';

import '../../domain/bandeau/entree_bandeau.dart';
import '../../l10n/generated/app_localizations.dart';
import '../core/bandeau/emplacement_bandeau.dart';
import '../core/boutons/bouton_pleine_largeur.dart';
import '../core/marque/marque_centree.dart';
import '../core/mise_en_page/pile_de_calques.dart';
import '../core/theme/mesures.dart';
import '../core/theme/typographie.dart';
import 'etat_demarrage.dart';

/// L'écran d'attente neutre de la séquence de démarrage — spec UX §2.1.
///
/// Le bloc de marque, centré, **et rien d'autre** : aucun indicateur de
/// progression. Le bloc affiché est déjà le signe que l'application démarre,
/// et l'attente est bornée par le délai du client HTTP — l'écran ne peut pas
/// rester statique plus longtemps que ça avant de basculer.
///
/// Selon [etat], paraît **sous** le bloc, sans jamais le déplacer :
/// - [Injoignable] — « Le serveur ne répond pas. » et « Réessayer », jamais
///   le Menu ;
/// - [Verification] et [Pret] — rien.
///
/// [MiseAJourRequise] ne passe **pas** par cet écran : la racine y substitue
/// l'écran bloquant du §11.2, qui remplace tout, bandeau compris.
///
/// Le bandeau (§2.4) occupe son calque — la ligne 5 hors ligne, la 12 quand
/// une mise à jour est recommandée. C'est le [DemarrageViewModel] qui décide
/// laquelle ; l'écran affiche ce qu'on lui donne.
class EcranAttente extends StatelessWidget {
  /// Crée l'écran pour [etat], avec l'éventuelle ligne de bandeau active.
  const EcranAttente({
    required this.etat,
    required this.entreeBandeau,
    required this.onReessayer,
    super.key,
  });

  /// L'état de la séquence, qui choisit la zone sous le bloc de marque.
  final EtatDemarrage etat;

  /// La ligne de bandeau à afficher, ou `null` — résolue par le ViewModel.
  final EntreeBandeau? entreeBandeau;

  /// Relance le contrôle de version — l'action de « Réessayer ».
  final VoidCallback onReessayer;

  @override
  Widget build(BuildContext context) {
    final textes = AppLocalizations.of(context);
    return Scaffold(
      body: PileDeCalques(
        children: {
          // Le calque de base est le seul que `PileDeCalques` laisse hors
          // safe area — une exemption écrite pour une carte qui court sous
          // l'encoche (§2.3), pas pour du contenu : cet écran n'a pas de
          // carte, la `SafeArea` est donc rétablie ici, sans quoi le bouton
          // « Réessayer » passerait sous la barre de gestes (§1.4).
          Calque.carte: SafeArea(
            child: SizedBox.expand(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: Espacements.x4),
                // Deux plans indépendants, et c'est ce qui tient l'invariant
                // du §2.1 : le bloc est centré seul, le bouton est ancré en
                // bas. Ni l'un ni l'autre ne peut donc déplacer le bloc.
                child: Stack(
                  children: [
                    MarqueCentree(sous: _zoneEtat(context, textes)),
                    if (etat is Injoignable)
                      Align(
                        alignment: Alignment.bottomCenter,
                        child: Padding(
                          padding: const EdgeInsets.only(
                            bottom: Espacements.x6,
                          ),
                          child: BoutonPleineLargeur(
                            libelle: textes.attenteActionReessayer,
                            onPressed: onReessayer,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
          Calque.bandeau: EmplacementBandeau(entree: entreeBandeau),
        },
      ),
    );
  }

  /// Ce qui vit sous le bloc de marque : le message d'échec, ou rien.
  Widget _zoneEtat(BuildContext context, AppLocalizations textes) {
    return switch (etat) {
      Injoignable() => Text(
        textes.attenteServeurInjoignable,
        style: Typographie.body.copyWith(
          color: Theme.of(context).colorScheme.onSurface,
        ),
        textAlign: TextAlign.center,
      ),
      // Explicites, jamais un `_` : un état ajouté à `EtatDemarrage` doit
      // forcer CE point de décision à se prononcer aussi (promesse de la
      // docstring du scellé).
      Verification() || MiseAJourRequise() || Pret() => const SizedBox.shrink(),
    };
  }
}
