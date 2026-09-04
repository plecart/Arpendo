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

  test('la mise à jour offre « Mettre à jour », et rien de plus', () {
    // Une seule action : la fermeture du bandeau est repoussée après le MVP
    // (cadrage §20). C'est aussi ce qui lui vaut de rester sur la rangée du
    // message plutôt que de descendre (§2.4).
    var miseAJour = 0;
    final ligne = ligneMiseAJourRecommandee(onMettreAJour: () => miseAJour++);

    expect(ligne.actions.map((action) => action.libelle(fr)), [
      'Mettre à jour',
    ]);
    ligne.actions.single.onPressed();
    expect(miseAJour, 1);
  });
}
