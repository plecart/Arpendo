import 'package:flutter/material.dart';

/// Les plans de superposition d'un écran, du fond vers l'avant — spec UX §2.2.
///
/// Le rang `z` est **la** source de l'ordre de peinture, pas la position de la
/// valeur dans cette énumération : c'est ce qui permet d'insérer un plan
/// intermédiaire sans dépendre de l'endroit où on l'écrit. Les valeurs sont
/// espacées comme dans la spécification, précisément pour laisser la place à
/// ces insertions.
enum Calque {
  /// Carte Mapbox — occupe l'écran entier, **encoche comprise** (§2.3).
  carte(0),

  /// Pile d'activité (§7.2.1) — sous les contrôles, non interactive sauf sa
  /// ligne du bas.
  pileActivite(40),

  /// Contrôles flottants sur la carte : bouton d'action « Partie », Recentrer.
  controles(50),

  /// Puces de header sur l'écran Jeu (§7.1), barre de titre ailleurs.
  header(100),

  /// L'emplacement **unique** du bandeau (§2.4) — un seul à la fois.
  bandeau(200),

  /// Feuille modale (Partie, Paramètres) et son voile (§2.5).
  feuille(300),

  /// Modale de confirmation et son voile (§2.6).
  confirmation(400),

  /// Écran bloquant plein écran — mise à jour obligatoire (§11.2).
  bloquant(500);

  const Calque(this.z);

  /// Le rang de superposition du §2.2 : le plus grand se peint par-dessus.
  final int z;
}

/// L'unique `Stack` d'écran du projet — le contrat de mise en page §2.2 et §2.3.
///
/// Il porte deux garanties, que rien d'autre n'a à répéter :
///
/// 1. **L'ordre de peinture suit les [Calque]**, jamais l'ordre d'écriture. Un
///    écran énumère ses plans dans l'ordre qui se lit le mieux ; celui qui est
///    devant est décidé ici.
/// 2. **Tout plan sauf [Calque.carte] vit dans la safe area** (§2.3). La carte
///    occupe l'écran entier, encoche comprise — c'est ce qui donne l'immersion,
///    et rien d'interactif n'y vit. Laisser cette enveloppe à chaque écran
///    ferait deux endroits à tenir, et un oubli ne se verrait que sur un
///    téléphone à encoche.
///
/// Chaque plan se dimensionne et se positionne lui-même : la pile n'impose
/// aucune contrainte serrée, de sorte qu'un header qui flotte en haut et une
/// carte qui remplit l'écran cohabitent sans que l'un déforme l'autre. Une
/// carte se donne donc en `SizedBox.expand`, un header à sa hauteur propre.
///
/// ```dart
/// PileDeCalques(
///   children: {
///     Calque.header: const HeaderDePartie(),
///     Calque.carte: const SizedBox.expand(child: CarteMapbox()),
///     Calque.bandeau: EmplacementBandeau(entree: entree),
///   },
/// );
/// ```
class PileDeCalques extends StatelessWidget {
  /// Crée la pile des [children], un widget par plan.
  const PileDeCalques({required this.children, super.key});

  /// Les plans à superposer. L'ordre d'écriture n'a aucune importance.
  final Map<Calque, Widget> children;

  @override
  Widget build(BuildContext context) {
    final plans = children.entries.toList()
      ..sort((a, b) => a.key.z.compareTo(b.key.z));
    return Stack(
      children: [
        for (final MapEntry(key: calque, value: enfant) in plans)
          if (calque == Calque.carte) enfant else SafeArea(child: enfant),
      ],
    );
  }
}

/// Ce qu'une feuille modale doit ajouter sous son contenu — §2.3.
///
/// Somme du **clavier** (`viewInsets`) et de la **barre de gestes**
/// (`padding`) : un bouton « Confirmer » caché sous le clavier est le défaut le
/// plus fréquent des feuilles Flutter, et n'ajouter que le clavier le laisse
/// sous la barre de gestes.
///
/// **Cette somme n'additionne jamais deux fois le même espace**, et c'est le
/// moteur qui le garantit, pas nous : `dart:ui` documente que `padding.bottom`
/// vaut `viewPadding.bottom` clavier fermé, et **zéro** clavier ouvert, parce
/// que le clavier recouvre alors la barre de gestes (`ui/window.dart`,
/// `FlutterView.padding`). D'où `padding` et non `viewPadding` : ce dernier
/// reste entier sous le clavier et écarterait le contenu d'une barre de gestes
/// que personne ne voit.
///
/// **Le résultat dépend du point d'appel, et c'est voulu.** Sous un [SafeArea],
/// le `padding` a déjà été appliqué *et* retiré du `MediaQuery` des descendants
/// (`widgets/safe_area.dart` : `MediaQuery.removePadding`) — cette fonction ne
/// rend alors que le clavier, sinon l'espace compterait double. Une feuille
/// modale s'affiche par le `Navigator`, donc **hors** de la [PileDeCalques] et
/// hors de sa safe area : elle reçoit bien les deux.
double rembourrageBas(BuildContext context) =>
    MediaQuery.viewInsetsOf(context).bottom +
    MediaQuery.paddingOf(context).bottom;
