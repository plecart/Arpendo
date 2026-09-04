import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../data/services/api_exception.dart';
import '../../data/services/connectivity_service.dart';
import '../../data/services/preferences_service.dart';
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
/// [ConnectivityService.enLigne]. [entreeBandeau] rend les deux lignes du
/// §2.4 que ce domaine possède — la 5 hors ligne, la 12 quand une mise à jour
/// est recommandée et n'a pas été écartée — et [resoudre] arbitre entre elles.
class DemarrageViewModel extends ChangeNotifier {
  /// Crée le modèle ; rien ne part vers le réseau avant [demarrer].
  DemarrageViewModel({
    required this._versions,
    required this._connectivite,
    required this._buildActuel,
    required this._preferences,
    required this._ouvrirMagasin,
  });

  final VersionClient _versions;
  final ConnectivityService _connectivite;
  final PreferencesService _preferences;

  /// Emmène le joueur vers la fiche du magasin — l'action « Mettre à jour »
  /// de la ligne 12. Le modèle ne sait pas comment : la racine branche le
  /// service, ce qui garde ce fichier hors de toute affaire de plateforme.
  final VoidCallback _ouvrirMagasin;

  /// Le numéro de build installé — l'entier de `version: x.y.z+N` du pubspec.
  final int _buildActuel;

  /// Le seuil recommandé publié par le serveur, dès qu'il a été lu.
  ///
  /// Nul tant que `/version` n'a pas répondu — et c'est ce qui rend la
  /// condition de la ligne 12 fausse pendant la vérification, sans avoir à
  /// interroger l'état.
  int? _buildRecommande;

  EtatDemarrage _etat = const Verification();
  bool _enLigne = true;
  bool _demarre = false;
  StreamSubscription<bool>? _abonnementReseau;

  /// L'état courant de la séquence.
  EtatDemarrage get etat => _etat;

  /// La ligne de bandeau à afficher, ou `null` si aucune n'est active.
  ///
  /// Deux conditions à ce stade — hors ligne (ligne 5) et mise à jour
  /// recommandée non fermée (ligne 12) ; [resoudre] arbitre, et c'est lui qui
  /// fait gagner la 5 quand les deux sont vraies. Toute ligne future s'ajoute
  /// à la liste, sans toucher à ce `get`.
  EntreeBandeau? get entreeBandeau => resoudre([
    if (!_enLigne) ligneReseauAbsent(),
    if (_miseAJourAProposer)
      ligneMiseAJourRecommandee(
        onMettreAJour: _ouvrirMagasin,
        onFermer: fermerMiseAJour,
      ),
  ]);

  /// Vrai quand la séquence a abouti sur un build sous le recommandé **et**
  /// que le joueur n'a pas déjà fermé le bandeau pour ce build-là (§11.2).
  ///
  /// **L'état compte autant que les nombres.** La condition n'est vraie qu'en
  /// [Pret] : proposer une mise à jour par-dessus « Le serveur ne répond
  /// pas. » ferait cohabiter deux messages dont l'un est la cause de l'autre,
  /// ce que la règle d'unicité du §2.4 refuse. C'est aussi ce qui empêche une
  /// recommandation lue avant un « Réessayer » raté de survivre à l'échec.
  ///
  /// La comparaison est un `>` et non un `!=` : ce qui a été écarté, c'est un
  /// **seuil**, pas un identifiant. Un serveur qui redescendrait sa
  /// recommandation ne doit pas rouvrir un bandeau déjà refusé.
  bool get _miseAJourAProposer {
    final etat = _etat;
    final recommande = _buildRecommande;
    if (etat is! Pret || !etat.miseAJourRecommandee || recommande == null) {
      return false;
    }
    final ecarte = _preferences.buildRecommandeEcarte();
    return ecarte == null || recommande > ecarte;
  }

  /// Masque le bandeau 12 jusqu'à une recommandation plus récente.
  ///
  /// La fermeture est **persistée avant** la notification : un redémarrage
  /// entre les deux laisserait le joueur avec un bandeau qu'il croit avoir
  /// fermé.
  Future<void> fermerMiseAJour() async {
    final recommande = _buildRecommande;
    if (recommande == null) return;
    await _preferences.ecarterBuildRecommande(recommande);
    notifyListeners();
  }

  /// Lance la séquence : état réseau initial, abonnement au flux, contrôle
  /// de version. À appeler une fois, par la racine de composition.
  Future<void> demarrer() async {
    // Drapeau posé AVANT le premier `await` : deux appels concurrents
    // verraient tous deux un `_abonnementReseau` encore nul et fuiraient un
    // abonnement — l'assert doit fermer aussi ce chemin-là.
    assert(
      !_demarre,
      "demarrer() ne se lance qu'une fois — un second appel fuirait le "
      'premier abonnement au flux réseau.',
    );
    _demarre = true;
    // La lecture initiale PRÉCÈDE l'abonnement, et l'ordre est un invariant :
    // inversé, une lecture lente écraserait un événement du flux plus récent
    // — l'état réseau reculerait dans le temps (garde dans les tests).
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
    _buildRecommande = versions.recommendedBuild;
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
