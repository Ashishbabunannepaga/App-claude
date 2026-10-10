import 'package:flutter/foundation.dart';

/// Build-time configuration via `--dart-define`. The app holds NO secrets:
/// only the public API base URL, environment name and public Firebase client identifiers.
class Env {
  static const String name = String.fromEnvironment('ENV', defaultValue: 'development');
  static const String _apiBaseUrl = String.fromEnvironment('API_BASE_URL');

  static bool get isProduction => name == 'production';

  /// Defaults point at a backend on the developer machine
  /// (Android emulator reaches the host via 10.0.2.2).
  static String get apiBaseUrl {
    if (_apiBaseUrl.isNotEmpty) return _apiBaseUrl;
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) return 'http://10.0.2.2:8000/api/v1';
    return 'http://localhost:8000/api/v1';
  }

  /// Origin of the API, used to resolve relative URLs returned by the server.
  static Uri get apiOrigin {
    final uri = Uri.parse(apiBaseUrl);
    return Uri(scheme: uri.scheme, host: uri.host, port: uri.port);
  }

  // Firebase (push). Public client config, not secrets. Push is disabled when unset.
  static const firebaseApiKey = String.fromEnvironment('FIREBASE_API_KEY');
  static const firebaseProjectId = String.fromEnvironment('FIREBASE_PROJECT_ID');
  static const firebaseSenderId = String.fromEnvironment('FIREBASE_SENDER_ID');
  static const firebaseAndroidAppId = String.fromEnvironment('FIREBASE_ANDROID_APP_ID');
  static const firebaseIosAppId = String.fromEnvironment('FIREBASE_IOS_APP_ID');

  // Legal pages are served by the backend (/privacy, /terms), so they work as soon as the API is live.
  static const String _privacyUrl = String.fromEnvironment('PRIVACY_URL');
  static const String _termsUrl = String.fromEnvironment('TERMS_URL');
  static String get privacyPolicyUrl => _privacyUrl.isNotEmpty ? _privacyUrl : '${apiOrigin.toString()}/privacy';
  static String get termsUrl => _termsUrl.isNotEmpty ? _termsUrl : '${apiOrigin.toString()}/terms';

  static const String supportEmail = String.fromEnvironment('SUPPORT_EMAIL', defaultValue: 'support@example.com');
  static const String grievanceOfficer = String.fromEnvironment(
    'GRIEVANCE_OFFICER',
    defaultValue: 'Grievance Officer, grievance@example.com',
  );

  /// Settings a store build must not ship with. Empty in a correct production build.
  static List<String> releaseProblems() => [
    if (!apiBaseUrl.startsWith('https://')) 'API_BASE_URL must be https:// (got $apiBaseUrl)',
    if (supportEmail.endsWith('@example.com')) 'SUPPORT_EMAIL is a placeholder',
    if (grievanceOfficer.contains('example.com')) 'GRIEVANCE_OFFICER is a placeholder',
  ];
}
