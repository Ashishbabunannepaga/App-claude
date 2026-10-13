import 'package:sentry_flutter/sentry_flutter.dart';

import 'config/env.dart';

/// Crash reporting with Sentry, off unless the build sets `--dart-define=SENTRY_DSN=...`.
///
/// Reports carry stack traces only: no screenshots, no view hierarchy, no user, no request data, and
/// breadcrumbs keep the event type but drop their text (it can contain policy details or answers).
Future<void> runWithErrorTracking(void Function() runApp) async {
  if (Env.sentryDsn.isEmpty) return runApp();
  await SentryFlutter.init((o) {
    o.dsn = Env.sentryDsn;
    o.environment = Env.name;
    o.sendDefaultPii = false;
    o.attachScreenshot = false;
    o.attachViewHierarchy = false;
    o.tracesSampleRate = 0;
    o.beforeSend = scrubEvent;
    o.beforeBreadcrumb = scrubBreadcrumb;
  }, appRunner: runApp);
}

SentryEvent? scrubEvent(SentryEvent event, Hint hint) {
  event.user = null;
  event.request = null;
  return event;
}

Breadcrumb? scrubBreadcrumb(Breadcrumb? crumb, Hint hint) {
  if (crumb == null) return null;
  return Breadcrumb(type: crumb.type, category: crumb.category, level: crumb.level, timestamp: crumb.timestamp);
}
