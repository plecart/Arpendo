import 'package:arpendo/data/services/connectivity_service.dart';
import 'package:connectivity_plus_platform_interface/connectivity_plus_platform_interface.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// Plateforme feinte : sa sonde est celle que le test lui donne.
class _PlateformeFeinte extends ConnectivityPlatform {
  _PlateformeFeinte(this._sonde);

  final Future<List<ConnectivityResult>> Function() _sonde;

  @override
  Future<List<ConnectivityResult>> checkConnectivity() => _sonde();
}

/// Rend un service dont le plugin répond par [sonde] — résultat ou exception.
///
/// Couture prévue par les plugins fédérés : `Connectivity()` relit
/// `ConnectivityPlatform.instance` à chaque appel, sans canal natif. Cette
/// instance est un état global du processus ; le test la restaure en sortant.
ConnectivityService _service(
  Future<List<ConnectivityResult>> Function() sonde,
) {
  final precedente = ConnectivityPlatform.instance;
  ConnectivityPlatform.instance = _PlateformeFeinte(sonde);
  addTearDown(() => ConnectivityPlatform.instance = precedente);
  return ConnectivityService();
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
}
