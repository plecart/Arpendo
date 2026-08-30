/// Les deux lignes de la table du §2.4 qui n'ont pas encore de domaine
/// propriétaire — le réseau ira à Territoire, la mise à jour à la séquence de
/// démarrage.
///
/// **Ce fichier n'est pas le registre des lignes du bandeau, et il ne le
/// deviendra pas** : une ligne se déclare dans le domaine qui possède sa
/// condition. Le pourquoi et la marche à suivre sont dans `app/README.md`,
/// section « Composants uniques ».
///
/// Aucune de ces fabriques n'évalue sa condition : c'est la racine de
/// composition qui décide si une ligne est active, et qui joint celles qui le
/// sont à [resoudre].
library;

import 'entree_bandeau.dart';

/// Ligne 5 — le téléphone n'a aucune interface réseau active (§2.4).
///
/// Sans action : il n'y a rien à faire d'autre que d'attendre, et le dire est
/// exactement ce que le texte fait.
///
/// ponytail: sa condition est incomplète, et volontairement — la table du §2.4
/// borne la ligne 5 à une « coupure de moins de cinq minutes », et cette borne
/// manque ici, faute d'horloge de coupure. **À reprendre par qui livrera la
/// ligne 6 (« Coupure de plus de 5 min »), dans le même lot**, sans quoi les
/// deux lignes seront actives ensemble au-delà de cinq minutes et [resoudre]
/// rendra la 5, qui masquera la 6 **en silence**. La spec veut l'inverse —
/// « l'entrée 6 … prend la main sur les deux » — mais elle ne l'obtient pas par
/// le rang : 6 est un rang **plus haut** que 5, donc une priorité **moindre**,
/// puisque le rang le plus bas gagne. Elle l'obtient par l'exclusivité des
/// conditions, qui rend la ligne 5 inactive passé le seuil. Et rien ne le
/// signalera : l'`assert` de [resoudre] ne voit que les collisions de rang, pas
/// les conditions qui se recouvrent.
EntreeBandeau ligneReseauAbsent() => EntreeBandeau(
  priorite: 5,
  severite: Severite.avertissement,
  texte: (l10n) => l10n.bandeauPasDeReseau,
);

/// Ligne 12 — une version plus récente est recommandée (§2.4, §11.2).
///
/// [onMettreAJour] ouvre la fiche du magasin, [onFermer] masque le bandeau
/// jusqu'à la version suivante. Les deux sont fournis par l'appelant : la
/// condition de cette ligne — « recommandée non atteinte et non fermée pour
/// cette version » — et la persistance de la fermeture appartiennent à la
/// séquence de démarrage, pas à la table des lignes.
EntreeBandeau ligneMiseAJourRecommandee({
  required void Function() onMettreAJour,
  required void Function() onFermer,
}) => EntreeBandeau(
  priorite: 12,
  severite: Severite.info,
  texte: (l10n) => l10n.bandeauMiseAJourDisponible,
  actions: [
    ActionBandeau(
      libelle: (l10n) => l10n.bandeauActionMettreAJour,
      onPressed: onMettreAJour,
    ),
    ActionBandeau(
      libelle: (l10n) => l10n.bandeauActionFermer,
      onPressed: onFermer,
    ),
  ],
);
