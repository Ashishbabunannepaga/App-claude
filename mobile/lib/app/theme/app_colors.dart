import 'package:flutter/material.dart';

/// Design tokens. Keep all colours here; widgets never hard-code hex values.
class AppColors {
  static const primary = Color(0xFF0B2A5B); // deep blue
  static const secondary = Color(0xFF2F6FED); // bright blue
  static const accent = Color(0xFF16A36A); // green
  static const warning = Color(0xFFE59E0B); // amber
  static const error = Color(0xFFD93B3B); // red
  static const background = Color(0xFFF5F7FB); // very light neutral
  static const surface = Colors.white;
  static const textPrimary = Color(0xFF111827);
  static const textSecondary = Color(0xFF5B6475);
  static const border = Color(0xFFE3E8F0);

  static const health = Color(0xFF16A36A);
  static const life = Color(0xFF7C4DFF);
  static const motor = Color(0xFF2F6FED);
  static const other = Color(0xFF5B6475);

  static Color forPolicyType(String type) => switch (type) {
    'health' => health,
    'life' => life,
    'motor' => motor,
    _ => other,
  };
}

class AppSpacing {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
  static const radius = 16.0;
}
