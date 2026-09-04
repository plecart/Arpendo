import 'package:arpendo/domain/bandeau/lignes.dart';
import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/bandeau/bandeau.dart';
import 'package:arpendo/ui/core/boutons/bouton_pleine_largeur.dart';
import 'package:arpendo/ui/core/marque/bloc_de_marque.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:arpendo/ui/demarrage/ecran_attente.dart';
import 'package:arpendo/ui/demarrage/etat_demarrage.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../tool/allonger_arb.dart' show marqueurDebut, marqueurFin;

/// L'accroche du bloc marque, isolée pour le test du texte cité du cadrage §1.
Widget accroche(BuildContext context) =>
    Text(AppLocalizations.of(context).marqueAccroche);

/// Les composants dont on vérifie le rendu sous la locale allongée.
///
/// **Toute issue qui ajoute un composant portant du texte l'ajoute ici.** La
/// liste est le seul endroit à tenir : le test qui la parcourt, lui, ne bouge
/// pas, et couvre le nouveau composant sans une ligne de plus.
///
/// Y figurer ne suffit pas toujours : ce que le garde ne voit pas — littéral
/// dans un `RichText` nu ou un `SelectableText`, texte qu'un composant ne
/// construit qu'à l'interaction, `semanticsLabel`, texte clippé par un
/// conteneur trop petit — est énuméré dans `app/README.md`, section « Ce que
/// prouve le test `fr-XA` », qui en est la source unique.
final composants = <String, WidgetBuilder>{
  // Le bloc entier — signe, logotype, accroche — plutôt que l'accroche seule
  // qu'il remplace ici : c'est en composition que la largeur contraint.
  'le bloc de marque': (_) => const BlocDeMarque(),
  // Les deux lignes que #43 livre, et les deux formes du bandeau : sans action,
  // puis avec ses deux boutons — c'est la seconde qui est contrainte, puisque
  // les libellés s'allongent de 30 % eux aussi.
  'le bandeau sans action (ligne 5)': (_) =>
      Bandeau(entree: ligneReseauAbsent()),
  'le bandeau à deux actions (ligne 12)': (_) => Bandeau(
    entree: ligneMiseAJourRecommandee(onMettreAJour: () {}, onFermer: () {}),
  ),
  // Son libellé vient de l'appelant : n'importe quelle valeur d'ARB prouve le
  // chemin de rendu sous la locale allongée — celle-ci est la première livrée.
  // Les libellés réels (« Réessayer », « Mettre à jour ») arrivent avec leurs
  // écrans, qui s'inscrivent ici à leur tour.
  'le bouton pleine largeur': (context) => BoutonPleineLargeur(
    libelle: AppLocalizations.of(context).marqueAccroche,
    onPressed: () {},
  ),
  // L'état d'échec, le plus riche en textes : message §2.1, « Réessayer »,
  // bloc de marque, et la ligne 5 sur son calque.
  "l'écran d'attente en échec": (_) => EcranAttente(
    etat: const Injoignable(),
    entreeBandeau: ligneReseauAbsent(),
    onReessayer: () {},
  ),
};

/// Vrai si [texte] est **une seule** valeur venue de l'ARB.
///
/// Contrôler les deux extrémités ne suffit pas : `'⟦a⟧ — ⟦b⟧'` les satisfait
/// alors qu'il concatène deux valeurs autour d'un séparateur écrit en dur —
/// c'est la forme qu'on écrit spontanément dès qu'un composant compose deux
/// textes. On exige donc en plus que l'intérieur ne porte aucun marqueur.
///
/// Effet de bord voulu : des marqueurs vidés rendent la condition fausse pour
/// **tout** texte, y compris légitime. Le garde ne peut pas être désarmé en
/// silence en changeant une constante — il rougit bruyamment.
bool vientEntierementDeLArb(String texte) {
  if (!texte.startsWith(marqueurDebut) || !texte.endsWith(marqueurFin)) {
    return false;
  }
  final interieur = texte.substring(
    marqueurDebut.length,
    texte.length - marqueurFin.length,
  );
  return !interieur.contains(marqueurDebut) && !interieur.contains(marqueurFin);
}

/// Écran de référence de conception (spec UX §0) : le cas le plus contraint.
const ecranDeReference = Size(360, 800);

