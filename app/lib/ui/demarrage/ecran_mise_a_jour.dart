import 'package:flutter/material.dart';

import '../../l10n/generated/app_localizations.dart';
import '../core/boutons/bouton_pleine_largeur.dart';
import '../core/marque/bloc_de_marque.dart';
import '../core/mise_en_page/pile_de_calques.dart';
import '../core/theme/mesures.dart';
import '../core/theme/typographie.dart';

/// L'écran bloquant de version minimale — spec UX §11.2.
///
/// Le seul écran du projet dont on **ne peut pas sortir** : ni bouton retour,
/// ni fermeture, ni geste de retour Android ([PopScope] avec `canPop: false`).
/// Ce n'est pas une modale qu'on écarte, c'est la fin du parcours tant que le
/// build installé est sous le minimum publié par le serveur — l'application ne
/// sait plus parler à l'api, la laisser continuer ne produirait que des
/// erreurs incompréhensibles.
///
/// Il occupe [Calque.bloquant] (z 500), le rang le plus haut du §2.2. Rien
/// n'est peint sous lui ici — la racine le rend seul — mais le dire dans la
/// pile garde le rang **écrit là où il s'applique**, et vaut à l'écran la
/// `SafeArea` que [PileDeCalques] pose sur tout sauf la carte.
///
/// [onMettreAJour] ouvre la fiche du magasin. L'écran ne sait pas comment —
/// c'est la racine de composition qui branche le service, et c'est ce qui rend
/// cet écran testable sans plateforme.
class EcranMiseAJour extends StatelessWidget {
  /// Crée l'écran ; [onMettreAJour] est son unique action.
  const EcranMiseAJour({required this.onMettreAJour, super.key});

  /// Ouvre la fiche du magasin — l'action du bouton « Mettre à jour ».
  final VoidCallback onMettreAJour;

  @override
  Widget build(BuildContext context) {
    final textes = AppLocalizations.of(context);
    return Scaffold(
      // `canPop: false` refuse le geste de retour ET le bouton système : le
      // §11.2 dit « pas de bouton retour, pas de fermeture », et sur Android
      // le geste est le chemin qu'on oublie de fermer.
      body: PopScope(
        canPop: false,
        child: PileDeCalques(
          children: {
            Calque.bloquant: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: Espacements.x4,
                vertical: Espacements.x6,
              ),
              // Deux plans indépendants, comme sur l'écran d'attente : le bloc
              // de marque est centré seul, le bouton est ancré en bas. Ni
              // l'un ni l'autre ne peut donc déplacer le bloc, et le logo ne
              // saute pas au passage attente → bloquant.
              child: Stack(
                children: [
                  Center(child: _blocEtMessage(context, textes)),
                  Align(
                    alignment: Alignment.bottomCenter,
                    child: BoutonPleineLargeur(
                      libelle: textes.miseAJourAction,
                      onPressed: onMettreAJour,
                    ),
                  ),
                ],
              ),
            ),
          },
        ),
      ),
    );
  }

  /// Le bloc de marque, et sous lui les trois textes du §11.2 — **peints sans
  /// compter dans la hauteur** du groupe.
  ///
  /// Même mécanique que l'écran d'attente, et pour la même raison : le
  /// [Center] ne mesure que le bloc, donc le logo occupe exactement la place
  /// qu'il occupe là-bas. Passer de l'un à l'autre ne le déplace pas.
  Widget _blocEtMessage(BuildContext context, AppLocalizations textes) {
    final couleurs = Theme.of(context).colorScheme;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const BlocDeMarque(),
        Align(
          alignment: Alignment.topCenter,
          heightFactor: 0,
          child: Padding(
            padding: const EdgeInsets.only(top: Espacements.x6),
            child: Column(
              children: [
                Text(
                  textes.miseAJourTitre,
                  style: Typographie.title.copyWith(color: couleurs.onSurface),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: Espacements.x3),
                Text(
                  textes.miseAJourCorps,
                  style: Typographie.body.copyWith(color: couleurs.onSurface),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: Espacements.x3),
                // La réassurance suit le corps plutôt que le bouton : elle
                // répond à l'inquiétude que le corps vient de créer, et le
                // §11.2 la motive par l'hésitation qu'elle évite — donc elle
                // doit être lue AVANT la décision de taper.
                Text(
                  textes.miseAJourProgressionConservee,
                  style: Typographie.caption.copyWith(
                    color: couleurs.onSurfaceVariant,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
