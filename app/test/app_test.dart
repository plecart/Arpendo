import 'package:arpendo/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets("l'application démarre sur un écran vide", (tester) async {
    await tester.pumpWidget(const ArpendoApp());

    expect(find.byType(Scaffold), findsOneWidget);
  });
}
