import 'dart:async';

import 'package:arpendo/data/services/api_exception.dart';
import 'package:arpendo/data/services/connectivity_service.dart';
import 'package:arpendo/data/services/version_client.dart';
import 'package:arpendo/ui/demarrage/demarrage_view_model.dart';
import 'package:arpendo/ui/demarrage/etat_demarrage.dart';
import 'package:flutter_test/flutter_test.dart';

/// Client de version qui rend [reponse] — ou lève, si c'est une erreur.
class _VersionsFigees implements VersionClient {
  _VersionsFigees(this.reponse);

  Object reponse;
  int appels = 0;

  @override
  Future<Versions> lire() async {
    appels++;
    final r = reponse;
    if (r is Versions) return r;
    throw r as Exception;
  }
}

/// Connectivité pilotée par le test : état initial + flux à la main.
class _ConnectivitePilotee implements ConnectivityService {
  _ConnectivitePilotee({this.initial = true});

  final bool initial;
  final controleur = StreamController<bool>.broadcast(sync: true);
  int lecturesInitiales = 0;

  @override
  Future<bool> isOnline() async {
    lecturesInitiales++;
    return initial;
  }

  @override
  Stream<bool> enLigne() => controleur.stream;
}

/// Lecture initiale périmée (« en ligne ») ; flux émettant l'état frais
/// (« hors ligne ») **synchroniquement à l'abonnement** — aucune horloge,
/// donc aucun ordonnanceur chargé ne peut inverser la course : dans l'ordre
/// livré l'événement arrive après la lecture et la corrige ; dans l'ordre
/// inversé la lecture, résolue après, écrase l'événement.
class _ConnectiviteRetardee implements ConnectivityService {
  @override
  Future<bool> isOnline() async => true;

  @override
  Stream<bool> enLigne() {
    final controleur = StreamController<bool>(sync: true);
    controleur.onListen = () => controleur.add(false);
    return controleur.stream;
  }
}

/// Nombre d'ouvertures du magasin demandées par le modèle.
late int ouverturesMagasin;

DemarrageViewModel _modele({
  Object? versions,
  _ConnectivitePilotee? connectivite,
  int build = 5,
}) {
  final vm = DemarrageViewModel(
    versions: _VersionsFigees(
      versions ?? const Versions(minBuild: 1, recommendedBuild: 1),
    ),
    connectivite: connectivite ?? _ConnectivitePilotee(),
    buildActuel: build,
    ouvrirMagasin: () => ouverturesMagasin++,
  );
  addTearDown(vm.dispose);
  return vm;
}

