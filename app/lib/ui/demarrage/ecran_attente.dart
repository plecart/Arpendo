import 'dart:async';

import 'package:flutter/material.dart';

import '../../domain/bandeau/entree_bandeau.dart';
import '../../l10n/generated/app_localizations.dart';
import '../core/bandeau/emplacement_bandeau.dart';
import '../core/boutons/bouton_pleine_largeur.dart';
import '../core/marque/bloc_de_marque.dart';
import '../core/mise_en_page/pile_de_calques.dart';
import '../core/theme/mesures.dart';
import '../core/theme/typographie.dart';
import 'etat_demarrage.dart';

/// L'écran d'attente neutre de la séquence de démarrage — spec UX §2.1.
///
/// Bloc de marque au centre, et selon [etat] :
/// - [Verification] — un indicateur de progression, **après 600 ms
///   seulement** : en dessous, il clignote et donne une impression de lenteur
///   là où il n'y en a pas ;
/// - [Injoignable] — « Le serveur ne répond pas. » et « Réessayer », jamais
///   le Menu ;
/// - [Pret] et [MiseAJourRequise] — l'écran reste, neutre (l'écran bloquant
///   de [MiseAJourRequise] est livré par le lot 2c de #46).
///
/// Le bandeau (§2.4) occupe son calque : la ligne 5 quand le téléphone est
/// hors ligne — c'est le [DemarrageViewModel] qui décide, l'écran affiche.
class EcranAttente extends StatefulWidget {
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

  /// L'attente silencieuse avant l'indicateur de progression (§2.1).
  static const delaiIndicateur = Duration(milliseconds: 600);

  @override
  State<EcranAttente> createState() => _EcranAttenteState();
}

class _EcranAttenteState extends State<EcranAttente> {
  Timer? _minuteur;
  bool _indicateurVisible = false;

  @override
  void initState() {
    super.initState();
    _armer();
  }

  @override
  void didUpdateWidget(EcranAttente ancien) {
    super.didUpdateWidget(ancien);
    if (ancien.etat != widget.etat) {
      _armer();
    }
  }

  @override
  void dispose() {
    _minuteur?.cancel();
    super.dispose();
  }

  /// (Ré)arme le délai de l'indicateur pour l'état courant.
  ///
  /// Chaque retour en [Verification] repart de zéro : un « Réessayer » qui
  /// répond vite ne doit pas montrer d'indicateur du tout.
  void _armer() {
    _minuteur?.cancel();
    _indicateurVisible = false;
    if (widget.etat is Verification) {
      _minuteur = Timer(EcranAttente.delaiIndicateur, () {
        setState(() => _indicateurVisible = true);
      });
    }
  }

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
                child: Column(
                  children: [
                    const Spacer(),
                    const BlocDeMarque(),
                    const SizedBox(height: Espacements.x6),
                    _zoneEtat(context, textes),
                    const Spacer(),
                    if (widget.etat is Injoignable)
                      Padding(
                        padding: const EdgeInsets.only(bottom: Espacements.x6),
                        child: BoutonPleineLargeur(
                          libelle: textes.attenteActionReessayer,
                          onPressed: widget.onReessayer,
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
          Calque.bandeau: EmplacementBandeau(entree: widget.entreeBandeau),
        },
      ),
    );
  }

  /// Ce qui vit sous le bloc de marque : indicateur, message d'échec, ou rien.
  Widget _zoneEtat(BuildContext context, AppLocalizations textes) {
    return switch (widget.etat) {
      Verification() when _indicateurVisible =>
        const CircularProgressIndicator(),
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
