import 'package:flutter/material.dart';

import '../../app/theme/app_colors.dart';
import '../../core/widgets/policy_card.dart';
import '../policy/presentation/claim_guide.dart';

class ExploreScreen extends StatelessWidget {
  const ExploreScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Explore')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          const SectionHeader('Claim guides'),
          for (final entry in claimGuides.entries)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: Card(
                child: ExpansionTile(
                  shape: const Border(),
                  leading: Icon(policyIcon(entry.key), color: AppColors.forPolicyType(entry.key)),
                  title: Text(entry.value.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                  childrenPadding: const EdgeInsets.fromLTRB(AppSpacing.md, 0, AppSpacing.md, AppSpacing.md),
                  children: [
                    for (final (i, s) in entry.value.steps.indexed)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('${i + 1}. ', style: const TextStyle(fontWeight: FontWeight.w600)),
                            Expanded(child: Text(s)),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ),
          const SectionHeader('Coming soon'),
          // Future modules (P2/P3) shown as labelled tiles only — no placeholder flows.
          const Wrap(
            spacing: AppSpacing.sm,
            runSpacing: AppSpacing.sm,
            children: [
              _SoonTile(Icons.mail_outline_rounded, 'Gmail import'),
              _SoonTile(Icons.account_balance_wallet_outlined, 'DigiLocker'),
              _SoonTile(Icons.health_and_safety_outlined, 'Policy health check'),
              _SoonTile(Icons.family_restroom_rounded, 'Family coverage'),
            ],
          ),
        ],
      ),
    );
  }
}

class _SoonTile extends StatelessWidget {
  const _SoonTile(this.icon, this.label);
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: (MediaQuery.sizeOf(context).width - AppSpacing.md * 2 - AppSpacing.sm) / 2,
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: AppColors.textSecondary),
            const SizedBox(height: AppSpacing.sm),
            Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
            const Text('Coming soon', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
          ],
        ),
      ),
    ),
  );
}
