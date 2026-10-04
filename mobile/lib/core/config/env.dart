import 'dart:io' show Platform;

/// Build-time configuration via `--dart-define`. The app holds NO secrets:
/// only the public API base URL and the environment name.
class Env {
  static const String name = String.fromEnvironment('ENV', defaultValue: 'development');
  static const String _apiBaseUrl = String.fromEnvironment('API_BASE_URL');

  static bool get isProduction => name == 'production';

  /// Defaults point at a backend on the developer machine
  /// (Android emulator reaches the host via 10.0.2.2).
  static String get apiBaseUrl {
    if (_apiBaseUrl.isNotEmpty) return _apiBaseUrl;
    return Platform.isAndroid ? 'http://10.0.2.2:8000/api/v1' : 'http://localhost:8000/api/v1';
  }

  /// Origin of the API, used to resolve relative URLs returned by the server.
  static Uri get apiOrigin {
    final uri = Uri.parse(apiBaseUrl);
    return uri.replace(path: '', query: null);
  }

  static const String privacyPolicyUrl = String.fromEnvironment(
    'PRIVACY_URL',
    defaultValue: 'https://example.com/privacy',
  ); // TODO: real URL
  static const String termsUrl = String.fromEnvironment(
    'TERMS_URL',
    defaultValue: 'https://example.com/terms',
  ); // TODO: real URL
  static const String supportEmail = String.fromEnvironment(
    'SUPPORT_EMAIL',
    defaultValue: 'support@example.com',
  ); // TODO: real address
}
