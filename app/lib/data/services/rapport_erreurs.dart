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

import 'dart:async';
import 'dart:developer' as developer;

import 'package:flutter/foundation.dart' show visibleForTesting;
import 'package:sentry_flutter/sentry_flutter.dart';

// ─── Ce que les trois volets partagent ─────────────────────────────────────────

/// Le nom sous lequel ce module écrit au journal de développement.
///
/// **`developer.log` n'écrit pas dans logcat**, contrairement à ce que
/// « journal » laisse croire : son contrat est d'émettre vers la vue Logging
/// de DevTools. En **release**, sans service VM attaché, personne n'écoute et
/// l'appel ne fait rien — il ne lève pas pour autant. C'est donc un confort de
/// développement, jamais un canal d'exploitation : aucun chemin de ce module ne
/// doit compter dessus pour être vu en production.
const String _journal = 'arpendo.sentry';

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
/// `POINT(… …)`, un JSON sérialisé et un saut de ligne. Le **tiret** en fait
/// partie : l'exclure pour préserver le signe d'une longitude négative ne
/// protégeait de rien — c'est le passage entier qui est remplacé, signe
/// compris — et laissait passer `hote-48.858370-2.294481`. Le faux positif
/// assumé est l'intervalle à quatre décimales (`12.345678-98.765432`),
/// assaini pour rien, comme la paire de durées jointe par une virgule l'est
/// déjà.
///
/// Le motif est identique caractère pour caractère à celui du serveur, sans
/// être strictement équivalent : `\d` ne couvre ici que `[0-9]` (syntaxe
/// ECMAScript), quand Python y met aussi les chiffres Unicode (catégorie
/// `Nd`) — le serveur retire donc **plus** que l'app, jamais moins.
final List<RegExp> _motifs = [
  RegExp(r'-?\d{1,3}\.\d{4,}[^\d]{1,20}-?\d{1,3}\.\d{4,}'),
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

// ─── Démarrage : quand on initialise, et ce qu'on pose ─────────────────────────

/// Ce qui met Sentry en place autour du lancement de l'application.
///
/// Une fonction plutôt qu'un appel direct au SDK, pour que
/// [demarrerAvecRapport] soit éprouvable sans réseau ni projet Sentry : le
/// test en fournit une qui note ce qu'elle reçoit.
typedef InitialisationSentry = Future<void> Function(
  String dsn,
  double? tauxEnvoi,
  AppRunner lancer,
);

/// Lance l'application, sous Sentry **seulement** si un DSN est fourni.
///
/// « Désactivé » veut dire *aucun appel au SDK*, et non un `init` avec un DSN
/// vide : ce dernier installe quand même les intégrations et le hook des
/// exceptions non rattrapées. C'est une différence qu'on ne voit pas sur un
/// poste de développement et qui compte partout ailleurs — la même décision,
/// et pour la même raison, que `configure_sentry` côté serveur.
///
/// Le DSN vient de `--dart-define=SENTRY_DSN`, injecté par les recettes
/// `just run` et `just build` depuis le `.env` de la racine. **Vide est un
/// état légitime**, et c'est le défaut du poste — à la différence
/// d'`API_BASE_URL`, dont l'absence arrête le démarrage.
///
/// [lancer] est appelé dans les deux branches, et **exactement une fois** :
/// sous DSN, c'est le SDK qui l'exécute, dans la zone où il capte les erreurs
/// non rattrapées ; sans DSN, on l'appelle directement. Tout ce que fait
/// l'application — construction des services comprise — est donc à
/// l'intérieur, et rien de ce qui peut échouer ne se produit avant que le
/// filet soit tendu.
///
/// **Le filet lui-même peut échouer, et l'application doit démarrer quand
/// même.** `SentryFlutter.init` n'est pas total : `Sentry.init` lève
/// `ArgumentError` hors de son `try`, et `_initDefaultValues`,
/// `_setDefaultConfiguration`, `createBinding` et les intégrations sont
/// attendus hors `try` (lu dans `Sentry.init` et `Sentry._init`, sentry
/// 9.29.0) — or `appRunner` n'est appelé qu'**après** les intégrations. Sans
/// le repli ci-dessous, un canal natif en erreur **figerait l'application sur
/// l'écran de démarrage d'Android** — `runApp` n'étant jamais atteint —, en
/// production seulement : le poste tourne DSN vide, et la CI aussi. Un outil
/// d'observabilité qui empêche l'application de démarrer coûte infiniment plus
/// que ce qu'il rapporte.
///
/// **Le repli ne couvre que les pannes de Sentry.** Comme c'est le SDK qui
/// appelle [lancer], une exception de l'*application* remonte par le même
/// chemin qu'une panne du SDK : elle est distinguée sur « le lancement
/// a-t-il commencé ? » et **relancée**. Les confondre annulerait en silence
/// le refus de démarrer sans `API_BASE_URL`, et remplacerait son message
/// explicite par une ligne de journal qui accuse Sentry à tort.
///
/// Args:
///   dsn: le point de collecte, ou la chaîne vide pour ne rien initialiser.
///   lancer: ce qui construit et fait tourner l'application.
///   initialiser: la mise en place du SDK. Le défaut est la vraie ; les tests
///     la remplacent pour observer qu'elle est appelée — ou qu'elle ne l'est
///     pas.
Future<void> demarrerAvecRapport({
  required String dsn,
  required AppRunner lancer,
  double? tauxEnvoi,
  InitialisationSentry initialiser = _initialiserSentry,
}) async {
  var lance = false;
  Future<void> lancerUneFois() async {
    if (lance) return;
    lance = true;
    await lancer();
  }

  if (dsn.isEmpty) {
    await lancerUneFois();
    return;
  }
  try {
    await initialiser(dsn, tauxEnvoi, lancerUneFois);
  } on Object catch (erreur, trace) {
    // `lance` discrimine les deux pannes que ce `catch` reçoit, et il faut les
    // traiter à l'opposé. Le SDK appelle [lancer] lui-même : une exception de
    // l'**application** traverse donc [initialiser] et arrive ici comme une
    // panne de Sentry. L'avaler annulerait en silence le refus de démarrer
    // sans `API_BASE_URL` — et en production seulement, là où un DSN est posé.
    if (lance) rethrow;
    // Sentry, lui, a échoué avant d'avoir rien lancé : repli silencieux à
    // l'écran, tracé au journal de développement. Il n'y a rien à proposer au
    // joueur, et Sentry — précisément indisponible — ne peut pas rapporter sa
    // propre panne. C'est donc le seul chemin du module qui n'ait AUCUN canal
    // en production : la trace se voit au premier `just run`, et nulle part
    // ailleurs. Assumé — l'alternative serait un `print`, que
    // `.claude/rules/contraintes.md` proscrit.
    developer.log(
      'Sentry non initialisé, l\'application démarre sans rapport d\'erreurs',
      name: _journal,
      error: erreur,
      stackTrace: trace,
    );
  }
  await lancerUneFois();
}

/// Pose les réglages du SDK — **et rien d'autre**, pour être éprouvable.
///
/// Séparée de [_initialiserSentry] à dessein : `SentryFlutter.init` parle au
/// canal natif, donc aucun test ne l'appelle, et une configuration écrite
/// *dans* sa closure serait la seule ligne du module que rien n'exerce. Or
/// c'est précisément la ligne dont l'absence est l'incident visé par le
/// cadrage §13.10 — la mesure l'a montré : retirer le `beforeSend` laissait
/// toute la suite verte. [SentryFlutterOptions] s'instancie sans réseau, un
/// test lit donc chaque réglage et fait passer un événement par le
/// `beforeSend` posé ici.
///
/// Quatre réglages, et rien de plus : le DSN, `sendDefaultPii` **faux**
/// (cadrage §13.10), [assainir] en `beforeSend`, et le taux d'envoi.
///
/// Le taux est le second garde-fou exigé par le cadrage §16 — « filtrage
/// entrant **et** échantillonnage dès le jour 1 » —, et il n'est pas
/// décoratif ici : le quota de 5 000 erreurs par mois est celui de
/// l'**organisation**, donc l'application et l'api le consomment ensemble, et
/// la déduplication du SDK ne rattrape rien sur le chemin qui vient de
/// s'ouvrir — elle repose sur `exception.hashCode`, or `PlatformException`
/// n'a ni `==` ni `hashCode`, si bien que deux incidents identiques comptent
/// pour deux.
///
/// À ne pas confondre avec `tracesSampleRate`, qui échantillonne les
/// **mesures de performance** : celui-là reste absent, aucune mesure n'étant
/// demandée, et l'activer facturerait des spans que personne ne lit.
///
/// **Cette fonction ne lève jamais, et c'est sa propriété la plus
/// importante.** Elle s'exécute dans la closure de configuration de
/// `SentryFlutter.init`, que le SDK enveloppe dans un `try` qui **avale**
/// (`rethrow` seulement en `automatedTestMode` — lu dans `Sentry.init`, sentry
/// 9.29.0). Une exception ici ne remonte donc à personne, et laisse un SDK
/// **à moitié configuré** : le DSN a déjà été posé en amont par
/// `_setEnvironmentVariables`, depuis le `--dart-define` que le justfile passe
/// toujours, si bien que le garde `dsn == null` du SDK ne rattrape rien.
/// Sentry s'initialiserait alors avec le vrai DSN et **sans `beforeSend`** —
/// [assainir] ne tournerait jamais, et rien ne le dirait. C'est l'incident du
/// cadrage §13.10 déclenché par une faute de frappe dans un `.env`.
///
/// D'où la répartition : les bornes sont vérifiées **en amont**, par
/// [tauxEnvoiValide], à la racine de composition, avant tout contact avec le
/// SDK. Ce qui reste ici **normalise au lieu de refuser** — une valeur
/// impossible devient « tout envoyer », jamais une exception.
///
/// Cette normalisation est **inatteignable depuis `main`**, et c'est voulu :
/// mesuré, le seul appelant de production est [_initialiserSentry], alimenté
/// par [tauxEnvoiValide], qui rend `null`, une valeur de `]0, 1]`, ou lève.
/// Elle n'est pas là pour un cas d'usage — elle est là pour que cette fonction
/// soit **totale**, quel que soit l'appelant, `tauxEnvoi` étant un paramètre
/// public. La totalité est la propriété sur laquelle repose tout ce qui
/// précède ; une garde qui la produit n'est pas morte parce qu'aucun chemin
/// connu ne l'emprunte.
///
/// Args:
///   options: les options que le SDK s'apprête à utiliser.
///   dsn: le point de collecte, non vide — l'appelant a déjà tranché.
///   tauxEnvoi: la part des événements réellement envoyés, dans `]0, 1]`.
///     `null`, ou toute valeur hors bornes, vaut « tout envoyer » :
///     l'échantillonnage borne un coût, il n'éteint jamais la collecte et il
///     n'empêche jamais la configuration d'aboutir.
@visibleForTesting
void configurerSentry(
  SentryFlutterOptions options,
  String dsn, {
  double? tauxEnvoi,
}) {
  options.dsn = dsn;
  options.sendDefaultPii = false;
  // Forme **positive** : `NaN` ne satisfait aucune comparaison, donc il tombe
  // ici sur « tout envoyer » au lieu de traverser. Posé tel quel, il rendrait
  // l'échantillonnage silencieusement inopérant — `NaN < x` est toujours faux,
  // donc aucun événement ne serait jamais écarté.
  options.sampleRate = _dansLesBornes(tauxEnvoi) ? tauxEnvoi : 1.0;
  options.beforeSend = _assainirOuAbandonner;
}

/// Le `beforeSend` : l'événement assaini, ou **rien**.
///
/// Le `try` n'est pas une précaution de style, il retourne le mode de panne du
/// SDK. **Le SDK Dart échoue ouvert** : son `_runBeforeSend` initialise sa
/// variable de sortie avec l'événement *d'origine*, et son `catch` ne la remet
/// pas à `null` (lu dans `SentryClient`, sentry 9.29.0). Un `beforeSend` qui
/// lève laisse donc partir l'événement **brut**. Le pendant Python part de
/// `None` et abandonne (`sentry_sdk/client.py`) — c'est-à-dire qu'il échoue
/// **fermé**.
///
/// La divergence qui compte entre les deux modules n'est donc pas dans les
/// motifs, elle est là ; et comme [assainir] modifie l'événement **sur place**,
/// un jet à mi-parcours laisserait partir un événement à moitié nettoyé, dont
/// la moitié restante est exactement ce que le §12.3 interdit.
///
/// [assainir] peut lever : mesuré, une structure cyclique ou une imbrication
/// profonde donnent un `StackOverflowError`. Aujourd'hui ces entrées-là
/// défont aussi `jsonEncode` en aval, donc l'événement serait perdu de toute
/// façon — mais ce recouvrement est **fortuit**, et toute raison future de
/// lever atterrirait dans le chemin ouvert avec un événement parfaitement
/// sérialisable. On ferme la porte plutôt que de compter dessus.
///
/// Abandonner un événement qu'on ne **sait pas** nettoyer n'est pas de
/// l'échantillonnage : c'est le filet qui se ferme.
///
/// **Le rapport n'est pas perdu pour autant**, et c'est ce qui rend `null`
/// acceptable plutôt que résigné : le SDK compte l'abandon
/// (`recordLostEvent(DiscardReason.beforeSend, …)`) et l'attache à la
/// prochaine enveloppe via `ClientReportTransport`. L'incident apparaît donc
/// dans les statistiques d'événements écartés de l'organisation, sous le motif
/// `before_send` — c'est-à-dire exactement l'observabilité qu'un « événement
/// minimal » chercherait à récupérer, obtenue sans construire quoi que ce soit
/// à partir d'une structure qu'on vient d'échouer à parcourir.
///
/// [assainir] modifiant l'événement **sur place**, celui qu'on abandonne a été
/// partiellement nettoyé au passage. Sans conséquence — la mutation ne fait que
/// retirer, elle est idempotente, et les objets partagés avec le `Scope` en
/// sortent plus propres — mais il vaut mieux le lire ici que le découvrir.
SentryEvent? _assainirOuAbandonner(SentryEvent evenement, Hint hint) {
  try {
    return assainir(evenement);
  } on Object catch (erreur, trace) {
    developer.log(
      'événement Sentry abandonné : assainissement impossible',
      name: _journal,
      error: erreur,
      stackTrace: trace,
    );
    return null;
  }
}

/// Dit si ce taux est utilisable — en forme **positive**, seule qui rejette
/// `NaN`.
///
/// C'est aussi ce qui rend vraie la promesse « mêmes bornes que le
/// `SampleRate` de l'api » : la contrainte pydantic `gt=0` exige elle aussi
/// que la comparaison soit *vraie*, là où un `x <= 0 || x > 1` laisserait
/// passer `NaN`, dont les deux membres sont faux.
bool _dansLesBornes(double? taux) => taux != null && taux > 0 && taux <= 1;

/// Met Sentry en place, puis lui confie le lancement de l'application.
Future<void> _initialiserSentry(
  String dsn,
  double? tauxEnvoi,
  AppRunner lancer,
) => SentryFlutter.init(
  (options) => configurerSentry(options, dsn, tauxEnvoi: tauxEnvoi),
  appRunner: lancer,
);

/// Lit le taux d'envoi injecté à la compilation, ou refuse de le deviner.
///
/// Séparée de [main] pour être prouvable : `String.fromEnvironment` est figée
/// à la compilation, un test ne peut pas la faire varier. Même raison, et même
/// forme, que `baseUrlValidee` et `numeroDeBuildValide`.
///
/// La chaîne **vide** rend `null` — la variable n'est pas configurée, on
/// envoie tout. Toute autre valeur inutilisable — pas un nombre, hors de
/// `]0, 1]`, `NaN`, un infini — est une configuration cassée et non un choix :
/// la laisser passer enverrait silencieusement 100 % là où quelqu'un croyait
/// avoir posé un plafond de coût.
///
/// **C'est ici que les bornes sont tenues, et nulle part en aval.** Le seul
/// autre endroit possible serait [configurerSentry], qui s'exécute dans la
/// closure de `SentryFlutter.init` — où lever revient à désactiver
/// l'assainissement en silence. Ici, en revanche, l'appel est une **expression
/// d'argument** de `demarrerAvecRapport`, évaluée avant d'y entrer : le jet
/// part donc avant le moindre contact avec le SDK, exactement comme
/// `baseUrlValidee` le fait pour `API_BASE_URL`.
///
/// Ce que « arrête le démarrage » veut dire précisément, `main` étant `async` :
/// une **erreur asynchrone non rattrapée**. Mesuré sur émulateur : l'écran de
/// démarrage d'Android **reste affiché** — `runApp` n'est jamais atteint — et
/// la trace part dans logcat, le moteur y imprimant les exceptions non
/// rattrapées. C'est donc, à la différence d'un `developer.log`, un signal
/// **visible en production**. Sentry n'est pas encore initialisé à ce moment,
/// donc rien ne la capte côté rapport. C'est le comportement déjà en place pour `API_BASE_URL`, et la raison
/// pour laquelle une valeur fautive se voit au **premier lancement**, jamais
/// plus tard.
///
/// Args:
///   brut: la valeur de `--dart-define=SENTRY_SAMPLE_RATE`.
///
/// Returns:
///   Le taux, ou `null` si la variable est absente.
///
/// Raises:
///   ArgumentError: si la valeur est présente et inutilisable.
double? tauxEnvoiValide(String brut) {
  if (brut.isEmpty) return null;
  final taux = double.tryParse(brut);
  if (!_dansLesBornes(taux)) {
    throw ArgumentError.value(
      brut,
      'SENTRY_SAMPLE_RATE',
      'doit être un nombre dans ]0, 1] — voir .env.example, section « Sentry »',
    );
  }
  return taux;
}

// ─── Signalement des incidents qu'aucun écran ne montre ────────────────────────

/// La signature par laquelle un service signale un incident de plateforme.
///
/// Les services de la couche Data la reçoivent en paramètre, avec
/// [signalerIncident] pour défaut : c'est ce qui leur évite d'importer
/// `sentry_flutter` — un seul fichier le fait — et ce qui rend leur
/// signalement observable en test.
typedef Signalement = void Function(
  String message, {
  required String source,
  Object? erreur,
  StackTrace? trace,
});

/// Ce qui remonte une erreur à Sentry — remplaçable en test.
typedef CaptureIncident = void Function(Object erreur, StackTrace? trace);

/// Écrit un incident de plateforme au journal, **et** le remonte à Sentry.
///
/// Le journal de développement reste : il est le seul canal lisible pendant
/// un développement, où Sentry est désactivé. En release il ne porte rien
/// (voir le nom de journal du module) — c'est Sentry qui prend le relais, et
/// c'est pourquoi ce couple existe plutôt qu'un `developer.log` seul. Sentry s'y ajoute pour les
/// incidents qu'aucun écran ne montre — une sonde réseau qui échoue
/// silencieusement, une fiche de magasin qu'aucune activité n'ouvre — et qui
/// resteraient donc invisibles depuis la production. C'est la promesse que
/// portaient les documentations de `ConnectivityService` et de
/// `MagasinService`.
///
/// **Sans Sentry initialisé, l'appel ne coûte rien et ne lève pas** : le hub
/// et la file de tâches du SDK valent `NoOpHub` et `NoOpTaskQueue` tant
/// qu'aucun `init` n'a eu lieu (lu dans `Sentry`, sentry 9.29.0). Aucun
/// appelant n'a donc à savoir si le rapport d'erreurs tourne.
///
/// Args:
///   message: ce qui s'est passé, en une phrase — écrit au journal.
///   source: le nom de journal de l'appelant (`arpendo.magasin`…).
///   erreur: l'exception d'origine, s'il y en a une. **C'est elle seule qui
///     part à Sentry** : un message sans exception est une note d'exécution,
///     pas un incident à instruire.
///   trace: la pile de l'erreur, quand l'appelant l'a.
///   capturer: la remontée à Sentry. Le défaut est la vraie.
void signalerIncident(
  String message, {
  required String source,
  Object? erreur,
  StackTrace? trace,
  CaptureIncident capturer = _capturerParSentry,
}) {
  developer.log(message, name: source, error: erreur, stackTrace: trace);
  if (erreur != null) capturer(erreur, trace);
}

/// La remontée réelle : elle part en fond, l'appelant n'a rien à en attendre.
void _capturerParSentry(Object erreur, StackTrace? trace) {
  unawaited(Sentry.captureException(erreur, stackTrace: trace));
}

// ─── Assainissement : ce qu'on retire d'un événement, et où ────────────────────

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
/// possible (vérifié : `SentryClient.captureEvent` ne relit plus `throwable`
/// après son `beforeSend`), rendrait la fidélité de `fromJson` responsable de
/// tout ce que l'événement transporte.
///
/// La mutation porte sur des objets que le `Scope` **partage** : sa copie de
/// la liste des fils d'Ariane est superficielle, si bien qu'un `Breadcrumb`
/// assaini l'est durablement. Sans conséquence tant que les règles sont
/// idempotentes — elles le sont, `[retiré]` ne contient aucun motif —, mais
/// une règle future qui ne le serait pas se composerait sur elle-même.
///
/// **Tous les emplacements porteurs de texte sont couverts**, et non les
/// seuls que le critère d'acceptation cite : le message (gabarit et
/// paramètres compris), les exceptions (valeur et mécanisme), les fils
/// d'Ariane, les fils d'exécution, l'utilisateur, la requête, les contextes,
/// `transaction`, `culprit`, `logger`, `serverName`, `fingerprint`,
/// `modules`, les étiquettes et `extra`. L'énumération est le prix d'un
/// protocole typé ; ce qui la rend tenable est le test de **population** qui
/// l'accompagne — un événement dont chaque emplacement porte une donnée
/// interdite, sérialisé puis relu. Un champ ajouté au fixture sans être
/// assaini fait rougir la suite ; un `expect` par champ ne l'aurait pas fait.
///
/// Restent en dehors **par choix** : `type` d'exception et piles d'appels (du
/// **code**, jamais une donnée de joueur), `id` d'utilisateur (ce qui rend un
/// rapport attribuable), `release`, `dist`, `environment` et `platform` (des
/// métadonnées de build que l'application choisit).
///
/// Reste en dehors **par contrainte**, et c'est le seul : `Mechanism.meta`,
/// que le SDK expose en lecture sans mutateur (`mechanism.dart` n'a que
/// `set data`). Son voisin `mechanism.data`, lui, est assaini. Le risque est
/// nul en pratique — `meta` n'est rempli que par le SDK natif, dont les
/// enveloppes ne passent pas par `beforeSend` (voir plus bas) — mais il est
/// écrit ici plutôt que taire : une énumération qui se dit complète et ne l'est
/// pas vaut moins qu'une énumération qui dit où elle s'arrête.
///
/// **Une voie échappe entièrement à cette fonction** : les plantages
/// **natifs**. `SentryFlutter.init` installe `NativeSdkIntegration` et laisse
/// `enableNativeCrashHandling` vrai ; le SDK Android envoie alors ses propres
/// enveloppes, et le SDK le dit lui-même — « captureEnvelope does not call the
/// beforeSend callback ». Ce que le natif reçoit du Dart, c'est
/// `sendDefaultPii`, transmis à `androidOptions.setSendDefaultPii`. [assainir]
/// est donc le filet de la **voie Dart**, pas de toutes les voies.
///
/// Rend toujours un événement, jamais `null` : ce module ne décide pas
/// d'abandonner un envoi — c'est le rôle de l'échantillonnage.
SentryEvent assainir(SentryEvent evenement) {
  _assainirMessage(evenement.message);
  evenement.exceptions?.forEach(_assainirException);
  evenement.breadcrumbs?.forEach(_assainirFilDAriane);
  evenement.threads?.forEach(_assainirFilDExecution);
  _assainirUtilisateur(evenement.user);
  evenement.request = _assainirRequete(evenement.request);
  _assainirContextes(evenement.contexts);
  evenement.transaction = _assainirFacultatif(evenement.transaction);
  evenement.culprit = _assainirFacultatif(evenement.culprit);
  evenement.logger = _assainirFacultatif(evenement.logger);
  evenement.serverName = _assainirFacultatif(evenement.serverName);
  evenement.fingerprint = evenement.fingerprint?.map(_assainirTexte).toList();
  evenement.modules = _assainirTable(evenement.modules);
  evenement.tags = _assainirTable(evenement.tags);
  // Le seul champ *remplacé* plutôt que modifié : c'est du JSON quelconque, et
  // [_assainirValeur] reconstruit les cartes qu'il traverse.
  // ignore: deprecated_member_use
  evenement.extra = _assainirJson(evenement.extra);
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

/// Assainit ce qu'une exception dit d'elle-même, mécanisme compris.
///
/// `type` reste : c'est le nom d'une classe. `stackTrace` non plus n'est pas
/// traversée — elle porte des noms de fichiers, de classes et de fonctions,
/// du code et jamais une donnée de joueur.
void _assainirException(SentryException exception) {
  exception.value = _assainirFacultatif(exception.value);
  final mecanisme = exception.mechanism;
  if (mecanisme == null) return;
  mecanisme.description = _assainirFacultatif(mecanisme.description);
  mecanisme.data = _assainirJson(Map<String, dynamic>.of(mecanisme.data));
}

/// Assainit le nom d'un fil d'exécution.
void _assainirFilDExecution(SentryThread fil) {
  fil.name = _assainirFacultatif(fil.name);
}

/// Assainit l'identité du joueur attachée à l'événement.
///
/// Le seul champ du protocole qui s'appelle littéralement « email », plus un
/// pseudonyme, un nom et une carte libre — et c'est précisément celui que le
/// domaine Compte remplira. `id` reste : c'est ce qui rend un rapport
/// attribuable, et c'est un identifiant technique, pas une donnée de contact.
void _assainirUtilisateur(SentryUser? utilisateur) {
  if (utilisateur == null) return;
  utilisateur.email = _assainirFacultatif(utilisateur.email);
  utilisateur.username = _assainirFacultatif(utilisateur.username);
  utilisateur.name = _assainirFacultatif(utilisateur.name);
  utilisateur.data = _assainirJson(utilisateur.data);
}

/// Assainit une requête HTTP jointe à l'événement.
///
/// Rien ne la remplit tant que `SentryHttpClient` n'est pas installé, mais
/// elle est l'emplacement qui porterait l'en-tête d'autorisation : la couvrir
/// coûte cinq lignes, et l'oublier se paierait au premier lot qui installe
/// l'intégration, sans que rien ne le signale.
/// C'est le seul emplacement **reconstruit** et non modifié : `env` et `data`
/// n'ont pas de mutateur, seulement des vues non modifiables et un paramètre
/// de constructeur (lu dans `SentryRequest`, sentry 9.29.0). Tous les champs
/// publics sont recopiés, `apiTarget` déprécié compris.
///
/// **Un seul se perd, et il faut le dire** : `unknown`, que le SDK marque
/// `@internal` — l'analyseur refuse de le lire hors du paquet. Il ne porte que
/// les clés JSON qu'une désérialisation n'a pas reconnues, donc il est nul
/// pour une requête construite côté Dart. C'est le prix exact qu'on a refusé
/// de payer sur l'événement entier en écartant l'aller-retour
/// `toJson`/`fromJson` : ici il porte sur un champ nul en pratique, et la
/// seule autre issue serait de laisser `env` et `data` non assainis.
SentryRequest? _assainirRequete(SentryRequest? requete) {
  if (requete == null) return null;
  return SentryRequest(
    url: _assainirFacultatif(requete.url),
    method: requete.method,
    queryString: _assainirFacultatif(requete.queryString),
    cookies: _assainirFacultatif(requete.cookies),
    fragment: _assainirFacultatif(requete.fragment),
    data: _assainirValeur(requete.data),
    headers: _assainirTable(Map<String, String>.of(requete.headers)),
    env: _assainirTable(Map<String, String>.of(requete.env)),
    // ignore: deprecated_member_use
    apiTarget: requete.apiTarget,
  );
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
///
/// Rend **la chaîne reçue elle-même** quand rien n'a bougé, et non une copie
/// égale : c'est ce qui permet à [_assainirValeur] de savoir, par `identical`,
/// qu'un conteneur est resté intact et de préserver son type.
///
/// **Aucun test ne peut faire rougir ce retour conditionnel**, et il faut le
/// dire plutôt que de laisser croire l'inverse : mesuré, `String.replaceAll`
/// rend déjà le receveur lui-même quand aucun motif ne correspond, si bien que
/// les deux branches sont observationnellement identiques sur cette VM. Le
/// conditionnel est là pour que la préservation de type ne **repose pas** sur
/// ce comportement, qu'aucune spécification ne promet. S'il disparaissait, la
/// conséquence serait cosmétique — un conteneur typé rendu en `List<dynamic>`
/// —, jamais une fuite : [_assainirValeur] assainit d'abord et compare ensuite.
String _assainirTexte(String texte) {
  var resultat = texte;
  for (final motif in _motifs) {
    resultat = resultat.replaceAll(motif, retire);
  }
  return resultat == texte ? texte : resultat;
}

/// Assainit un texte qui peut être absent.
String? _assainirFacultatif(String? texte) =>
    texte == null ? null : _assainirTexte(texte);

/// Assainit les valeurs d'une table de chaînes, en gardant ses clés.
Map<String, String>? _assainirTable(Map<String, String>? table) =>
    table?.map((clef, valeur) => MapEntry(clef, _assainirTexte(valeur)));

/// Descend dans une structure et n'assainit que ce qu'elle sait reconnaître.
///
/// Générique par nécessité : une carte d'`extra` ou de données de fil
/// d'Ariane est du JSON quelconque, dont la forme n'est pas connue à
/// l'écriture. Ce qui n'est ni chaîne, ni carte, ni liste — un nombre isolé,
/// un booléen, un objet typé du protocole — est rendu tel quel.
/// Un conteneur dont **rien** n'a bougé est rendu tel quel, jamais recopié :
/// sans cette précaution, traverser les contextes du SDK dégraderait un
/// `List<SentryRuntime>` en `List<dynamic>` pour ne rien y avoir changé.
Object? _assainirValeur(Object? valeur) {
  if (valeur is String) return _assainirTexte(valeur);
  if (valeur is Map) {
    final paire = _formeUnePaire(valeur.values);
    var modifie = false;
    final assainie = <String, dynamic>{};
    for (final entree in valeur.entries) {
      final apres = _assainirEnfant(entree.value, paire);
      modifie |= !identical(apres, entree.value);
      assainie[entree.key.toString()] = apres;
    }
    return modifie ? assainie : valeur;
  }
  if (valeur is List) {
    final paire = _formeUnePaire(valeur);
    var modifie = false;
    final assainie = <dynamic>[];
    for (final element in valeur) {
      final apres = _assainirEnfant(element, paire);
      modifie |= !identical(apres, element);
      assainie.add(apres);
    }
    return modifie ? assainie : valeur;
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
