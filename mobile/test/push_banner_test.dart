import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:insureiq/core/push/push_service.dart';

void main() {
  Widget host() => MaterialApp(
    scaffoldMessengerKey: PushService.messengerKey,
    home: const Scaffold(body: SizedBox()),
  );

  testWidgets('a push that arrives while the app is open shows a banner that opens its link', (tester) async {
    await tester.pumpWidget(host());
    String? opened;
    PushService.showForeground(
      title: 'Your policy is ready',
      body: 'Tap to review the details.',
      link: '/policy/abc',
      viewLabel: 'View',
      open: (link) => opened = link,
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 750)); // let the banner slide in
    expect(find.text('Your policy is ready\nTap to review the details.'), findsOneWidget);
    await tester.tap(find.text('View'));
    expect(opened, '/policy/abc');
  });

  testWidgets('no link means no View button, and an empty push shows nothing', (tester) async {
    await tester.pumpWidget(host());
    PushService.showForeground(title: 'Renewal in 30 days', body: null, link: null, viewLabel: 'View', open: (_) {});
    await tester.pump();
    expect(find.text('Renewal in 30 days'), findsOneWidget);
    expect(find.text('View'), findsNothing);

    PushService.messengerKey.currentState!.clearSnackBars();
    await tester.pump();
    PushService.showForeground(title: ' ', body: null, link: '/x', viewLabel: 'View', open: (_) {});
    await tester.pump();
    expect(find.byType(SnackBar), findsNothing);
  });
}
