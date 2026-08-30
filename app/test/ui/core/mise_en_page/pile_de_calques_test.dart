import 'package:arpendo/ui/core/mise_en_page/pile_de_calques.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Encoches simulées : une barre d'état en haut, une barre de gestes en bas.
const _encoches = EdgeInsets.only(top: 24, bottom: 30);

/// Monte [enfant] dans un `MediaQuery` que le moteur pourrait produire.
///
/// [padding] et [viewPadding] sont **distincts à dessein**, parce qu'ils le
/// sont sur un appareil : `dart:ui` documente que `padding.bottom` vaut
/// `viewPadding.bottom` clavier fermé, et **zéro** clavier ouvert — la barre
/// de gestes est alors recouverte (`ui/window.dart`, `FlutterView.padding`).
/// Les poser égaux avec un clavier ouvert décrirait un état qui n'existe pas,
/// et un test bâti dessus épinglerait une valeur qu'aucun écran ne rencontre.
Widget _sousEncoches(
  Widget enfant, {
  EdgeInsets padding = EdgeInsets.zero,
  EdgeInsets? viewPadding,
  double clavier = 0,
}) => Directionality(
  textDirection: TextDirection.ltr,
  child: MediaQuery(
    data: MediaQueryData(
      padding: padding,
      viewPadding: viewPadding ?? padding,
      viewInsets: EdgeInsets.only(bottom: clavier),
    ),
    child: enfant,
  ),
);

/// Rend `rembourrageBas` mesuré sous [media].
Future<double> _rembourrageSous(
  WidgetTester tester,
  Widget Function(Widget) media,
) async {
  late double mesure;
  await tester.pumpWidget(
    media(
      Builder(
        builder: (context) {
          mesure = rembourrageBas(context);
          return const SizedBox();
        },
      ),
    ),
  );
  return mesure;
}

/// Un calque qui note s'il a reçu l'appui, et qui remplit l'espace offert.
Widget _cible(void Function() onTap) =>
    SizedBox.expand(child: GestureDetector(onTap: onTap));

/// Un calque repérable, assez petit pour que sa position se lise.
Widget _repere(Key cle) => SizedBox(key: cle, width: 10, height: 10);

void main() {
  testWidgets("le calque de z le plus haut reçoit l'appui, quel que soit "
      "l'ordre d'écriture", (tester) async {
    var carteTouchee = false;
    var bandeauTouche = false;

    // Les deux calques sont écrits dans le désordre : sans tri, `bandeau`
    // serait peint en premier, donc dessous, et c'est la carte qui recevrait
    // l'appui. C'est ce que ce test refuse.
    await tester.pumpWidget(
      _sousEncoches(
        PileDeCalques(
          children: {
            Calque.bandeau: _cible(() => bandeauTouche = true),
            Calque.carte: _cible(() => carteTouchee = true),
          },
        ),
      ),
    );
    await tester.tapAt(tester.getCenter(find.byType(PileDeCalques)));

    expect(bandeauTouche, isTrue);
    expect(carteTouchee, isFalse);
  });

  testWidgets('la carte touche le bord, tout autre calque non', (tester) async {
    const cleCarte = Key('carte');
    const cleHeader = Key('header');

    await tester.pumpWidget(
      _sousEncoches(
        PileDeCalques(
          children: {
            Calque.carte: _repere(cleCarte),
            Calque.header: _repere(cleHeader),
          },
        ),
        padding: _encoches,
      ),
    );

    expect(tester.getTopLeft(find.byKey(cleCarte)).dy, 0);
    expect(tester.getTopLeft(find.byKey(cleHeader)).dy, _encoches.top);
  });

  testWidgets('la safe area protège aussi du bas, pas seulement du haut', (
    tester,
  ) async {
    const cleControles = Key('controles');

    await tester.pumpWidget(
      _sousEncoches(
        PileDeCalques(
          children: {
            // Ancré en bas de son calque : c'est là que la barre de gestes
            // mord, et c'est la bande où le §1.4 place toutes les actions
            // fréquentes.
            Calque.controles: Align(
              alignment: Alignment.bottomLeft,
              child: _repere(cleControles),
            ),
          },
        ),
        padding: _encoches,
      ),
    );

    final ecran = tester.getSize(find.byType(PileDeCalques)).height;

    expect(
      ecran - tester.getBottomLeft(find.byKey(cleControles)).dy,
      _encoches.bottom,
    );
  });

  testWidgets('clavier fermé, le rembourrage bas vaut la barre de gestes', (
    tester,
  ) async {
    final mesure = await _rembourrageSous(
      tester,
      (enfant) => _sousEncoches(enfant, padding: _encoches),
    );

    expect(mesure, _encoches.bottom);
  });

  testWidgets('clavier ouvert, la barre de gestes ne compte pas deux fois', (
    tester,
  ) async {
    // L'état réel d'un appareil clavier ouvert : le clavier recouvre la barre
    // de gestes, donc `padding.bottom` retombe à zéro pendant que
    // `viewPadding.bottom` reste entier. Lire `viewPadding` ici écarterait le
    // bouton de 30 dp de trop.
    final mesure = await _rembourrageSous(
      tester,
      (enfant) => _sousEncoches(
        enfant,
        padding: EdgeInsets.only(top: _encoches.top),
        viewPadding: _encoches,
        clavier: 300,
      ),
    );

    expect(mesure, 300);
  });

  testWidgets('le rembourrage bas est une somme, pas un maximum', (
    tester,
  ) async {
    // Cas **synthétique** : un appareil ne présente jamais les deux non nuls
    // en même temps, puisque le clavier recouvre la barre de gestes. Il est
    // néanmoins nécessaire, et c'est le seul qui distingue `+` de `max`, de
    // `min` ou d'une lecture unique — trois implémentations que les cas réels
    // laissent toutes passer.
    const clavier = 300.0;
    final mesure = await _rembourrageSous(
      tester,
      (enfant) => _sousEncoches(enfant, padding: _encoches, clavier: clavier),
    );

    expect(mesure, clavier + _encoches.bottom);
  });

  testWidgets('sous une safe area, le rembourrage bas est déjà consommé', (
    tester,
  ) async {
    // `SafeArea` applique le rembourrage **et** le retire du `MediaQuery` de
    // ses descendants (`widgets/safe_area.dart`, `MediaQuery.removePadding`).
    // Une feuille modale s'affiche par le `Navigator`, hors de la pile, et
    // reçoit donc la valeur entière du test précédent.
    final mesure = await _rembourrageSous(
      tester,
      (enfant) => _sousEncoches(SafeArea(child: enfant), padding: _encoches),
    );

    expect(mesure, 0);
  });
}
