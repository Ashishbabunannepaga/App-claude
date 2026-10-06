import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme/app_colors.dart';
import '../../core/brand.dart';
import '../../core/push/push_prompt.dart';
import '../../core/utils/formatters.dart';
import '../../core/widgets/async_states.dart';
import '../../core/widgets/policy_card.dart';
import '../account/data/account_repository.dart';
import '../coverage/coverage_data.dart';
import '../coverage/coverage_widgets.dart';
import 'home_hero.dart';
import '../insights/insights_screen.dart';
import '../auth/data/auth_controller.dart';
import '../policy/data/models.dart';
import '../policy/data/policy_repository.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final summary = ref.watch(portfolioProvider);
    final policies = ref.watch(policiesProvider);

    return Scaffold(
      appBar: AppBar(
        leadingWidth: 96,
        toolbarHeight: 64,
        leading: const Padding(
          padding: EdgeInsets.only(left: AppSpacing.md),
          child: Center(child: _Coins()),
        ),
        title: const BrandLogo(height: 34),
        centerTitle: true,
        actions: [
          const _Bell(),
          Padding(
            padding: const EdgeInsets.only(right: AppSpacing.md),
            child: _Avatar(name: user?.firstName ?? ''),
          ),
        ],
      ),
      body: PushPrompt(
        child: RefreshIndicator(
          onRefresh: () async {
            invalidatePolicies(ref);
            ref.invalidate(unreadCountProvider);
            ref.invalidate(rewardsProvider);
          },
          child: AsyncValueView(
            value: summary,
            onRetry: () => invalidatePolicies(ref),
            data: (s) => ListView(
              padding: const EdgeInsets.all(AppSpacing.md),
              children: [
                HomeHero(name: user?.firstName ?? '', hasPolicies: s.totalPolicies > 0),
                if (s.totalPolicies > 0) ...[const SizedBox(height: AppSpacing.md), _CoverageCard(summary: s)],
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
                const _TopInsights(),
                if (s.totalPolicies > 0) ...[
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
                const SizedBox(height: AppSpacing.md),
                const ExpertReviewCard(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Coins extends ConsumerWidget {
  const _Coins();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balance = ref.watch(rewardsProvider).value?.balance;
    return Semantics(
      button: true,
      label: 'Coins: ${balance ?? 0}. Open rewards',
      excludeSemantics: true,
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: () async {
          await context.push('/rewards');
          ref.invalidate(rewardsProvider);
        },
        child: Container(
          padding: const EdgeInsets.fromLTRB(10, 4, 4, 4),
          decoration: BoxDecoration(color: const Color(0xFFFFF4D6), borderRadius: BorderRadius.circular(20)),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '${balance ?? 0}',
                style: const TextStyle(fontWeight: FontWeight.w800, color: Color(0xFF7A4E00)),
              ),
              const SizedBox(width: 4),
              const CoinIcon(size: 22),
            ],
          ),
        ),
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.name});
  final String name;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    label: 'Profile',
    excludeSemantics: true,
    child: InkWell(
      customBorder: const CircleBorder(),
      onTap: () => context.go('/profile'),
      child: CircleAvatar(
        radius: 17,
        backgroundColor: AppColors.primary,
        child: name.isEmpty
            ? const Icon(Icons.person_rounded, color: Colors.white, size: 20)
            : Text(
                name[0].toUpperCase(),
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
              ),
      ),
    ),
  );
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
        tile(Icons.family_restroom_rounded, 'Family', () => context.push('/family')),
      ],
    );
  }
}

class _Bell extends ConsumerWidget {
  const _Bell();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(unreadCountProvider).value ?? 0;
    return IconButton(
      tooltip: 'Notifications',
      onPressed: () async {
        await context.push('/notifications');
        ref.invalidate(unreadCountProvider);
      },
      icon: Badge(
        isLabelVisible: count > 0,
        label: Text('$count'),
        child: const Icon(Icons.notifications_none_rounded),
      ),
    );
  }
}

/// The three most important coverage insights (gaps, renewals, nominees).
class _TopInsights extends ConsumerWidget {
  const _TopInsights();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(insightsProvider).value?.items ?? const <Insight>[];
    if (items.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          'Insurance check-up',
          action: TextButton(
            onPressed: () => context.push('/insights'),
            child: Text(items.length > 3 ? 'All ${items.length}' : 'Details'),
          ),
        ),
        for (final i in items.take(3)) InsightTile(i),
      ],
    );
  }
}
