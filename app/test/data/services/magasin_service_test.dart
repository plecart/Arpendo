import 'package:arpendo/data/services/magasin_service.dart';
import 'package:flutter_test/flutter_test.dart';

/// Un lanceur feint : enregistre les liens tentés, et rend ce qu'on lui dit.
///
/// `reponses` est consommée dans l'ordre — une entrée par tentative attendue.
class _LanceurFeint {
  _LanceurFeint(this._reponses);

  final List<Object> _reponses;
  final tentatives = <Uri>[];

  Future<bool> call(Uri uri) async {
    tentatives.add(uri);
    final reponse = _reponses.removeAt(0);
    if (reponse is Exception) throw reponse;
    return reponse as bool;
  }
}

const _identifiant = 'com.arpendo.game';
const _lienWeb = 'https://play.google.com/store/apps/details?id=$_identifiant';

MagasinService _magasin(_LanceurFeint lanceur) =>
    MagasinService(identifiantApplication: _identifiant, lancer: lanceur.call);

void main() {
  test('ouvre le lien du magasin, et rien de plus', () async {
    final lanceur = _LanceurFeint([true]);
    final magasin = _magasin(lanceur);

    await magasin.ouvrirFiche();

    expect(
      lanceur.tentatives,
      [Uri.parse('market://details?id=com.arpendo.game')],
      reason:
          "l'application du magasin d'abord — elle ouvre la fiche "
          'directement, là où le navigateur ferait un détour',
    );
  });

  test('sans magasin installé, replie sur le lien web', () async {
    final lanceur = _LanceurFeint([false, true]);
    final magasin = _magasin(lanceur);

    await magasin.ouvrirFiche();

    expect(lanceur.tentatives.last, Uri.parse(_lienWeb));
  });

  test(
    'un refus de plateforme sur le premier lien n\'arrête pas le second',
    () async {
      // `launchUrl` lève quand aucune activité ne répond au schéma — c'est le
      // cas d'un émulateur sans Play Services, exactement celui que le repli
      // existe pour couvrir. Une exception non rattrapée le rendrait inerte.
      final lanceur = _LanceurFeint([Exception('aucune activité'), true]);
      final magasin = _magasin(lanceur);

      await magasin.ouvrirFiche();

      expect(lanceur.tentatives.last, Uri.parse(_lienWeb));
    },
  );

  test('les deux liens échouent : rien ne remonte', () async {
    // Le §11.2 : l'écran ne change pas, aucun message. Une exception qui
    // remonterait ici casserait le `onPressed` du bouton, donc le seul écran
    // dont le joueur ne peut pas sortir.
    // Les DEUX liens lèvent, pas seulement le second : avec un premier lien
    // qui rend `false`, le test resterait vert même sans clause de rattrapage
    // — l'exception ne serait jamais atteinte. Mesuré par mutation.
    final magasin = _magasin(
      _LanceurFeint([Exception('magasin'), Exception('navigateur')]),
    );

    await expectLater(magasin.ouvrirFiche(), completes);
  });
}
