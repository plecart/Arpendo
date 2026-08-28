/// Dérive la locale de test `fr-XA` de la locale livrée `fr`.
///
/// `fr-XA` n'est ni maintenue à la main ni versionnée : `just l10n` la
/// régénère depuis `app_fr.arb` avant chaque `flutter gen-l10n`. Elle sert au
/// test de `test/l10n/fr_xa_test.dart`, qui y lit deux garanties d'un coup —
/// la tolérance de +30 % de longueur exigée par la spec UX §0, et l'absence de
/// chaîne en dur, qu'un texte sans marqueur trahit.
///
/// Usage : `dart run tool/allonger_arb.dart`, depuis `app/`.
library;

import 'dart:convert';
import 'dart:io';

/// Marqueur ouvrant toute valeur allongée.
const marqueurDebut = '⟦';

/// Marqueur fermant toute valeur allongée.
const marqueurFin = '⟧';

/// Allongement minimal appliqué à chaque valeur (spec UX §0).
const facteurAllongement = 0.3;

/// Caractère de remplissage.
///
/// Neutre à la lecture et absent des textes de l'interface : un débordement
/// qu'il provoque se voit, et il ne se confond avec aucun contenu réel.
const remplissage = '·';

/// ARB de la locale livrée, seule source versionnée des textes.
const cheminSource = 'lib/l10n/app_fr.arb';

/// ARB dérivé, réécrit à chaque `just l10n` et ignoré par git.
const cheminSortie = 'lib/l10n/app_fr_XA.arb';

/// Rend [valeur] allongée d'au moins [facteurAllongement] et encadrée des
/// marqueurs.
///
/// Le remplissage s'ajoute **après** le message et jamais dedans : les
/// `{placeholders}` et la syntaxe ICU traversent intacts, quel que soit leur
/// nombre. Une valeur vide rend les deux marqueurs seuls.
String allonger(String valeur) {
  final ajout = remplissage * (valeur.length * facteurAllongement).ceil();
  return '$marqueurDebut$valeur$ajout$marqueurFin';
}

/// Rend la table ARB de `fr-XA` à partir de celle de `fr`.
///
/// `@@locale` bascule sur `fr_XA` — c'est lui que `gen-l10n` lit pour nommer la
/// locale. Les métadonnées `@clé` sont recopiées telles quelles : ce ne sont
/// pas des textes d'interface, et les allonger déclarerait des placeholders
/// différents des deux côtés. Toute autre entrée est un message, donc allongée.
Map<String, Object?> deriverXA(Map<String, Object?> fr) => {
  for (final MapEntry(:key, :value) in fr.entries)
    key: switch (key) {
      '@@locale' => 'fr_XA',
      _ when key.startsWith('@') => value,
      _ => allonger(value! as String),
    },
};

/// Réécrit [cheminSortie] depuis [cheminSource], relatifs au dossier `app/`.
void main() {
  final fr =
      jsonDecode(File(cheminSource).readAsStringSync()) as Map<String, Object?>;
  const encodeur = JsonEncoder.withIndent('  ');
  File(cheminSortie).writeAsStringSync('${encodeur.convert(deriverXA(fr))}\n');
}
