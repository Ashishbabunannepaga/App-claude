import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:go_router/go_router.dart';

import '../../features/account/data/account_repository.dart';
import '../config/env.dart';

/// Push notifications via Firebase Cloud Messaging (APNs on iOS through Firebase).
///
/// Disabled unless the FIREBASE_* dart-defines are provided, so development builds run without a
/// Firebase project. iOS additionally needs the Push Notifications capability enabled in Xcode and
/// an APNs key uploaded to Firebase.
class PushService {
  PushService._();

  static bool _initialised = false;
  static bool get enabled => _initialised;

  static FirebaseOptions? get _options {
    if (kIsWeb || Env.firebaseApiKey.isEmpty) return null;
    final appId = defaultTargetPlatform == TargetPlatform.iOS ? Env.firebaseIosAppId : Env.firebaseAndroidAppId;
    if (appId.isEmpty) return null;
    return FirebaseOptions(
      apiKey: Env.firebaseApiKey,
      appId: appId,
      messagingSenderId: Env.firebaseSenderId,
      projectId: Env.firebaseProjectId,
    );
  }

  static Future<void> init() async {
    final options = _options;
    if (options == null) return;
    try {
      await Firebase.initializeApp(options: options);
      _initialised = true;
    } catch (e) {
      debugPrint('Push disabled: $e');
    }
  }

  /// Ask permission, register this device with the backend and route notification taps.
  static Future<void> registerForUser(AccountRepository repo, GoRouter router) async {
    if (!_initialised) return;
    final messaging = FirebaseMessaging.instance;
    final settings = await messaging.requestPermission();
    if (settings.authorizationStatus == AuthorizationStatus.denied) return;
    final platform = defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android';

    Future<void> register(String? token) async {
      if (token == null) return;
      try {
        await repo.registerDevice(token, platform);
      } catch (e) {
        debugPrint('Device registration failed: $e');
      }
    }

    await register(await messaging.getToken());
    messaging.onTokenRefresh.listen(register);

    void open(RemoteMessage m) {
      final link = m.data['deep_link'] as String?;
      if (link != null && link.startsWith('/')) router.push(link);
    }

    FirebaseMessaging.onMessageOpenedApp.listen(open);
    final initial = await messaging.getInitialMessage();
    if (initial != null) open(initial);
  }
}