void main() {
  setUp(() => ouverturesMagasin = 0);

  test('build au niveau : Pret sans mise à jour recommandée', () async {
    final vm = _modele(
      versions: const Versions(minBuild: 3, recommendedBuild: 5),
      build: 5,
    );

    await vm.demarrer();

    expect(vm.etat, const Pret(miseAJourRecommandee: false));
  });

  test(
    'build sous le recommandé : Pret avec mise à jour recommandée',
    () async {
      final vm = _modele(
        versions: const Versions(minBuild: 3, recommendedBuild: 7),
        build: 5,
      );

      await vm.demarrer();

      expect(vm.etat, const Pret(miseAJourRecommandee: true));
    },
  );

  test('build sous le minimal : MiseAJourRequise', () async {
    final vm = _modele(
      versions: const Versions(minBuild: 6, recommendedBuild: 7),
      build: 5,
    );

    await vm.demarrer();

    expect(vm.etat, const MiseAJourRequise());
  });

  for (final (nom, panne) in <(String, Exception)>[
    ('hors ligne', const HorsLigne()),
    ('serveur injoignable', const ServeurInjoignable()),
    ('erreur http', const ErreurHttp(503)),
    ('réponse invalide', const ReponseInvalide()),
  ]) {
    test('échec de la lecture — $nom — : Injoignable', () async {
      final vm = _modele(versions: panne);

      await vm.demarrer();

      expect(vm.etat, const Injoignable());
    });
  }

  test('reessayer relance la lecture et repasse par Verification', () async {
    final versions = _VersionsFigees(const ServeurInjoignable());
    final vm = DemarrageViewModel(
      versions: versions,
      connectivite: _ConnectivitePilotee(),
      buildActuel: 5,
      ouvrirMagasin: () {},
    );
    addTearDown(vm.dispose);
    await vm.demarrer();
    expect(vm.etat, const Injoignable());

    final etatsVus = <EtatDemarrage>[];
    vm.addListener(() => etatsVus.add(vm.etat));
    versions.reponse = const Versions(minBuild: 1, recommendedBuild: 1);
    await vm.reessayer();

    expect(versions.appels, 2);
    expect(etatsVus.first, const Verification());
    expect(vm.etat, const Pret(miseAJourRecommandee: false));
  });

  test(
    "l'état réseau initial vient d'isOnline(), avant l'abonnement",
    () async {
      // Sur Android, le flux n'émet pas de façon fiable l'état courant à
      // l'abonnement : un ViewModel qui ne fait que s'abonner a un état réseau
      // initial indéfini (réconciliation PR #74).
      final connectivite = _ConnectivitePilotee(initial: false);
      final vm = _modele(connectivite: connectivite);

      await vm.demarrer();

      expect(connectivite.lecturesInitiales, 1);
      expect(vm.entreeBandeau?.priorite, 5, reason: 'hors ligne → ligne 5');
    },
  );

  test('le flux réseau met à jour le bandeau et notifie', () async {
    final connectivite = _ConnectivitePilotee(initial: false);
    final vm = _modele(connectivite: connectivite);
    await vm.demarrer();
    var notifications = 0;
    vm.addListener(() => notifications++);

    connectivite.controleur.add(true);

    expect(vm.entreeBandeau, isNull);
    expect(notifications, 1);
  });

  test("un événement du flux arrivé pendant demarrer() n'est pas écrasé par isOnline()", () async {
    // Si demarrer() s'abonnait AVANT d'attendre isOnline(), la lecture
    // initiale, plus ancienne, écraserait l'événement plus récent — bandeau
    // absent alors que le téléphone est hors ligne. La doublure émet à
    // l'abonnement même : la course est jouée sans horloge, le verdict ne
    // dépend pas de la charge de la machine.
    final vm = DemarrageViewModel(
      versions: _VersionsFigees(
        const Versions(minBuild: 1, recommendedBuild: 1),
      ),
      connectivite: _ConnectiviteRetardee(),
      buildActuel: 5,
      ouvrirMagasin: () {},
    );
    addTearDown(vm.dispose);

    await vm.demarrer();

    expect(vm.entreeBandeau?.priorite, 5);
  });

  test("dispose ferme l'abonnement au flux réseau", () async {
    final connectivite = _ConnectivitePilotee();
    final vm = DemarrageViewModel(
      versions: _VersionsFigees(
        const Versions(minBuild: 1, recommendedBuild: 1),
      ),
      connectivite: connectivite,
      buildActuel: 5,
      ouvrirMagasin: () {},
    );
    await vm.demarrer();
    expect(connectivite.controleur.hasListener, isTrue);

    vm.dispose();

    expect(connectivite.controleur.hasListener, isFalse);
  });

  group('bandeau 12 — mise à jour recommandée', () {
    const sousLeRecommande = Versions(minBuild: 1, recommendedBuild: 9);

    test('build sous le recommandé : le bandeau 12 est proposé', () async {
      final vm = _modele(versions: sousLeRecommande);

      await vm.demarrer();

      expect(vm.entreeBandeau?.priorite, 12);
    });

    test('le bandeau 12 porte une seule action, sans « Fermer »', () async {
      // La fermeture — et la persistance qu'elle suppose — sont repoussées
      // après le MVP (cadrage §20). Une action unique tient sur la rangée du
      // message (§2.4), ce qui est aussi ce que la ligne 12 veut dire : la
      // mise à jour est recommandée, pas imposée.
      final vm = _modele(versions: sousLeRecommande);

      await vm.demarrer();

      expect(vm.entreeBandeau!.actions, hasLength(1));
    });

    test('un échec après une lecture réussie efface la proposition', () async {
      // Sinon une recommandation lue avant un « Réessayer » raté continuerait
      // de piloter le bandeau 12 par-dessus l'écran de panne — deux messages
      // dont l'un est la cause de l'autre (§2.4).
      final versions = _VersionsFigees(sousLeRecommande);
      final vm = DemarrageViewModel(
        versions: versions,
        connectivite: _ConnectivitePilotee(),
        buildActuel: 5,
        ouvrirMagasin: () {},
      );
      addTearDown(vm.dispose);
      await vm.demarrer();
      expect(vm.entreeBandeau?.priorite, 12);

      versions.reponse = const ServeurInjoignable();
      await vm.reessayer();

      expect(vm.etat, const Injoignable());
      expect(vm.entreeBandeau, isNull);
    });

    test('hors ligne, la ligne 5 masque la 12', () async {
      // Règle d'unicité du §2.4 : la plus prioritaire gagne, et le rang le
      // plus bas est le plus prioritaire. Sans réseau, proposer une mise à
      // jour qu'on ne peut pas télécharger serait une impasse.
      final vm = _modele(
        versions: sousLeRecommande,
        connectivite: _ConnectivitePilotee(initial: false),
      );

      await vm.demarrer();

      expect(vm.entreeBandeau?.priorite, 5);
    });

    test('« Mettre à jour » ouvre la fiche du magasin', () async {
      final vm = _modele(versions: sousLeRecommande);
      await vm.demarrer();

      vm.entreeBandeau!.actions.first.onPressed();

      expect(ouverturesMagasin, 1);
    });
  });
}
