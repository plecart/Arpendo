/// Échec typé d'un appel au serveur.
///
/// Scellée : tout appelant qui traite un échec le fait par un `switch`
/// exhaustif, et le compilateur signale l'oubli le jour où un cas s'ajoute.
///
/// Un échec ne transporte **jamais** de texte destiné à l'écran (spec UX
/// §13.3) : il porte une raison typée, et l'appelant choisit le message.
sealed class ApiException implements Exception {
  const ApiException();
}

/// Le téléphone n'a aucune interface réseau active.
///
/// Message attendu à l'écran : « Pas de connexion — capture en pause »
/// (cadrage §10.3).
final class HorsLigne extends ApiException {
  const HorsLigne();
}

/// Le réseau est présent, mais le serveur n'a pas répondu.
///
/// Message attendu à l'écran : « Serveur indisponible — capture en pause.
/// Garde l'application ouverte, la reprise est automatique » (cadrage §10.3).
/// Ce message doit explicitement décourager de fermer l'application : sans
/// lui, un incident serveur se transforme en perte de progression massive.
final class ServeurInjoignable extends ApiException {
  const ServeurInjoignable();
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
