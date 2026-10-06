import 'package:flutter/material.dart';

/// CapitUp v2 design tokens (mirrors replica/design/tokens.json; contrast-checked there).
/// Keep all colours here; widgets never hard-code hex values.
///
/// Status and category base colours are for icons and fills. Text in those colours uses the `*Text` versions.
class AppColors {
  // Brand: deep teal + warm gold (from the CapitUp logo).
  static const ink = Color(0xFF0B2B2E);
  static const primary = Color(0xFF0B7A75);
  static const primaryDark = Color(0xFF07524F);
  static const gold = Color(0xFFF5A81C);
  static const goldText = Color(0xFF7A4E00);
  static const goldTint = Color(0xFFFFF3D6);

  /// Kept for existing call sites: the interactive accent is the brand teal.
  static const secondary = primary;

  // Status.
  static const accent = Color(0xFF17A06A); // success
  static const warning = Color(0xFFE59E0B);
  static const error = Color(0xFFE5484D);
  static const successText = Color(0xFF0F7A4E);
  static const warningText = Color(0xFF8A5300);
  static const errorText = Color(0xFFB42318);
  static const unknownText = Color(0xFF66706D);
  static const successTint = Color(0xFFE4F6EE);
  static const warningTint = Color(0xFFFFF1D6);
  static const errorTint = Color(0xFFFDECEC);

  // Surfaces and text.
  static const background = Color(0xFFF6F8F7);
  static const surface = Colors.white;
  static const surfaceTint = Color(0xFFEAF5F3);
  static const textPrimary = Color(0xFF0F1F1D);
  static const textSecondary = Color(0xFF55635F);
  static const border = Color(0xFFE1E8E6);

  // Policy types.
  static const health = Color(0xFFE5484D);
  static const life = Color(0xFF6D5BD0);
  static const motor = Color(0xFF2F7DE1);
  static const other = Color(0xFF55635F);

  static Color forPolicyType(String type) => switch (type) {
    'health' => health,
    'life' => life,
    'motor' => motor,
    _ => other,
  };

  /// Pale fill behind a policy-type icon.
  static Color tintForPolicyType(String type) => forPolicyType(type).withValues(alpha: 0.12);
}

class AppSpacing {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
  static const radius = 20.0;
  static const radiusLg = 28.0;
  static const radiusSm = 14.0;
}

class AppShadows {
  static const card = [BoxShadow(color: Color(0x140B2B2E), blurRadius: 18, offset: Offset(0, 6))];
  static const lift = [BoxShadow(color: Color(0x290B2B2E), blurRadius: 28, offset: Offset(0, 12))];
}
