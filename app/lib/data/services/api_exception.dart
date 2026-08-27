/// Échec typé d'un appel au serveur.
///
/// Scellée : tout appelant qui traite un échec le fait par un `switch`
/// exhaustif, et le compilateur signale l'oubli le jour où un cas s'ajoute.
///
/// Un échec ne transporte **jamais** de texte destiné à l'écran (spec UX
/// §13.3) : il porte une raison typée, et l'appelant choisit le message.
sealed class ApiException implements Exception {
  const ApiException();

  /// Nom du cas, pour les journaux et les traces.
  ///
  /// Le défaut de [Object.toString] rend « Instance of 'HorsLigne' » : le nom
  /// du cas noyé dans du bruit, sur la seule ligne qu'on lira d'un incident.
  /// Défini ici plutôt que sur chaque cas — un cas ajouté demain se nomme sans
  /// qu'on y pense, et rien ne peut être oublié.
  ///
  /// ponytail: repose sur `runtimeType`, que `flutter build --obfuscate`
  /// mangle. L'option n'est pas utilisée par le projet ; si elle l'était, ces
  /// noms redeviendraient des littéraux, un par cas.
  @override
  String toString() => '$runtimeType';
}

/// Le téléphone n'a aucune interface réseau active.
///
/// Message attendu à l'écran : cadrage §10.3.
final class HorsLigne extends ApiException {
  const HorsLigne();
}

/// Le réseau est présent, mais le serveur n'a pas répondu.
///
/// Message attendu à l'écran : cadrage §10.3. Il doit décourager de fermer
/// l'application — sans cela, un incident serveur se transforme en perte de
/// progression massive.
final class ServeurInjoignable extends ApiException {
  const ServeurInjoignable();
}

/// Le serveur a répondu, hors de la plage 2xx.
///
/// Porte le [statut] et rien d'autre : ni le corps, ni un message. Le texte
/// affiché est le choix de l'appelant (spec UX §13.3).
final class ErreurHttp extends ApiException {
  const ErreurHttp(this.statut);

  /// Code de statut HTTP renvoyé par le serveur.
  final int statut;

  /// Le nom du cas **et** son statut : un échec HTTP sans son code ne dit rien.
  @override
  String toString() => '${super.toString()}($statut)';
}

/// Le serveur a répondu 2xx, avec un corps inexploitable.
///
/// Octets qui ne sont pas de l'UTF-8, JSON invalide, corps vide, ou racine qui
/// n'est pas un objet. Le corps d'une réponse est une frontière de confiance :
/// sans ce cas, une régression du serveur ferait planter l'application en
/// partie au lieu d'afficher un bandeau (spec UX §13.3).
final class ReponseInvalide extends ApiException {
  const ReponseInvalide();
}

/// Classe une panne de transport selon l'état du réseau.
///
/// C'est le **seul** endroit où se décide la distinction que le cadrage §10.3
/// impose : sans réseau, le joueur est [HorsLigne] ; avec réseau, c'est le
/// serveur qui est en cause. Fonction pure, donc testable sans réseau.
///
/// [enLigne] : le téléphone a-t-il une interface réseau active, tel que le
/// rapporte le service de connectivité.
///
/// Renvoie l'échec typé correspondant ; ne lève jamais.
ApiException classifierPanneDeTransport({required bool enLigne}) =>
    enLigne ? const ServeurInjoignable() : const HorsLigne();
