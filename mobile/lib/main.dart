import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app/app.dart';
import 'core/push/push_service.dart';
import 'core/security/app_lock.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Indian formats everywhere (₹ lakh grouping, "4 Oct 2026"), independent of the device locale.
  Intl.defaultLocale = 'en_IN';
  await initializeDateFormatting('en_IN');
  final prefs = await SharedPreferences.getInstance();
  await PushService.init();
  // TODO(Week 9): Crashlytics (no policy content in crash reports).
  runApp(ProviderScope(overrides: [sharedPrefsProvider.overrideWithValue(prefs)], child: const InsureApp()));
}
