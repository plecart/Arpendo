import 'dart:async';

import 'package:arpendo/data/services/connectivity_service.dart';
import 'package:connectivity_plus_platform_interface/connectivity_plus_platform_interface.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// Plateforme feinte : sa sonde et son flux sont ceux que le test lui donne.
class _PlateformeFeinte extends ConnectivityPlatform {
  _PlateformeFeinte(this._sonde, this._evenements);

  final Future<List<ConnectivityResult>> Function() _sonde;
  final Stream<List<ConnectivityResult>> _evenements;

  @override
  Future<List<ConnectivityResult>> checkConnectivity() => _sonde();

  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged => _evenements;
}

/// Une sonde qui fait rougir le test si on l'appelle.
///
/// `enLigne()` s'alimente au flux d'événements, jamais à la sonde ponctuelle :
/// la passer aux tests de flux prouve cette séparation au lieu de la supposer.
Future<List<ConnectivityResult>> _jamaisSondee() =>
    throw StateError('enLigne() ne doit pas sonder la plateforme');

/// Rend un service dont le plugin répond par [sonde] — résultat ou exception —
/// et émet [evenements] sur son flux de connectivité.
///
/// Couture prévue par les plugins fédérés : `Connectivity()` relit
/// `ConnectivityPlatform.instance` à chaque appel, sans canal natif. Cette
/// instance est un état global du processus ; le test la restaure en sortant.
ConnectivityService _service(
  Future<List<ConnectivityResult>> Function() sonde, {
  Stream<List<ConnectivityResult>> evenements = const Stream.empty(),
}) {
  final precedente = ConnectivityPlatform.instance;
  ConnectivityPlatform.instance = _PlateformeFeinte(sonde, evenements);
  addTearDown(() => ConnectivityPlatform.instance = precedente);
  return ConnectivityService();
}

/// Un flux qui rejoue [evenements] : une liste d'interfaces s'émet, tout autre
/// objet s'émet en erreur — ce qu'aucun `async*` ne sait faire sans se clore.
Stream<List<ConnectivityResult>> _flux(Iterable<Object> evenements) {
  final controleur = StreamController<List<ConnectivityResult>>();
  for (final evenement in evenements) {
    if (evenement is List<ConnectivityResult>) {
      controleur.add(evenement);
    } else {
      controleur.addError(evenement);
    }
  }
  controleur.close();
  return controleur.stream;
}

void main() {
  test('une interface active met en ligne', () async {
    final service = _service(() async => const [ConnectivityResult.mobile]);

    expect(await service.isOnline(), isTrue);
  });

  test('aucune interface met hors ligne', () async {
    final service = _service(() async => const [ConnectivityResult.none]);

    expect(await service.isOnline(), isFalse);
  });

  test('un incident de plateforme présume le réseau présent', () async {
    final service = _service(() async => throw PlatformException(code: 'x'));

    expect(await service.isOnline(), isTrue);
  });

  test('un plugin absent présume le réseau présent', () async {
    final service = _service(() async => throw MissingPluginException('x'));

    expect(await service.isOnline(), isTrue);
  });

  test('toute autre exception remonte au lieu de mentir', () async {
    // Une `Exception` non liée à la plateforme, et pas une `Error` : `Error`
    // n'a jamais été rattrapée par `on Exception`, un tel test resterait vert
    // sans rien prouver. C'est bien la famille `Exception` qui était avalée.
    final service = _service(() async => throw const FormatException());

    await expectLater(service.isOnline(), throwsFormatException);
  });

  test("le flux n'émet rien quand l'état ne change pas", () async {
    // Deux interfaces **différentes**, toutes deux en ligne : le `distinct` que
    // le plugin applique lui-même les laisse passer toutes les deux, parce
    // qu'il compare des listes d'interfaces. Seul le nôtre, qui compare l'état
    // en ligne, les réduit à un seul événement.
    final service = _service(
      _jamaisSondee,
      evenements: _flux(const [
        [ConnectivityResult.wifi],
        [ConnectivityResult.mobile],
      ]),
    );

    await expectLater(service.enLigne(), emitsInOrder([true, emitsDone]));
  });

  test('le flux émet à chaque bascule', () async {
    final service = _service(
      _jamaisSondee,
      evenements: _flux(const [
        [ConnectivityResult.wifi],
        [ConnectivityResult.none],
        [ConnectivityResult.wifi],
      ]),
    );

    await expectLater(
      service.enLigne(),
      emitsInOrder([true, false, true, emitsDone]),
    );
  });

  test(
    'un incident de plateforme sur le flux présume le réseau présent',
    () async {
      final service = _service(
        _jamaisSondee,
        evenements: _flux([
          PlatformException(code: 'x'),
          const [ConnectivityResult.none],
        ]),
      );

      await expectLater(
        service.enLigne(),
        emitsInOrder([true, false, emitsDone]),
      );
    },
  );

  test('toute autre erreur du flux remonte au lieu de mentir', () async {
    final service = _service(
      _jamaisSondee,
      evenements: _flux(const [FormatException()]),
    );

    await expectLater(
      service.enLigne(),
      emitsInOrder([emitsError(isFormatException), emitsDone]),
    );
  });
}
