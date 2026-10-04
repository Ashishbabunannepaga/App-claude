import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/async_states.dart';
import '../../../core/widgets/policy_card.dart';
import '../data/models.dart';
import '../data/policy_repository.dart';

Color scoreColor(int score) => score >= 75
    ? AppColors.accent
    : score >= 50
    ? AppColors.warning
    : AppColors.error;

class PolicyHealthScreen extends ConsumerWidget {
  const PolicyHealthScreen({super.key, required this.policyId});
  final String policyId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final health = ref.watch(healthProvider(policyId));
    final policy = ref.watch(policyProvider(policyId)).value;
    return Scaffold(
      appBar: AppBar(title: const Text('Policy health')),
      body: AsyncValueView(
        value: health,
        onRetry: () => ref.invalidate(healthProvider(policyId)),
        data: (h) => !h.available
            ? EmptyView(icon: Icons.health_and_safety_outlined, title: 'Not enough details yet', message: h.disclaimer)
            : ListView(
                padding: const EdgeInsets.all(AppSpacing.md),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(AppSpacing.lg),
                      child: Row(
                        children: [
                          ScoreRing(score: h.score!),
                          const SizedBox(width: AppSpacing.lg),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(policy?.displayName ?? '', style: Theme.of(context).textTheme.titleMedium),
                                const SizedBox(height: AppSpacing.xs),
                                Text(
                                  '${h.strong.length} strong · ${h.attention.length} need attention · '
                                  '${h.notCovered.length} not covered',
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (h.strong.isNotEmpty) _Section('Strong', Icons.check_circle_rounded, AppColors.accent, h.strong),
                  if (h.attention.isNotEmpty)
                    _Section('Needs attention', Icons.warning_amber_rounded, AppColors.warning, h.attention),
                  if (h.notCovered.isNotEmpty)
                    _Section('Not covered', Icons.cancel_rounded, AppColors.error, h.notCovered),
                  if (h.notMentioned.isNotEmpty) ...[
                    const SectionHeader('Not mentioned in your document'),
                    Wrap(
                      spacing: AppSpacing.sm,
                      runSpacing: AppSpacing.sm,
                      children: [for (final label in h.notMentioned) Chip(label: Text(label))],
                    ),
                  ],
                  const SizedBox(height: AppSpacing.lg),
                  Text(h.disclaimer, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                  const SizedBox(height: AppSpacing.lg),
                ],
              ),
      ),
    );
  }
}

class ScoreRing extends StatelessWidget {
  const ScoreRing({super.key, required this.score, this.size = 88});
  final int score;
  final double size;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: size,
    height: size,
    child: Stack(
      alignment: Alignment.center,
      children: [
        SizedBox.expand(
          child: CircularProgressIndicator(
            value: score / 100,
            strokeWidth: 9,
            strokeCap: StrokeCap.round,
            backgroundColor: AppColors.border,
            color: scoreColor(score),
          ),
        ),
        Text(
          '$score%',
          style: TextStyle(fontSize: size / 4.4, fontWeight: FontWeight.w700),
        ),
      ],
    ),
  );
}

class _Section extends StatelessWidget {
  const _Section(this.title, this.icon, this.color, this.items);
  final String title;
  final IconData icon;
  final Color color;
  final List<HealthFinding> items;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      SectionHeader(title),
      Card(
        child: Column(
          children: [
            for (final f in items)
              ListTile(
                leading: Icon(icon, color: color),
                title: Text(f.label, style: const TextStyle(fontWeight: FontWeight.w600)),
                subtitle: Text(f.detail),
              ),
          ],
        ),
      ),
    ],
  );
}
