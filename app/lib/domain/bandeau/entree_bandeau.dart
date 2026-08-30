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
  ///
  /// **C'est donc aussi ce qui identifie l'entrée pour l'affichage** — la
  /// ligne, pas son contenu. Deux entrées construites depuis la même ligne ne
  /// sont pas égales : la classe n'a ni `==` ni `hashCode`, et les fabriques
  /// de `lignes.dart` rendent un objet neuf à chaque appel, closures
  /// comprises. Un affichage décide donc de **rejouer sa transition** en
  /// comparant les priorités, jamais les objets, qui diffèrent à chaque
  /// reconstruction.
  ///
  /// Cela ne dit rien de son **contenu**, qui peut changer à rang constant : la
  /// ligne 8 porte un décompte à la seconde, la 13 un nombre de captures, la 6
  /// voit son action apparaître après trente secondes. Rendre le contenu reste
  /// affaire de reconstruction ordinaire ; seule la transition se décide sur la
  /// priorité.
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
  ///
  /// **À ne pas confondre avec [Severite.bloquant]**, que la spécification
  /// nomme du même mot : la sévérité décide du glyphe et de la couleur, ce
  /// drapeau décide de l'état « carte masquée » (§12.2).
  ///
  /// Dans la table du §2.4 telle qu'elle existe aujourd'hui, les deux
  /// coïncident : les trois seules lignes de sévérité `bloquant` — 1, 2 et 3 —
  /// sont exactement celles que le §12.2 nomme comme masquant la carte. Ils
  /// restent deux paramètres parce que la spécification les distingue, et
  /// parce que rien n'interdit une ligne future de gravité `bloquant` qui
  /// laisserait la carte vivre.
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
/// Un `assert` refuse en debug **deux entrées de même rang** — une bourde de
/// numérotation, puisqu'un rang identifie une ligne du §2.4. Il ne fait que
/// cela : la règle d'exclusivité du §2.4 est bien plus forte — « aucune
/// condition ne doit pouvoir être vraie en même temps qu'une condition plus
/// prioritaire » — et elle porte sur les **conditions**, que ce module ne voit
/// pas. Deux lignes dont les conditions se recouvrent passeront ici sans un
/// mot, et la mieux classée masquera l'autre ; c'est au domaine qui déclare
/// une ligne de garantir que sa condition exclut celles d'au-dessus. En
/// release, où l'`assert` ne s'exécute pas, deux entrées de même rang laissent
/// gagner la première rencontrée — un choix arbitraire, mais déterministe.
EntreeBandeau? resoudre(Iterable<EntreeBandeau> actives) {
  assert(
    actives.map((entree) => entree.priorite).toSet().length == actives.length,
    'Deux entrées portent le même rang : un rang identifie une ligne de la '
    'table de la spec UX §2.4, deux lignes ne peuvent pas partager le leur.',
  );
  if (actives.isEmpty) return null;
  return actives.reduce(
    (gagnante, entree) =>
        entree.priorite < gagnante.priorite ? entree : gagnante,
  );
}
