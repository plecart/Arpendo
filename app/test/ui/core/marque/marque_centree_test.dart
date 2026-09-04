import 'package:arpendo/l10n/generated/app_localizations.dart';
import 'package:arpendo/ui/core/marque/bloc_de_marque.dart';
import 'package:arpendo/ui/core/marque/marque_centree.dart';
import 'package:arpendo/ui/core/theme/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<Rect> _positionDuBloc(WidgetTester tester, {Widget? sous}) async {
  await tester.pumpWidget(
    MaterialApp(
      locale: const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: themeArpendo(Brightness.light),
      home: Scaffold(body: MarqueCentree(sous: sous)),
    ),
  );
  return tester.getRect(find.byType(BlocDeMarque));
}

void main() {
  testWidgets('le bloc est centré verticalement', (tester) async {
    final bloc = await _positionDuBloc(tester);

    final ecran = tester.getRect(find.byType(MaterialApp));
    expect(bloc.center.dy, moreOrLessEquals(ecran.center.dy, epsilon: 0.5));
  });

  testWidgets('ce qui paraît dessous ne le déplace pas', (tester) async {
    // **L'invariant que ce widget existe pour tenir.** Sans lui, chaque écran
    // le recopierait, et le logo sauterait au premier qui s'en écarterait.
    // Trois contenus de hauteurs très différentes, une seule position.
    final positions = {
      'rien': await _positionDuBloc(tester),
      'une ligne': await _positionDuBloc(tester, sous: const Text('Court.')),
      'un pavé': await _positionDuBloc(
        tester,
        sous: const SizedBox(height: 400, child: Text('Haut.')),
      ),
    };

    expect(
      positions.values.toSet(),
      hasLength(1),
      reason: 'mesuré : $positions',
    );
  });

  testWidgets('le contenu se place sous le bloc, jamais dessus', (
    tester,
  ) async {
    await _positionDuBloc(tester, sous: const Text('Dessous.'));

    expect(
      tester.getTopLeft(find.text('Dessous.')).dy,
      greaterThanOrEqualTo(tester.getBottomLeft(find.byType(BlocDeMarque)).dy),
    );
  });
}
