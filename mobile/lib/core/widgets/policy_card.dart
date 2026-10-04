import 'package:flutter/material.dart';

import '../../app/theme/app_colors.dart';
import '../../features/policy/data/models.dart';
import '../utils/formatters.dart';

IconData policyIcon(String type) => switch (type) {
  'health' => Icons.favorite_rounded,
  'life' => Icons.shield_rounded,
  'motor' => Icons.directions_car_rounded,
  _ => Icons.description_rounded,
};

class StatusChip extends StatelessWidget {
  const StatusChip({super.key, required this.policy});
  final Policy policy;

  @override
  Widget build(BuildContext context) {
    final (label, color) = !policy.verified
        ? ('Review needed', AppColors.warning)
        : switch (policy.status) {
            'active' => ('Active', AppColors.accent),
            'expiring_soon' => ('Expires in ${policy.daysToExpiry} days', AppColors.warning),
            'expired' => ('Expired', AppColors.error),
            _ => ('Dates missing', AppColors.textSecondary),
          };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20)),
      child: Text(
        label,
        style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 12),
      ),
    );
  }
}

class PolicyCard extends StatelessWidget {
  const PolicyCard({super.key, required this.policy, this.onTap});
  final Policy policy;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.forPolicyType(policy.policyType);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.md),
          child: Row(
            children: [
              CircleAvatar(
                backgroundColor: color.withValues(alpha: 0.12),
                child: Icon(policyIcon(policy.policyType), color: color),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      policy.displayName,
                      style: Theme.of(context).textTheme.titleMedium,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${policyTypeLabel(policy.policyType)} · ${formatInrCompact(policy.sumInsured)} cover',
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    StatusChip(policy: policy),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, color: AppColors.textSecondary),
            ],
          ),
        ),
      ),
    );
  }
}

class SectionHeader extends StatelessWidget {
  const SectionHeader(this.title, {super.key, this.action});
  final String title;
  final Widget? action;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: AppSpacing.lg, bottom: AppSpacing.sm),
    child: Row(
      children: [
        Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium)),
        ?action,
      ],
    ),
  );
}
