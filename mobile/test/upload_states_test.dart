import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:insureiq/app/theme/app_theme.dart';
import 'package:insureiq/core/network/api_exception.dart';
import 'package:insureiq/core/security/app_lock.dart';
import 'package:insureiq/features/policy/data/models.dart';
import 'package:insureiq/features/policy/data/policy_repository.dart';
import 'package:insureiq/features/policy/presentation/processing_screen.dart';
import 'package:insureiq/l10n/app_localizations.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Upload edge cases (T022) and the processing screen's failure, offline and timeout states (T017).
class _Repo extends PolicyRepository {
  _Repo(this.next) : super(Dio());

  /// What each poll returns: a document, or an ApiException to throw (a dropped connection).
  final List<Object> next;
  int polls = 0;
  int retries = 0;
  ApiException? retryError;

  @override
  Future<PolicyDocument> document(String id) async {
    final item = next[polls < next.length ? polls : next.length - 1];
    polls++;
    if (item is ApiException) throw item;
    return item as PolicyDocument;
  }

  @override
  Future<PolicyDocument> retry(String documentId) async {
    retries++;
    if (retryError != null) throw retryError!;
    return PolicyDocument(id: documentId, status: 'uploaded');
  }
}

PolicyDocument _doc(String status, [String? code]) => PolicyDocument(id: 'd1', status: status, errorCode: code);

Future<void> _pump(WidgetTester tester, _Repo repo, {Locale locale = const Locale('en')}) async {
  SharedPreferences.setMockInitialValues({});
  final prefs = await SharedPreferences.getInstance();
  final router = GoRouter(
    initialLocation: '/processing',
    routes: [
      GoRoute(path: '/', builder: (_, _) => const Text('HOME')),
      GoRoute(path: '/add', builder: (_, _) => const Text('ADD')),
      GoRoute(path: '/add/manual', builder: (_, _) => const Text('MANUAL')),
      GoRoute(
        path: '/processing',
        builder: (_, _) => const ProcessingScreen(documentId: 'd1'),
      ),
    ],
  );
  await tester.pumpWidget(
    ProviderScope(
      overrides: [sharedPrefsProvider.overrideWithValue(prefs), policyRepositoryProvider.overrideWithValue(repo)],
      child: MaterialApp.router(
        routerConfig: router,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: locale,
        theme: AppTheme.light(),
      ),
    ),
  );
  await tester.pump();
}

void main() {
  test('not_a_policy has its own message; same-file failures are not retryable', () {
    expect(_doc('failed', 'not_a_policy').errorText, contains('insurance policy'));
    for (final code in PolicyDocument.permanentErrors) {
      expect(_doc('failed', code).canRetry, isFalse, reason: code);
    }
    expect(_doc('failed', 'ai_unavailable').canRetry, isTrue);
    expect(_doc('failed', 'ocr_unavailable').canRetry, isTrue);
    expect(_doc('processing').canRetry, isFalse);
  });

  for (final locale in const [Locale('en'), Locale('hi')]) {
    testWidgets('a file that can never be read offers another file, not a retry [${locale.languageCode}]', (
      tester,
    ) async {
      await _pump(tester, _Repo([_doc('failed', 'pdf_password_protected')]), locale: locale);
      expect(find.byKey(const Key('processing-retry')), findsNothing);
      await tester.tap(find.byKey(const Key('processing-another-file')));
      await tester.pumpAndSettle();
      expect(find.text('ADD'), findsOneWidget);
    });
  }

  testWidgets('a temporary failure offers Try again and starts reading again', (tester) async {
    final repo = _Repo([_doc('failed', 'ai_unavailable'), _doc('processing')]);
    await _pump(tester, repo);
    await tester.tap(find.byKey(const Key('processing-retry')));
    await tester.pump();
    expect(repo.retries, 1);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    await tester.pump(const Duration(seconds: 2));
  });

  testWidgets('a dropped connection shows a message and keeps checking until it is back', (tester) async {
    final repo = _Repo([
      _doc('processing'),
      ApiException('network', 'No internet connection. Check your connection and try again.'),
      _doc('failed', 'not_a_policy'),
    ]);
    await _pump(tester, repo);
    await tester.pump(const Duration(seconds: 2));
    expect(find.byKey(const Key('processing-error')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget, reason: 'still waiting, not a dead end');
    await tester.pump(const Duration(seconds: 2));
    expect(find.byKey(const Key('processing-error')), findsNothing);
    expect(find.byKey(const Key('processing-another-file')), findsOneWidget);
  });

  testWidgets('after 3 minutes the spinner stops: Try again or go home, never a spinner forever', (tester) async {
    final repo = _Repo([_doc('processing')])
      ..retryError = ApiException('still_processing', "We're still reading this document. Please wait a minute.");
    await _pump(tester, repo);
    await tester.pump(const Duration(minutes: 3, seconds: 4));
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.byKey(const Key('processing-retry')), findsOneWidget);

    await tester.tap(find.byKey(const Key('processing-retry')));
    await tester.pump();
    expect(find.textContaining('still reading'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget, reason: 'goes back to watching the document');

    await tester.pump(const Duration(minutes: 3, seconds: 4));
    await tester.tap(find.text(lookupAppLocalizations(const Locale('en')).backToHome));
    await tester.pumpAndSettle();
    expect(find.text('HOME'), findsOneWidget);
  });

  test('several photos go up as one request: file plus pages in order', () async {
    final dio = Dio();
    FormData? sent;
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          sent = options.data as FormData;
          handler.resolve(Response(requestOptions: options, statusCode: 201, data: {'id': 'd1', 'status': 'uploaded'}));
        },
      ),
    );
    final doc = await PolicyRepository(dio).upload(
      Uint8List.fromList([1]),
      'page1.jpg',
      morePages: [
        (Uint8List.fromList([2]), 'page2.jpg'),
        (Uint8List.fromList([3]), 'page3.jpg'),
      ],
    );
    expect(doc.id, 'd1');
    expect(sent!.files.map((f) => '${f.key}:${f.value.filename}').toList(), [
      'file:page1.jpg',
      'pages:page2.jpg',
      'pages:page3.jpg',
    ]);
  });
}
