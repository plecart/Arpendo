import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../data/services/api_exception.dart';
import '../../data/services/connectivity_service.dart';
import '../../data/services/version_client.dart';
import '../../domain/bandeau/entree_bandeau.dart';
import '../../domain/bandeau/lignes.dart';
import 'etat_demarrage.dart';

/// Déroule la séquence de démarrage — premier ViewModel de l'application.
///
/// Contrôle de version **avant tout autre appel** (spec UX §2.1) : la seule
/// requête que ce modèle émet est `GET /version`, via [VersionClient]. La
/// racine de composition lit [etat] et fait un `switch` exhaustif → écran.
///
/// Il tient aussi l'état réseau : lu **une fois** par
/// [ConnectivityService.isOnline] — sur Android le flux n'émet pas de façon
/// fiable l'état courant à l'abonnement, un modèle qui ne ferait que
/// s'abonner aurait un état initial indéfini — puis suivi par
/// [ConnectivityService.enLigne]. Hors ligne, [entreeBandeau] rend la ligne 5
/// du §2.4 ; la ligne 12 (mise à jour recommandée) est câblée par le lot 2c
/// de #46, sa condition est déjà exposée par [Pret.miseAJourRecommandee].
class DemarrageViewModel extends ChangeNotifier {
  /// Crée le modèle ; rien ne part vers le réseau avant [demarrer].
  DemarrageViewModel({
    required this._versions,
    required this._connectivite,
    required this._buildActuel,
  });

  final VersionClient _versions;
  final ConnectivityService _connectivite;

  /// Le numéro de build installé — l'entier de `version: x.y.z+N` du pubspec.
  final int _buildActuel;

  EtatDemarrage _etat = const Verification();
  bool _enLigne = true;
  StreamSubscription<bool>? _abonnementReseau;

  /// L'état courant de la séquence.
  EtatDemarrage get etat => _etat;

  /// La ligne de bandeau à afficher, ou `null` si aucune n'est active.
  ///
  /// Une seule condition pour ce lot : hors ligne → ligne 5. Toute ligne
  /// future s'ajoute à la liste, [resoudre] arbitre.
  EntreeBandeau? get entreeBandeau =>
      resoudre([if (!_enLigne) ligneReseauAbsent()]);

  /// Lance la séquence : état réseau initial, abonnement au flux, contrôle
  /// de version. À appeler une fois, par la racine de composition.
  Future<void> demarrer() async {
    _enLigne = await _connectivite.isOnline();
    _abonnementReseau = _connectivite.enLigne().listen((enLigne) {
      if (enLigne == _enLigne) return;
      _enLigne = enLigne;
      notifyListeners();
    });
    await _verifier();
  }

  /// Relance le contrôle de version — l'action du bouton « Réessayer ».
  Future<void> reessayer() => _verifier();

  /// Interroge `/version` et classe le résultat.
  ///
  /// **Tout** échec d'api aboutit à [Injoignable] : au démarrage, la seule
  /// issue offerte au joueur est « Réessayer » (§2.1), et distinguer un 500
  /// d'un délai dépassé ne lui donnerait aucune action de plus. Le bandeau
  /// réseau (ligne 5), lui, dit déjà si le téléphone est hors ligne.
  Future<void> _verifier() async {
    _changer(const Verification());
    final Versions versions;
    try {
      versions = await _versions.lire();
    } on ApiException {
      _changer(const Injoignable());
      return;
    }
    if (_buildActuel < versions.minBuild) {
      _changer(const MiseAJourRequise());
    } else {
      _changer(
        Pret(miseAJourRecommandee: _buildActuel < versions.recommendedBuild),
      );
    }
  }

  void _changer(EtatDemarrage nouvel) {
    if (nouvel == _etat) return;
    _etat = nouvel;
    notifyListeners();
  }

  @override
  void dispose() {
    _abonnementReseau?.cancel();
    super.dispose();
  }
}