/// Monte [constructeur] sous [locale], avec les deux locales générées reconnues.
///
/// La liste des locales est celle de `gen-l10n`, et non celle de la production
/// (`fr` seul) : c'est ce qui permet au test de pomper `fr-XA` sans que l'app
/// la livre jamais.
Widget sousLocale(Locale locale, WidgetBuilder constructeur) => MaterialApp(
  locale: locale,
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  theme: themeArpendo(Brightness.light),
  home: Scaffold(body: Builder(builder: constructeur)),
);

void main() {
  testWidgets("l'accroche rend le texte cité du cadrage §1", (tester) async {
    await tester.pumpWidget(sousLocale(const Locale('fr'), accroche));

    expect(find.text('prends du terrain'), findsOneWidget);
  });

  for (final MapEntry(key: nom, value: constructeur) in composants.entries) {
    testWidgets("$nom : son texte vient de l'ARB, sans déborder ni couper", (
      tester,
    ) async {
      tester.view.physicalSize = ecranDeReference;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        sousLocale(const Locale('fr', 'XA'), constructeur),
      );

      // Les `Text` que l'app écrit — `Text` comme `Text.rich`. On lit le texte
      // **visible**, et lui seul : `toPlainText` inclut par défaut le
      // `semanticsLabel` d'un span, qui masquerait un littéral derrière un
      // libellé conforme, et un `U+FFFC` par `WidgetSpan`, qui ferait rougir à
      // tort un texte de l'ARB portant une icône en ligne.
      final textes = tester
          .widgetList<Text>(
            // `skipOffstage: false` : un littéral posé sous un `Offstage` ou
            // dans la branche non affichée d'un `IndexedStack` est absent de
            // la recherche par défaut, et passerait le garde sans être vu.
            find.byType(Text, skipOffstage: false),
          )
          .map(
            (t) =>
                t.data ??
                t.textSpan!.toPlainText(
                  includeSemanticsLabels: false,
                  includePlaceholders: false,
                ),
          )
          // Un texte vide n'affiche rien : il ne peut pas être une chaîne en
          // dur, et le mobilier Material en pose (`AboutDialog`).
          .where((texte) => texte.isNotEmpty);
      expect(
        textes,
        isNotEmpty,
        reason: 'un composant qui ne rend aucun texte ne prouve rien',
      );
      for (final texte in textes) {
        expect(
          vientEntierementDeLArb(texte),
          isTrue,
          reason:
              "« $texte » ne vient pas entièrement de l'ARB : soit c'est une "
              "chaîne en dur, soit une valeur de l'ARB est concaténée à un "
              'morceau écrit dans le code. Un composant qui affiche du texte '
              'écrit par Material lui-même — compteur de `TextField`, boutons '
              "d'`AboutDialog` — ne se teste pas ainsi : ce texte est localisé "
              'par `GlobalMaterialLocalizations`, pas par notre ARB',
        );
      }

      // La troncature ne se lit que sur l'objet de rendu, et on ne l'exige que
      // de ce qui est **peint** — d'où `skipOffstage` laissé à sa valeur par
      // défaut ici, à l'inverse de la recherche des textes ci-dessus. Un
      // `Offstage` n'est pas même mis en page ; une branche non affichée d'un
      // `IndexedStack` l'est, mais n'est pas peinte : dans les deux cas, une
      // coupure que personne ne voit n'est pas un défaut, là où un littéral
      // qui y dort en est un le jour où la branche s'affiche. L'écart ne joue
      // que dans ce sens : les paragraphes retenus sont par construction un
      // sous-ensemble des textes contrôlés ci-dessus.
      //
      // On vise les `RichText` issus d'un `Text` : `Icon` en rend un aussi
      // (`widgets/icon.dart:328`), et les prendre tous ferait rougir un
      // composant à icône sœur sur un caractère de fonte. Une icône posée *en
      // ligne*, elle, reste dans le lot — sans dommage : `Icon` ne pose ni
      // `maxLines` ni `ellipsis`, donc ne se déclare jamais tronquée.
      for (final paragraphe in tester.renderObjectList<RenderParagraph>(
        find.descendant(of: find.byType(Text), matching: find.byType(RichText)),
      )) {
        expect(
          paragraphe.didExceedMaxLines,
          isFalse,
          reason:
              'texte tronqué : la spec UX §0 veut des conteneurs qui '
              'grandissent, pas qui coupent',
        );
      }
      expect(
        tester.takeException(),
        isNull,
        reason:
            'la spec UX §0 exige que tout conteneur absorbe +30 % de longueur '
            'sur ${ecranDeReference.width.toInt()} × '
            '${ecranDeReference.height.toInt()} dp',
      );
    });
  }
}
