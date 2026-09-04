import 'package:arpendo/domain/bandeau/entree_bandeau.dart';
import 'package:arpendo/domain/bandeau/lignes.dart';
import 'package:arpendo/l10n/generated/app_localizations_fr.dart';
import 'package:flutter_test/flutter_test.dart';

/// Les textes tels que la locale livrée les rend.
///
/// La classe générée s'instancie sans arbre de widgets : ces lignes se
/// vérifient donc en test unitaire, sans rien monter. C'est ce qui permet de
/// comparer le texte rendu à celui que la spec arrête, mot pour mot.
final fr = AppLocalizationsFr();

void main() {
  test('la ligne réseau prend le pas sur la mise à jour', () {
    final actives = [
      ligneMiseAJourRecommandee(onMettreAJour: () {}),
      ligneReseauAbsent(),
    ];

    expect(resoudre(actives)?.texte(fr), fr.bandeauPasDeReseau);
  });

  test('la ligne réseau porte le texte et la sévérité du §2.4', () {
    final ligne = ligneReseauAbsent();

    expect(ligne.texte(fr), 'Pas de réseau. La reprise est automatique.');
    expect(ligne.severite, Severite.avertissement);
    expect(ligne.actions, isEmpty);
    expect(ligne.bloquant, isFalse);
  });

  test('la ligne de mise à jour porte le texte et la sévérité du §2.4', () {
    final ligne = ligneMiseAJourRecommandee(onMettreAJour: () {});

    expect(ligne.texte(fr), 'Une nouvelle version est disponible.');
    expect(ligne.severite, Severite.info);
    expect(ligne.bloquant, isFalse);
  });

  test('la mise à jour porte son geste sur son message, sans bouton', () {
    // « Une nouvelle version est disponible. » et « Mettre à jour » disaient
    // la même chose deux fois. Le message est le lien (§2.4).
    var miseAJour = 0;
    final ligne = ligneMiseAJourRecommandee(onMettreAJour: () => miseAJour++);

    expect(ligne.actions, isEmpty);
    expect(ligne.onTexteTape, isNotNull);

    ligne.onTexteTape!();
    expect(miseAJour, 1);
  });

  test('un message tapable et des boutons ne coexistent pas', () {
    // Les deux offriraient le même geste deux fois, et doubleraient la cible
    // tactile à tenir. L'`assert` du modèle le refuse en debug.
    expect(
      () => EntreeBandeau(
        priorite: 99,
        severite: Severite.info,
        texte: (_) => 'peu importe',
        actions: [ActionBandeau(libelle: (_) => 'Agir', onPressed: () {})],
        onTexteTape: () {},
      ),
      throwsA(isA<AssertionError>()),
    );
  });
}
