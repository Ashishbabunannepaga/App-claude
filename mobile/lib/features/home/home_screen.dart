import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme/app_colors.dart';
import '../../core/utils/formatters.dart';
import '../../core/widgets/async_states.dart';
import '../../core/widgets/policy_card.dart';
import '../auth/data/auth_controller.dart';
import '../policy/data/models.dart';
import '../policy/data/policy_repository.dart';

String _greeting() {
  final h = DateTime.now().hour;
  return h < 12
      ? 'Good morning'
      : h < 17
      ? 'Good afternoon'
      : 'Good evening';
}

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final summary = ref.watch(portfolioProvider);
    final policies = ref.watch(policiesProvider);

    return Scaffold(
      appBar: AppBar(title: Text('${_greeting()}${user?.firstName.isNotEmpty == true ? ', ${user!.firstName}' : ''}')),
      body: RefreshIndicator(
        onRefresh: () async => invalidatePolicies(ref),
        child: AsyncValueView(
          value: summary,
          onRetry: () => invalidatePolicies(ref),
          data: (s) => s.totalPolicies == 0
              ? ListView(
                  children: [
                    const SizedBox(height: 80),
                    EmptyView(
                      icon: Icons.add_moderator_rounded,
                      title: 'Add your first policy',
                      message:
                          'Upload a health, life or motor policy. We\'ll read it and explain it in plain language.',
                      action: FilledButton.icon(
                        onPressed: () => context.push('/add'),
                        icon: const Icon(Icons.upload_file_rounded),
                        label: const Text('Add policy'),
                      ),
                    ),
                  ],
                )
              : ListView(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  children: [
                    _CoverageCard(summary: s),
                    if (s.pendingVerification > 0) ...[
                      const SizedBox(height: AppSpacing.md),
                      Card(
                        color: const Color(0xFFFFF7E6),
                        child: ListTile(
                          leading: const Icon(Icons.fact_check_rounded, color: AppColors.warning),
                          title: Text(
                            '${s.pendingVerification} '
                            '${s.pendingVerification == 1 ? 'policy needs' : 'policies need'} your review',
                          ),
                          trailing: const Icon(Icons.chevron_right_rounded),
                          onTap: () => context.go('/portfolio'),
                        ),
                      ),
                    ],
                    if (s.upcomingRenewals.isNotEmpty) ...[
                      const SectionHeader('Upcoming renewal'),
                      _RenewalCard(item: s.upcomingRenewals.first),
                    ],
                    const SectionHeader('Quick actions'),
                    const _QuickActions(),
                    SectionHeader(
                      'Your policies',
                      action: TextButton(onPressed: () => context.go('/portfolio'), child: const Text('See all')),
                    ),
                    ...?policies.value
                        ?.take(3)
                        .map(
                          (p) => Padding(
                            padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                            child: PolicyCard(policy: p, onTap: () => context.push('/policy/${p.id}')),
                          ),
                        ),
                  ],
                ),
        ),
      ),
    );
  }
}

class _CoverageCard extends StatelessWidget {
  const _CoverageCard({required this.summary});
  final PortfolioSummary summary;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(AppSpacing.lg),
    decoration: BoxDecoration(color: AppColors.primary, borderRadius: BorderRadius.circular(AppSpacing.radius)),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Your insurance', style: TextStyle(color: Colors.white70)),
        const SizedBox(height: AppSpacing.xs),
        Text(
          '${summary.activePolicies} active ${summary.activePolicies == 1 ? 'policy' : 'policies'}',
          style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: AppSpacing.md),
        Row(
          children: [
            _Stat('Health cover', formatInrCompact(summary.healthCover)),
            _Stat('Life cover', formatInrCompact(summary.lifeCover)),
            _Stat('Yearly premium', formatInrCompact(summary.totalAnnualPremium)),
          ],
        ),
      ],
    ),
  );
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w700),
        ),
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
      ],
    ),
  );
}

class _RenewalCard extends StatelessWidget {
  const _RenewalCard({required this.item});
  final RenewalItem item;

  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      leading: Icon(policyIcon(item.policyType), color: AppColors.forPolicyType(item.policyType)),
      title: Text('${item.insurer ?? policyTypeLabel(item.policyType)} · ${policyTypeLabel(item.policyType)}'),
      subtitle: Text('Expires ${formatDate(item.endDate)}'),
      trailing: Text(
        '${item.daysToExpiry} days',
        style: TextStyle(
          color: item.daysToExpiry <= 30 ? AppColors.warning : AppColors.textSecondary,
          fontWeight: FontWeight.w700,
        ),
      ),
      onTap: () => context.push('/policy/${item.policyId}'),
    ),
  );
}

class _QuickActions extends ConsumerWidget {
  const _QuickActions();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    Future<void> pickPolicyThen(String suffix) async {
      final policies = ref.read(policiesProvider).value ?? [];
      final verified = policies.where((p) => p.verified).toList();
      if (verified.length == 1) {
        context.push('/policy/${verified.first.id}$suffix');
      } else {
        context.go('/portfolio');
      }
    }

    Widget tile(IconData icon, String label, VoidCallback onTap) => Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
          child: Column(
            children: [
              CircleAvatar(
                radius: 26,
                backgroundColor: const Color(0xFFE3ECFF),
                child: Icon(icon, color: AppColors.secondary),
              ),
              const SizedBox(height: AppSpacing.xs),
              Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            ],
          ),
        ),
      ),
    );
    return Row(
      children: [
        tile(Icons.add_rounded, 'Add policy', () => context.push('/add')),
        tile(Icons.auto_awesome_rounded, 'Ask AI', () => pickPolicyThen('/ask')),
        tile(Icons.support_agent_rounded, 'Claim help', () => context.go('/explore')),
        tile(Icons.family_restroom_rounded, 'Family', () => context.go('/profile')),
      ],
    );
  }
}
