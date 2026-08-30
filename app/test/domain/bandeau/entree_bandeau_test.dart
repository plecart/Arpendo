import 'package:arpendo/domain/bandeau/entree_bandeau.dart';
import 'package:flutter_test/flutter_test.dart';

/// Une entrée dont seule la priorité compte pour le test qui l'utilise.
///
/// Le texte est un littéral : le module ne connaît pas les textes de
/// l'interface, il ne fait que transporter la fonction qui les résoudra. C'est
/// aussi ce qui rend ces tests indépendants de l'ARB.
EntreeBandeau _prioritaire(int priorite) => EntreeBandeau(
  priorite: priorite,
  severite: Severite.info,
  texte: (_) => 'peu importe',
);

void main() {
  test(
    'plusieurs conditions vraies : seule la plus prioritaire est rendue',
    () {
      final urgente = _prioritaire(5);

      final resolue = resoudre([_prioritaire(12), urgente, _prioritaire(9)]);

      expect(resolue, same(urgente));
    },
  );

  test('aucune condition vraie : aucun bandeau', () {
    expect(resoudre(const <EntreeBandeau>[]), isNull);
  });

  test('une entrée déclarée hors du module concourt comme les autres', () {
    // Le point de la spec §2.4 : un domaine ajoute sa ligne chez lui, sans
    // qu'une ligne de `resoudre` change. Cette entrée-ci n'existe nulle part
    // dans `lib/` — elle est inventée ici, et elle gagne quand même.
    final inventee = _prioritaire(3);

    expect(resoudre([_prioritaire(5), inventee]), same(inventee));
  });

  test('deux entrées ne peuvent pas porter le même rang', () {
    expect(
      () => resoudre([_prioritaire(5), _prioritaire(5)]),
      throwsA(isA<AssertionError>()),
    );
  });

  test('une entrée refuse plus de deux actions', () {
    final action = ActionBandeau(libelle: (_) => 'agir', onPressed: () {});

    expect(
      () => EntreeBandeau(
        priorite: 1,
        severite: Severite.info,
        texte: (_) => 'peu importe',
        actions: [action, action, action],
      ),
      throwsA(isA<AssertionError>()),
    );
  });
}
