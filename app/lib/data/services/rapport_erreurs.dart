/// Sentry côté application : ce qu'on retire d'un événement, et quand on
/// n'initialise pas le SDK du tout.
///
/// **Seul fichier de l'application qui importe `sentry_flutter`.** Tout ce qui
/// touche au rapport d'erreurs passe par ici — la racine de composition ne
/// connaît que [demarrerAvecRapport].
///
/// Le pendant serveur est `api/src/arpendo_api/core/sentry.py`. Les deux
/// portent **les mêmes motifs et le même marqueur**, à dessein : une
/// divergence de motif serait une divergence de protection. Ils ne partagent
/// pourtant aucun code, et ne le pourront jamais — le `before_send` de Python
/// reçoit un dictionnaire, celui de Dart un [SentryEvent] **typé**.
///
/// Cette différence a une conséquence de fond : côté serveur, deux filets se
/// superposent — l'`EventScrubber` du SDK, qui travaille par clé, et `scrub`,
/// qui travaille par motif. **Le SDK Dart n'a pas d'`EventScrubber`**
/// (vérifié dans `sentry-9.29.0` : la classe n'existe que dans le SDK Python).
/// [assainir] est donc le filet *unique*, ce qui interdit de le limiter aux
/// seuls emplacements que le rapport de bogue du jour cite.
library;

import 'package:sentry_flutter/sentry_flutter.dart';

/// Ce qui remplace un motif retiré.
///
/// Explicite plutôt que vide : une valeur simplement absente se lit comme un
/// bogue, et personne ne cherche l'assainissement qui l'a produite.
const String retire = '[retiré]';

/// Les motifs retirés des **chaînes**, quel que soit l'endroit de l'événement
/// où elles logent — recopiés de `PATTERNS` côté serveur.
///
/// La coordonnée se reconnaît à la **paire**, jamais à un nombre isolé : un
/// horodatage ISO (`…:35.751365Z`) porte exactement la même forme décimale, et
/// un motif à un seul nombre les emporterait tous — on assainirait alors la
/// seule chose qui permet de dater une erreur. Le séparateur est délibérément
/// large : la virgule seule laisserait passer `lat=…&lon=…`, un WKT
/// `POINT(… …)`, un JSON sérialisé et un saut de ligne.
final List<RegExp> _motifs = [
  RegExp(r'-?\d{1,3}\.\d{4,}[^\d\-]{1,20}-?\d{1,3}\.\d{4,}'),
  RegExp(r'\bBearer\s+[\w\-._~+/]+=*', caseSensitive: false),
  RegExp(r'\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b'),
];

/// La plus grande valeur absolue qu'un degré prenne — au-delà, ce n'est pas
/// une longitude.
const double _degreMaximal = 180.0;

/// Décimales minimales pour qu'un **nombre** soit tenu pour une coordonnée.
///
/// Quatre décimales valent environ 11 m. En dessous, la valeur ne localise
/// plus personne, et le seuil évite d'emporter les nombres ronds que le code
/// produit partout — un `1.0`, un `0.25`.
const int _decimalesMinimales = 4;

/// Rend cet événement débarrassé de ce qu'on n'a pas le droit d'envoyer.
///
/// Branchée en `beforeSend` par [demarrerAvecRapport], mais **éprouvable
/// seule** : elle ne parle à rien — ni réseau, ni `init`, ni projet Sentry —
/// et un test la nourrit d'un [SentryEvent] écrit à la main.
///
/// Elle **modifie l'événement reçu** et le rend, là où son homologue Python
/// en construit une copie. Ce n'est pas un relâchement : les objets du
/// protocole Dart sont typés et mutables, et le SDK lui-même recommande
/// l'affectation directe (`copyWith` y est `@Deprecated`). Les deux autres
/// voies ont été écartées — reconstruire champ par champ recopierait un
/// constructeur qui bougera, et un aller-retour `toJson`/`fromJson`, pourtant
/// possible (vérifié : `SentryClient` ne relit plus `throwable` après
/// `beforeSend`, `sentry_client.dart:174`), rendrait la fidélité de
/// `fromJson` responsable de tout ce que l'événement transporte.
///
/// **Emplacements couverts**, et pourquoi ceux-là — l'énumération est le prix
/// d'un protocole typé, et elle est tenue ici plutôt que laissée implicite :
/// [SentryEvent.message] (gabarit et paramètres compris), les valeurs
/// d'exception, les fils d'Ariane (texte et données), `extra` et son
/// successeur [SentryEvent.contexts], et les étiquettes.
///
/// ponytail: `request`, `transaction` et `culprit` ne sont **pas** assainis —
/// rien ne les remplit aujourd'hui : l'application n'installe ni
/// `SentryHttpClient` ni `SentryNavigatorObserver`, et son client HTTP est un
/// `http.Client` nu. **À reprendre par qui installera l'une de ces deux
/// intégrations, dans le même lot** : `request.headers` porte alors
/// l'en-tête d'autorisation, et `transaction` le nom de route.
///
/// Rend toujours un événement, jamais `null` : ce module ne décide pas
/// d'abandonner un envoi — c'est le rôle de l'échantillonnage.
SentryEvent assainir(SentryEvent evenement) {
  _assainirMessage(evenement.message);
  evenement.exceptions?.forEach(_assainirException);
  evenement.breadcrumbs?.forEach(_assainirFilDAriane);
  // Les deux seuls champs *remplacés* plutôt que modifiés : ce sont du JSON
  // quelconque, et [_assainirValeur] reconstruit les cartes qu'il traverse.
  // ignore: deprecated_member_use
  evenement.extra = _assainirJson(evenement.extra);
  evenement.tags = evenement.tags?.map(
    (clef, valeur) => MapEntry(clef, _assainirTexte(valeur)),
  );
  _assainirContextes(evenement.contexts);
  return evenement;
}

