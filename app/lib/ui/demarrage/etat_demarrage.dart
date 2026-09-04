import 'package:flutter/foundation.dart';

/// L'état de la séquence de démarrage — spec UX §2.1, étape 1.
///
/// Scellé : la racine de composition fait un `switch` exhaustif dessus, et
/// tout état ajouté (le domaine Compte prolongera [Pret] par sa transition de
/// session) force chaque point de décision à se prononcer — extension, jamais
/// modification invasive.
///
/// Chaque état définit `==` par sa valeur : un `ChangeNotifier` compare l'état
/// courant au précédent, et deux `Pret` identiques ne doivent pas passer pour
/// un changement.
sealed class EtatDemarrage {
  const EtatDemarrage();
}

/// Le contrôle de version est en cours ; l'écran d'attente est affiché.
@immutable
class Verification extends EtatDemarrage {
  /// Crée l'état d'attente.
  const Verification();

  @override
  bool operator ==(Object other) => other is Verification;

  @override
  int get hashCode => (Verification).hashCode;
}

/// Le build installé est sous le minimum : écran bloquant (UX §11.2).
///
/// L'écran lui-même (`EcranMiseAJour`, calque z 500) est livré par le lot 2c
/// de #46 ; d'ici là, la racine affiche l'attente neutre.
@immutable
class MiseAJourRequise extends EtatDemarrage {
  /// Crée l'état bloquant.
  const MiseAJourRequise();

  @override
  bool operator ==(Object other) => other is MiseAJourRequise;

  @override
  int get hashCode => (MiseAJourRequise).hashCode;
}

/// La lecture de `/version` a échoué : « Le serveur ne répond pas. » +
/// « Réessayer » (UX §2.1) — jamais le Menu.
@immutable
class Injoignable extends EtatDemarrage {
  /// Crée l'état d'échec.
  const Injoignable();

  @override
  bool operator ==(Object other) => other is Injoignable;

  @override
  int get hashCode => (Injoignable).hashCode;
}

/// Le contrôle de version est passé ; l'écran d'attente reste, inchangé,
/// jusqu'à ce que le domaine Compte prolonge la séquence (étape 2).
@immutable
class Pret extends EtatDemarrage {
  /// Crée l'état terminal du lot.
  const Pret({required this.miseAJourRecommandee});

  /// Vrai si le build installé est sous le recommandé : condition de la
  /// ligne 12 du bandeau (§2.4), dont le câblage — actions, persistance de la
  /// fermeture — est livré par le lot 2c de #46.
  final bool miseAJourRecommandee;

  @override
  bool operator ==(Object other) =>
      other is Pret && other.miseAJourRecommandee == miseAJourRecommandee;

  @override
  int get hashCode => Object.hash(Pret, miseAJourRecommandee);
}
