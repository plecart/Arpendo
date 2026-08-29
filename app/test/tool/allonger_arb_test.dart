import 'package:flutter_test/flutter_test.dart';

import '../../tool/allonger_arb.dart'
    show allonger, deriverXA, facteurAllongement, marqueurDebut, marqueurFin;

void main() {
  group('allonger', () {
    test('transcrit les 30 % de la spec, il ne les arbitre pas', () {
      expect(
        facteurAllongement,
        0.3,
        reason:
            'la spec UX §0 fixe la tolérance à +30 % et la constante la '
            'transcrit. Sans cet ancrage, le seuil du test suivrait la '
            'constante partout : la garantie pourrait disparaître sans '
            'faire rougir une seule assertion',
      );
    });

    test('rend une valeur au moins 30 % plus longue', () {
      const valeur = 'prends du terrain';

      expect(
        allonger(valeur).length,
        greaterThanOrEqualTo((valeur.length * (1 + facteurAllongement)).ceil()),
        reason:
            'la spec UX §0 exige que tout conteneur absorbe +30 % de longueur ; '
            'une locale qui allonge moins ne prouve rien',
      );
    });

    test('encadre la valeur des deux marqueurs', () {
      final allongee = allonger('prends du terrain');

      expect(allongee, startsWith(marqueurDebut));
      expect(allongee, endsWith(marqueurFin));
    });

    test('laisse les placeholders intacts', () {
      expect(
        allonger('il reste {minutes} minutes'),
        contains('{minutes}'),
        reason:
            'un placeholder abîmé casserait la génération ; le remplissage '
            "s'ajoute autour du message, jamais dedans",
      );
    });
  });

  group('deriverXA', () {
    test('bascule la locale déclarée', () {
      expect(deriverXA({'@@locale': 'fr'})['@@locale'], 'fr_XA');
    });

    test('recopie les métadonnées sans y toucher', () {
      const metadonnees = {'description': 'Cité — cadrage §1, ne pas modifier'};

      expect(
        deriverXA({'accroche': 'prends du terrain', '@accroche': metadonnees}),
        containsPair('@accroche', metadonnees),
        reason:
            'les descriptions et les placeholders doivent être lus à '
            "l'identique des deux côtés par `gen-l10n`",
      );
    });

    test('allonge les seules valeurs de texte', () {
      final xa = deriverXA({'accroche': 'prends du terrain'});

      expect(xa['accroche'], allonger('prends du terrain'));
    });
  });
}