/// Assainit le texte d'un message, son gabarit et ses paramètres.
void _assainirMessage(SentryMessage? message) {
  if (message == null) return;
  message.formatted = _assainirTexte(message.formatted);
  final gabarit = message.template;
  if (gabarit != null) message.template = _assainirTexte(gabarit);
  message.params = _assainirJson(message.params);
}

/// Assainit ce qu'une exception dit d'elle-même.
///
/// `stackTrace` n'est pas traversée : elle porte des noms de fichiers, de
/// classes et de fonctions — du code, jamais une donnée de joueur.
void _assainirException(SentryException exception) {
  final valeur = exception.value;
  if (valeur != null) exception.value = _assainirTexte(valeur);
}

/// Assainit le texte d'un fil d'Ariane et les données qu'il transporte.
void _assainirFilDAriane(Breadcrumb fil) {
  final message = fil.message;
  if (message != null) fil.message = _assainirTexte(message);
  fil.data = _assainirJson(fil.data);
}

/// Assainit les contextes **sur place**.
///
/// [Contexts] est une vue de carte, pas un champ qu'on remplace : on réécrit
/// ses entrées. Les contextes que le SDK remplit lui-même — appareil, système,
/// application — sont des objets typés, que [_assainirValeur] rend inchangés
/// faute de savoir les traverser ; ils ne portent aucune donnée de joueur tant
/// que `sendDefaultPii` reste faux. Ceux qu'un appelant ajoute sont des cartes
/// ou des listes, et ceux-là sont traversés.
void _assainirContextes(Contexts contextes) {
  for (final clef in contextes.keys.toList()) {
    contextes[clef] = _assainirValeur(contextes[clef]);
  }
}

/// Retire de ce texte chaque motif sensible.
String _assainirTexte(String texte) {
  for (final motif in _motifs) {
    texte = texte.replaceAll(motif, retire);
  }
  return texte;
}

/// Descend dans une structure et n'assainit que ce qu'elle sait reconnaître.
///
/// Générique par nécessité : une carte d'`extra` ou de données de fil
/// d'Ariane est du JSON quelconque, dont la forme n'est pas connue à
/// l'écriture. Ce qui n'est ni chaîne, ni carte, ni liste — un nombre isolé,
/// un booléen, un objet typé du protocole — est rendu tel quel.
Object? _assainirValeur(Object? valeur) {
  if (valeur is String) return _assainirTexte(valeur);
  if (valeur is Map) {
    final paire = _formeUnePaire(valeur.values);
    return <String, dynamic>{
      for (final entree in valeur.entries)
        entree.key.toString(): _assainirEnfant(entree.value, paire),
    };
  }
  if (valeur is List) {
    final paire = _formeUnePaire(valeur);
    return <dynamic>[
      for (final element in valeur) _assainirEnfant(element, paire),
    ];
  }
  return valeur;
}

/// Assainit un élément en tenant compte de ce que ses **voisins** révèlent.
///
/// C'est ici que la règle de la paire s'applique aux nombres : une composante
/// n'est retirée que si le conteneur qui la porte en contient une seconde.
Object? _assainirEnfant(Object? valeur, bool dansUnePaire) =>
    dansUnePaire && _aLaFormeDunDegre(valeur)
    ? retire
    : _assainirValeur(valeur);

/// Dit si ces valeurs voisines contiennent **au moins deux** composantes de
/// coordonnée.
///
/// La même règle que pour les chaînes, transposée aux nombres : **une position
/// se reconnaît à la paire**. Un flottant isolé est indécidable — durée, prix,
/// moyenne — et le redresser emporterait la moitié des nombres d'un événement.
///
/// Le faux positif assumé est un conteneur de deux mesures fines
/// (`{"p50": 12.345678, "p99": 98.765432}`), assaini pour rien. L'asymétrie
/// est voulue : perdre un centile se voit et se répare, laisser fuir une
/// position ne se voit pas et ne se répare pas (cadrage §12.3).
bool _formeUnePaire(Iterable<Object?> valeurs) =>
    valeurs.where(_aLaFormeDunDegre).length >= 2;

/// Dit si ce **nombre** a la forme d'une composante de coordonnée.
///
/// Une forme, pas une certitude : `12.345678` peut être une durée. C'est
/// pourquoi cette fonction ne décide rien seule — voir [_formeUnePaire].
///
/// Seuls les `double` sont examinés : un `int` n'a pas de décimales, donc
/// jamais la précision qui localise.
bool _aLaFormeDunDegre(Object? valeur) {
  if (valeur is! double) return false;
  if (valeur.abs() > _degreMaximal) return false;
  final ecriture = valeur.toString();
  final separateur = ecriture.indexOf('.');
  if (separateur < 0) return false;
  return ecriture.length - separateur - 1 >= _decimalesMinimales;
}

/// Assainit une structure JSON facultative en lui rendant son type statique.
///
/// [_assainirValeur] est volontairement typée `Object?` — elle descend dans
/// des formes qu'elle ne connaît pas. Cette enveloppe rend le résultat au
/// type du champ appelant, une fois, plutôt qu'un transtypage recopié à
/// chaque emplacement.
T? _assainirJson<T extends Object>(T? valeur) =>
    valeur == null ? null : _assainirValeur(valeur) as T;
