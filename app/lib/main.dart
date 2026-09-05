import 'dart:async';

import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:provider/provider.dart';

import 'data/services/api_client.dart';
import 'data/services/connectivity_service.dart';
import 'data/services/magasin_service.dart';
import 'data/services/rapport_erreurs.dart';
import 'data/services/version_client.dart';
import 'l10n/generated/app_localizations.dart';
import 'ui/core/theme/theme.dart';
import 'ui/demarrage/demarrage_view_model.dart';
import 'ui/demarrage/ecran_attente.dart';
import 'ui/demarrage/ecran_mise_a_jour.dart';
import 'ui/demarrage/etat_demarrage.dart';

/// Met le rapport d'erreurs en place, puis construit et lance l'application.
///
/// Ce fichier est le **seul** à lire l'environnement de compilation.
/// `API_BASE_URL`, `SENTRY_DSN` et `SENTRY_SAMPLE_RATE` sont injectées par
/// `--dart-define` depuis le `.env` de la racine — recettes `just run` et
/// `just build` —, et leur absence ne veut pas dire la même chose : sans url
/// d'api on s'arrête net, car une valeur par défaut en dur masquerait une
/// configuration cassée ; sans DSN on démarre normalement, Sentry simplement
/// désactivé ; sans taux d'envoi on envoie tout, l'échantillonnage bornant un
/// coût sans jamais éteindre la collecte (cadrage §16).
///
/// Un taux **présent mais inutilisable** s'arrête en revanche ici, comme une
/// url d'api manquante : ces trois valeurs sont figées à la compilation, donc
/// une valeur fautive est un build cassé, vu au premier lancement. La refuser
/// plus tard — dans la closure de configuration du SDK — désactiverait
/// l'assainissement en silence.
///
/// Tout le reste du démarrage vit dans [_construireEtLancer], que
/// [demarrerAvecRapport] exécute — sous la zone de capture du SDK quand un DSN
/// est fourni. Rien qui puisse échouer ne se produit donc avant que le filet
/// soit tendu.
Future<void> main() async {
  // Avant tout le reste : le SDK Sentry parle au canal natif dès son
  // initialisation, et `PackageInfo.fromPlatform` en fait autant plus loin.
  WidgetsFlutterBinding.ensureInitialized();
  await demarrerAvecRapport(
    dsn: const String.fromEnvironment('SENTRY_DSN'),
    tauxEnvoi: tauxEnvoiValide(
      const String.fromEnvironment('SENTRY_SAMPLE_RATE'),
    ),
    lancer: _construireEtLancer,
  );
}

/// Construit les services partagés et monte l'application.
///
/// Tout le reste les reçoit : c'est ici, et nulle part ailleurs, qu'ils sont
/// instanciés.
Future<void> _construireEtLancer() async {
  const baseUrl = String.fromEnvironment('API_BASE_URL');
  // La seule attente de cette construction : `PackageInfo` parle à la
  // plateforme, et son résultat est requis avant `runApp`.
  final info = await PackageInfo.fromPlatform();
  final connectivite = ConnectivityService();
  runApp(
    ArpendoApp(
      client: ApiClient(
        config: ApiConfig(baseUrl: baseUrlValidee(baseUrl)),
        // `x.y.z+N` — le serveur journalise la version entière, la
        // comparaison, elle, ne porte que sur le numéro de build.
        clientVersion: '${info.version}+${info.buildNumber}',
        connectivite: connectivite,
      ),
      connectivite: connectivite,
      buildActuel: numeroDeBuildValide(info.buildNumber),
      // L'identifiant vient de la plateforme, jamais d'une constante : c'est
      // l'application réellement installée dont il faut ouvrir la fiche.
      magasin: MagasinService(identifiantApplication: info.packageName),
    ),
  );
}

/// Refuse un `buildNumber` non entier, avec la cause probable.
///
/// Sur Android, `package_info_plus` y met `versionCode` — toujours un
/// entier ; sur iOS (phase 2), il peut valoir la **version** (`1.2.3`) quand
/// aucun build n'est déclaré. Une frontière de plateforme se valide comme
/// `API_BASE_URL` : échouer ici donne un message, échouer dans `int.parse`
/// donnait un écran noir avant `runApp`.
int numeroDeBuildValide(String brut) {
  final numero = int.tryParse(brut);
  if (numero == null) {
    throw StateError(
      'buildNumber « $brut » n\'est pas un entier. Vérifier le champ '
      '`version: x.y.z+N` du pubspec — et, sur iOS, que le build est bien '
      'déclaré (package_info_plus y met sinon la version).',
    );
  }
  return numero;
}

