import 'package:flutter_test/flutter_test.dart';
import 'package:insureiq/core/observability.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

void main() {
  test('crash reports drop user and request data', () {
    final event = SentryEvent(
      user: SentryUser(id: 'u1'),
      request: SentryRequest(url: 'https://api/x', data: {'question': 'Is maternity covered?'}),
    );
    final out = scrubEvent(event, Hint())!;
    expect(out.user, isNull);
    expect(out.request, isNull);
  });

  test('breadcrumbs keep the type but lose their text', () {
    final out = scrubBreadcrumb(
      Breadcrumb(message: 'Answer: your room rent is capped', type: 'debug', data: {'k': 'v'}),
      Hint(),
    )!;
    expect(out.type, 'debug');
    expect(out.message, isNull);
    expect(out.data, anyOf(isNull, isEmpty));
  });
}
