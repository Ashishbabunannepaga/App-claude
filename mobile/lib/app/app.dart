import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'router.dart';
import 'theme/app_theme.dart';

class InsureApp extends ConsumerWidget {
  const InsureApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
    title: 'InsureIQ',
    debugShowCheckedModeBanner: false,
    theme: AppTheme.light(),
    routerConfig: ref.watch(routerProvider),
  );
}
