/// Les lignes de la table du §2.4 que cette application sait déjà former.
///
/// **Ce fichier n'est pas le registre des lignes du bandeau, et il ne le
/// deviendra pas.** Une ligne appartient au domaine qui possède sa condition —
/// les permissions, le territoire, la partie — et s'y déclare, sans que
/// [resoudre] ni ce fichier changent. Les deux ci-dessous n'ont pas encore de
/// domaine propriétaire : le réseau ira à Territoire avec la fenêtre de cinq
/// minutes (lignes 4 et 6), la mise à jour à la séquence de démarrage. Elles
/// déménageront chez eux quand ces domaines existeront.
///
/// Aucune n'évalue sa condition : c'est la racine de composition qui décide si
/// une ligne est active, et qui joint celles qui le sont à [resoudre].
library;

import 'entree_bandeau.dart';

/// Ligne 5 — le téléphone n'a aucune interface réseau active (§2.4).
///
/// Sans action : il n'y a rien à faire d'autre que d'attendre, et le dire est
/// exactement ce que le texte fait. La nuance « coupure de moins de cinq
/// minutes » de la table appartient à la ligne 6, plus prioritaire, qui prendra
/// la main quand Territoire la livrera — cette ligne-ci n'a donc pas d'horloge.
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
