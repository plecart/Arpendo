import 'package:arpendo/data/services/preferences_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<PreferencesService> _service([
  Map<String, Object> initiales = const {},
]) async {
  SharedPreferences.setMockInitialValues(initiales);
  return PreferencesService(await SharedPreferences.getInstance());
}

void main() {
  test("le build écarté est relu à l'identique", () async {
    final prefs = await _service();

    await prefs.ecarterBuildRecommande(42);

    expect(prefs.buildRecommandeEcarte(), 42);
  });

  test('installation neuve : aucun build écarté', () async {
    final prefs = await _service();

    expect(prefs.buildRecommandeEcarte(), isNull);
  });

  test('une fermeture survit au redémarrage', () async {
    // `setMockInitialValues` simule le stockage **déjà sur le disque** : c'est
    // le seul montage qui exerce la relecture au lancement suivant, celle dont
    // dépend « le bandeau ne revient pas pour la même version » (§11.2). La
    // clé se donne **sans** le préfixe `flutter.` : le plugin le pose
    // lui-même, et l'écrire ici couplerait le test à un `static` mutable.
    final prefs = await _service({'build_recommande_ecarte': 7});

    expect(prefs.buildRecommandeEcarte(), 7);
  });
}
