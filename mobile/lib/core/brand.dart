import 'package:flutter/material.dart';

import '../app/theme/app_colors.dart';

/// Brand identity in one place. Swap the name here and drop the logo into assets/brand/logo.png.
class Brand {
  static const name = 'CapitUp';
  static const logoAsset = 'assets/brand/logo.png';
}

/// The brand logo from assets/brand/logo.png, or a text wordmark until that file is added.
class BrandLogo extends StatelessWidget {
  const BrandLogo({super.key, this.height = 28, this.onDark = false});
  final double height;
  final bool onDark;

  @override
  Widget build(BuildContext context) => Semantics(
    label: Brand.name,
    image: true,
    child: Image.asset(
      Brand.logoAsset,
      height: height,
      fit: BoxFit.contain,
      excludeFromSemantics: true,
      errorBuilder: (_, _, _) => _Wordmark(height: height, onDark: onDark),
    ),
  );
}

class _Wordmark extends StatelessWidget {
  const _Wordmark({required this.height, required this.onDark});
  final double height;
  final bool onDark;

  @override
  Widget build(BuildContext context) {
    final main = onDark ? Colors.white : AppColors.primary;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: height,
          height: height,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppColors.secondary, AppColors.primary],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(height * 0.3),
          ),
          child: Icon(Icons.trending_up_rounded, color: Colors.white, size: height * 0.7),
        ),
        SizedBox(width: height * 0.25),
        Text.rich(
          TextSpan(
            children: [
              TextSpan(
                text: 'Capit',
                style: TextStyle(color: main),
              ),
              TextSpan(
                text: 'Up',
                style: TextStyle(color: onDark ? const Color(0xFF8FB4FF) : AppColors.secondary),
              ),
            ],
          ),
          style: TextStyle(fontSize: height * 0.72, fontWeight: FontWeight.w800, letterSpacing: -0.5),
        ),
      ],
    );
  }
}
