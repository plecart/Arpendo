import 'package:flutter/material.dart';

import '../../l10n/generated/app_localizations.dart';
import '../core/boutons/bouton_pleine_largeur.dart';
import '../core/marque/marque_centree.dart';
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
              // Marges d'écran horizontales seulement, comme l'écran
              // d'attente : la marge basse est celle de la bande de
              // `MarqueCentree`, et la doubler ici volait 48 dp à la zone du
              // contenu — assez pour lui faire recouvrir le bouton.
              padding: const EdgeInsets.symmetric(horizontal: Espacements.x4),
              // `MarqueCentree` tient les deux plans : le bloc centré dans
              // ce qui reste au-dessus de la bande basse, et le bouton dans
              // cette bande. Le logo occupe donc la même place que sur
              // l'écran d'attente, et rien ne peut le déplacer.
              child: MarqueCentree(
                sous: _message(context, textes),
                bandeBasse: BoutonPleineLargeur(
                  libelle: textes.miseAJourAction,
                  onPressed: onMettreAJour,
                ),
              ),
            ),
          },
        ),
      ),
    );
  }

  /// Les deux textes du §11.2, sous le bloc de marque.
  Widget _message(BuildContext context, AppLocalizations textes) {
    final couleurs = Theme.of(context).colorScheme;
    return Column(
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
      ],
    );
  }
}
