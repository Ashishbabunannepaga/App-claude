import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/app.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // TODO(Week 7): Firebase.initializeApp() for push notifications; (Week 9) Crashlytics.
  runApp(const ProviderScope(child: InsureApp()));
}