/// Refuse une `API_BASE_URL` absente, avec la marche à suivre.
///
/// Séparée de [main] pour être prouvable en test — `String.fromEnvironment`
/// est figée à la compilation, un test ne peut pas la faire varier.
String baseUrlValidee(String brute) {
  if (brute.isEmpty) {
    throw StateError(
      'API_BASE_URL absente. Lancer par `just run` (ou `just build`), qui '
      "l'injecte en --dart-define depuis le .env de la racine — "
      'voir .env.example, section « Application ».',
    );
  }
  return brute;
}

/// Racine de l'application.
///
/// Pilotée par l'état (spec UX §2.1) : un `switch` **exhaustif** sur
/// [EtatDemarrage] choisit l'écran — un état ajouté ne compile pas tant que
/// chaque point de décision ne s'est pas prononcé.
///
/// Elle pose les jetons de conception du §1, dans les deux modes. Le mode
/// sombre est **disponible, jamais imposé** : `ThemeMode.system` le fait
/// suivre le réglage de l'appareil, et aucun réglage de l'application ne le
/// force.
class ArpendoApp extends StatelessWidget {
  /// Crée la racine sur des services déjà construits — par [main] en
  /// production, par le test sinon.
  const ArpendoApp({
    required this.client,
    required this.connectivite,
    required this.buildActuel,
    required this.magasin,
    super.key,
  });

  /// Seul point de contact avec le serveur, possédé par la racine : le
  /// `dispose` du `Provider` appelle [ApiClient.close].
  final ApiClient client;

  /// Lecture de l'état du réseau, partagée avec le ViewModel.
  final ConnectivityService connectivite;

  /// Le numéro de build installé, comparé aux seuils de `/version`.
  final int buildActuel;

  /// L'accès à la fiche du magasin, partagé par l'écran bloquant et la ligne
  /// 12 : un seul chemin vers le magasin, une seule paire de liens à tenir.
  final MagasinService magasin;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<ApiClient>(
          create: (_) => client,
          dispose: (_, c) => c.close(),
        ),
        ChangeNotifierProvider<DemarrageViewModel>(
          create: (contexte) {
            final modele = DemarrageViewModel(
              versions: VersionClient(contexte.read<ApiClient>()),
              connectivite: connectivite,
              buildActuel: buildActuel,
              ouvrirMagasin: magasin.ouvrirFiche,
            );
            unawaited(modele.demarrer());
            return modele;
          },
          // La séquence démarre avec l'application, pas à la première lecture.
          lazy: false,
        ),
      ],
      child: MaterialApp(
        // La liste générée porte déjà les trois délégués
        // `Global*Localizations` du SDK, en plus de celui des textes de l'app.
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        // Une seule locale livrée (cadrage §12.6). `fr-XA`, générée à côté
        // pour la vérification de longueur, est une locale de test : les
        // tests la pompent, l'application ne l'offre jamais.
        supportedLocales: const [Locale('fr')],
        theme: themeArpendo(Brightness.light),
        darkTheme: themeArpendo(Brightness.dark),
        themeMode: ThemeMode.system,
        home: Consumer<DemarrageViewModel>(
          builder: (_, modele, _) => switch (modele.etat) {
            // Le seul écran dont on ne sort pas (§11.2) : il remplace tout,
            // bandeau compris — un client qui ne parle plus à l'api n'a rien
            // d'utile à dire de son réseau.
            MiseAJourRequise() => EcranMiseAJour(
              onMettreAJour: magasin.ouvrirFiche,
            ),
            // Jamais un Menu mensonger (§2.1) : l'attente neutre tient les
            // trois autres états, et le bandeau vit sur son calque.
            Verification() || Injoignable() || Pret() => EcranAttente(
              etat: modele.etat,
              entreeBandeau: modele.entreeBandeau,
              onReessayer: modele.reessayer,
            ),
          },
        ),
      ),
    );
  }
}
