import 'package:flutter/foundation.dart';

import '../../l10n/generated/app_localizations.dart';

/// Le degré de gravité d'une entrée de bandeau — spec UX §2.4.
///
/// La sévérité est portée par la **forme** du glyphe (cercle, triangle,
/// octogone) et non par la couleur seule : les trois silhouettes restent
/// lisibles en niveaux de gris, à petite taille, et pour un daltonien. La
/// correspondance vers un glyphe et une couleur appartient à la couche
/// d'interface ; ce module n'en connaît rien, et c'est ce qui lui permet de
/// servir aussi la notification permanente d'Android (§10.2), qui n'a pas de
/// widget.
enum Severite {
  /// Information — la partie continue normalement.
  info,

  /// Avertissement — quelque chose ne marche pas, le jeu reste jouable.
  avertissement,

  /// Bloquant — le jeu ne peut pas continuer tant que la cause dure.
  bloquant,
}

/// Un bouton texte d'une entrée de bandeau — au plus deux par entrée (§2.4).
@immutable
class ActionBandeau {
  /// Crée l'action de [libelle], qui exécute [onPressed] quand on l'actionne.
  const ActionBandeau({required this.libelle, required this.onPressed});

  /// Le libellé du bouton, **résolu depuis la localisation**.
  ///
  /// Une fonction et non une chaîne : l'entrée est construite une fois, hors
  /// de tout `BuildContext`, alors que le texte dépend de la locale ambiante
  /// au moment du rendu (cadrage §12.6 — aucune chaîne en dur).
  final String Function(AppLocalizations) libelle;

  /// Ce que l'action déclenche. Fournie par l'appelant qui possède la ligne.
  final void Function() onPressed;
}

/// Une ligne de la table de priorité du bandeau — spec UX §2.4.
///
/// Une entrée est **la description d'un message à afficher**, pas la condition
/// qui le déclenche : c'est le domaine propriétaire de la ligne qui décide si
/// elle est active, et qui la remet à [resoudre] quand elle l'est.
///
/// ```dart
/// EntreeBandeau(
///   priorite: 5,
///   severite: Severite.avertissement,
///   texte: (l10n) => l10n.bandeauPasDeReseau,
/// );
/// ```
@immutable
class EntreeBandeau {
  /// Crée l'entrée de [priorite], de gravité [severite], portant [texte].
  ///
  /// [actions] en compte zéro, une ou deux — au-delà, l'anatomie du §2.4 n'a
  /// plus la place de les rendre, et un `assert` le refuse en debug. [bloquant]
  /// dit que la carte doit être masquée et les interactions de jeu coupées
  /// (§12.2) ; l'entrée le **porte comme donnée**, elle ne le réalise pas.
  const EntreeBandeau({
    required this.priorite,
    required this.severite,
    required this.texte,
    this.actions = const [],
    this.bloquant = false,
  }) : assert(
         actions.length <= 2,
         "L'anatomie du bandeau (spec UX §2.4) admet zéro à deux boutons "
         'texte, pas davantage.',
       );

  /// Le rang de la ligne dans la table du §2.4 — **le plus bas gagne**.
  ///
  /// Les rangs ne se renumérotent pas : ils sont l'identité des lignes dans la
  /// spécification, et une ligne ajoutée plus tard prend un rang libre.
  final int priorite;

  /// La gravité, qui décide du glyphe et de la couleur au rendu.
  final Severite severite;

  /// Le message, **résolu depuis la localisation** — voir [ActionBandeau.libelle].
  ///
  /// Un message est **une seule** valeur de l'ARB, avec ses placeholders s'il
  /// en faut : le garde `fr-XA` rougit sur un texte composé de deux valeurs
  /// autour d'un séparateur écrit dans le code.
  final String Function(AppLocalizations) texte;

  /// Les boutons texte, de zéro à deux, dans leur ordre d'affichage.
  final List<ActionBandeau> actions;

  /// Vrai si l'affichage de cette entrée masque la carte et coupe le jeu.
  final bool bloquant;
}

/// L'unique entrée à afficher parmi celles dont la condition est vraie.
///
/// Rend la plus prioritaire de [actives], ou `null` si aucune ne l'est. C'est
/// la **règle d'unicité** du §2.4 : un seul bandeau à la fois, parce que le
/// budget vertical du §2.2 ne tient pas trois bandeaux, et parce que celui du
/// haut est toujours la cause des suivants.
///
/// **Ajouter une ligne ne touche pas cette fonction** : un domaine déclare son
/// entrée chez lui et la joint à [actives]. Il n'existe volontairement aucune
/// énumération centrale des conditions, qu'une ligne nouvelle devrait modifier.
///
/// Deux entrées de même priorité violeraient la règle d'exclusivité du §2.4 —
/// « aucune condition ne doit pouvoir être vraie en même temps qu'une condition
/// plus prioritaire ». Un `assert` les refuse en debug ; en release, le choix
/// reste déterministe (la première rencontrée).
EntreeBandeau? resoudre(Iterable<EntreeBandeau> actives) {
  assert(
    actives.map((entree) => entree.priorite).toSet().length == actives.length,
    "Deux entrées de même priorité : la règle d'exclusivité de la spec UX "
    '§2.4 veut que deux conditions ne soient jamais vraies ensemble.',
  );
  if (actives.isEmpty) return null;
  return actives.reduce(
    (gagnante, entree) =>
        entree.priorite < gagnante.priorite ? entree : gagnante,
  );
}
