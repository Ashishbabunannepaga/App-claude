import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:insureiq/app/theme/app_theme.dart';
import 'package:insureiq/features/account/data/account_repository.dart';
import 'package:insureiq/features/auth/data/auth_controller.dart';
import 'package:insureiq/features/auth/data/auth_repository.dart';
import 'package:insureiq/features/home/home_hero.dart';
import 'package:insureiq/l10n/app_localizations.dart';

/// "Talk to an expert": an expert call is CapitUp contacting the client, so it needs the contact consent,
/// asked for in the same dialog, unticked by default.
class _SignedIn extends AuthController {
  _SignedIn(this.consent);
  final bool consent;
  final changes = <Map<String, dynamic>>[];

  @override
  AuthState build() => AuthState(AuthStatus.signedIn, AppUser(id: 'u1', contactConsent: consent));

  @override
  Future<void> updateProfile(Map<String, dynamic> changes) async {
    this.changes.add(changes);
    state = AuthState(AuthStatus.signedIn, AppUser(id: 'u1', contactConsent: changes['contact_consent'] as bool));
  }
}

class _Support extends AccountRepository {
  _Support() : super(Dio());
  final sent = <String>[];

  @override
  Future<void> contactSupport(String category, String message) async => sent.add(category);
}

Future<(_SignedIn, _Support)> _pump(
  WidgetTester tester, {
  required bool consent,
  Locale locale = const Locale('en'),
}) async {
  final auth = _SignedIn(consent);
  final support = _Support();
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(() => auth),
        accountRepositoryProvider.overrideWithValue(support),
      ],
      child: MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: locale,
        theme: AppTheme.light(),
        home: const Scaffold(body: Center(child: ExpertReviewCard())),
      ),
    ),
  );
  await tester.pumpAndSettle();
  await tester.tap(find.byType(ExpertReviewCard));
  await tester.pumpAndSettle();
  return (auth, support);
}

TextButton _requestButton(WidgetTester tester) =>
    tester.widget<TextButton>(find.byKey(const Key('expert-request-call')));

void main() {
  for (final locale in const [Locale('en'), Locale('hi')]) {
    testWidgets('without consent: unticked box, no request until ticked [${locale.languageCode}]', (tester) async {
      final (auth, support) = await _pump(tester, consent: false, locale: locale);
      final box = tester.widget<CheckboxListTile>(find.byKey(const Key('expert-contact-consent')));
      expect(box.value, isFalse);
      expect(_requestButton(tester).onPressed, isNull);

      await tester.tap(find.byKey(const Key('expert-contact-consent')));
      await tester.pump();
      expect(_requestButton(tester).onPressed, isNotNull);
      await tester.tap(find.byKey(const Key('expert-request-call')));
      await tester.pumpAndSettle();

      expect(auth.changes, [
        {'contact_consent': true},
      ]);
      expect(support.sent, ['expert_review']);
    });
  }

  testWidgets('already opted in: no box, request goes straight through', (tester) async {
    final (auth, support) = await _pump(tester, consent: true);
    expect(find.byKey(const Key('expert-contact-consent')), findsNothing);
    await tester.tap(find.byKey(const Key('expert-request-call')));
    await tester.pumpAndSettle();
    expect(auth.changes, isEmpty);
    expect(support.sent, ['expert_review']);
  });

  testWidgets('cancel sends nothing and changes no consent', (tester) async {
    final (auth, support) = await _pump(tester, consent: false);
    await tester.tap(find.byKey(const Key('expert-contact-consent')));
    await tester.pump();
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(auth.changes, isEmpty);
    expect(support.sent, isEmpty);
  });
}
