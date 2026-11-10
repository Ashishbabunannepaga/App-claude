import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:insureiq/app/theme/app_theme.dart';
import 'package:insureiq/core/security/app_lock.dart';
import 'package:insureiq/features/account/presentation/settings_screens.dart';
import 'package:insureiq/features/auth/data/auth_controller.dart';
import 'package:insureiq/features/auth/data/auth_repository.dart';
import 'package:insureiq/features/auth/presentation/login_screen.dart';
import 'package:insureiq/l10n/app_localizations.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// The "CapitUp may contact me" opt-in: optional, off by default, never required to sign up.
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

Future<void> _pump(
  WidgetTester tester,
  Widget screen, {
  List overrides = const [],
  Locale locale = const Locale('en'),
}) async {
  SharedPreferences.setMockInitialValues({});
  final prefs = await SharedPreferences.getInstance();
  await tester.pumpWidget(
    ProviderScope(
      overrides: [sharedPrefsProvider.overrideWithValue(prefs), ...overrides],
      child: MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: locale,
        theme: AppTheme.light(),
        home: screen,
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  test('AppUser reads contact_consent and defaults to off', () {
    expect(AppUser.fromJson({'id': 'a', 'contact_consent': true}).contactConsent, isTrue);
    expect(AppUser.fromJson({'id': 'a', 'contact_consent': false}).contactConsent, isFalse);
    expect(AppUser.fromJson({'id': 'a'}).contactConsent, isFalse);
  });

  test('OtpArgs carries the opt-in, off unless set', () {
    expect(OtpArgs('x', true, 30).contactConsent, isFalse);
    expect(OtpArgs('x', true, 30, contactConsent: true).contactConsent, isTrue);
  });

  for (final locale in const [Locale('en'), Locale('hi')]) {
    testWidgets('login: opt-in is unticked and not needed to continue [${locale.languageCode}]', (tester) async {
      await _pump(tester, const LoginScreen(), locale: locale);
      final optIn = tester.widget<Checkbox>(find.byKey(const Key('contact-consent')));
      expect(optIn.value, isFalse);

      await tester.enterText(find.byType(TextField), '9876543210');
      // Tick only the required privacy/terms box (the first checkbox).
      await tester.tap(find.byType(Checkbox).first);
      await tester.pump();
      expect(tester.widget<Checkbox>(find.byKey(const Key('contact-consent'))).value, isFalse);
      final button = tester.widget<FilledButton>(find.byType(FilledButton));
      expect(button.onPressed, isNotNull, reason: 'signing up must never require the contact opt-in');

      await tester.tap(find.byKey(const Key('contact-consent')));
      await tester.pump();
      expect(tester.widget<Checkbox>(find.byKey(const Key('contact-consent'))).value, isTrue);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('profile switch turns the opt-in on and off', (tester) async {
    final controller = _SignedIn(false);
    await _pump(
      tester,
      const NotificationSettingsScreen(),
      overrides: [authControllerProvider.overrideWith(() => controller)],
    );
    await tester.scrollUntilVisible(find.byKey(const Key('contact-consent-switch')), 100);
    expect(tester.widget<SwitchListTile>(find.byKey(const Key('contact-consent-switch'))).value, isFalse);

    await tester.tap(find.byKey(const Key('contact-consent-switch')));
    await tester.pumpAndSettle();
    expect(controller.changes.last, {'contact_consent': true});
    expect(tester.widget<SwitchListTile>(find.byKey(const Key('contact-consent-switch'))).value, isTrue);
  });
}
