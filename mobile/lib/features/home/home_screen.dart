import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme/app_colors.dart';
import '../../core/brand.dart';
import '../../core/push/push_prompt.dart';
import '../../core/ui/pressable.dart';
import '../../core/utils/formatters.dart';
import '../../core/widgets/async_states.dart';
import '../../core/widgets/policy_card.dart';
import '../account/data/account_repository.dart';
import '../auth/data/auth_controller.dart';
import '../coverage/coverage_data.dart';
import '../coverage/coverage_widgets.dart';
import '../insights/insights_screen.dart';
import '../policy/data/models.dart';
import '../policy/data/policy_repository.dart';
import 'home_hero.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final summary = ref.watch(portfolioProvider);
    final policies = ref.watch(policiesProvider);
    final first = user?.firstName ?? '';

    return Scaffold(
      body: PushPrompt(
        child: SafeArea(
          bottom: false,
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
                padding: const EdgeInsets.fromLTRB(AppSpacing.md, AppSpacing.sm, AppSpacing.md, 128),
                children: [
                  _Header(name: first),
                  const SizedBox(height: AppSpacing.md),
                  const AskBar(),
                  const SizedBox(height: AppSpacing.md),
                  HomeHero(hasPolicies: s.totalPolicies > 0, summary: s),
                  if (s.pendingVerification > 0) ...[
                    const SizedBox(height: AppSpacing.md),
                    _ReviewBanner(count: s.pendingVerification),
                  ],
                  const SectionHeader('What would you like to do?'),
                  const _Services(),
                  if (s.upcomingRenewals.isNotEmpty) ...[
                    const SectionHeader('Coming up'),
                    SizedBox(
                      height: 118,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: s.upcomingRenewals.length,
                        separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.sm),
                        itemBuilder: (_, i) => _RenewalCard(item: s.upcomingRenewals[i]),
                      ),
                    ),
                  ],
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
                            child: PolicyCard(
                              policy: p,
                              onTap: () => context.push(p.verified ? '/policy/${p.id}' : '/policy/${p.id}/verify'),
                            ),
                          ),
                        ),
                  ],
                  const SizedBox(height: AppSpacing.sm),
                  const _EarnStrip(),
                  const SizedBox(height: AppSpacing.md),
                  const ExpertReviewCard(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Header extends ConsumerWidget {
  const _Header({required this.name});
  final String name;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balance = ref.watch(rewardsProvider).value?.balance;
    final count = ref.watch(unreadCountProvider).value ?? 0;
    ref.listen(rewardsProvider, (prev, next) {
      final before = prev?.value?.balance, after = next.value?.balance;
      if (before != null && after != null && after > before) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppColors.ink,
            content: Row(
              children: [
                const CoinIcon(size: 26),
                const SizedBox(width: 10),
                Text('+${after - before} coins earned', style: const TextStyle(fontWeight: FontWeight.w800)),
              ],
            ),
          ),
        );
      }
    });
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const BrandLogo(height: 38),
            const Spacer(),
            Pressable(
              semanticLabel: 'Coins: ${balance ?? 0}. Open rewards',
              onTap: () async {
                await context.push('/rewards');
                ref.invalidate(rewardsProvider);
              },
              child: Container(
                padding: const EdgeInsets.fromLTRB(12, 5, 5, 5),
                decoration: BoxDecoration(color: AppColors.goldTint, borderRadius: BorderRadius.circular(20)),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '${balance ?? 0}',
                      style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.goldText),
                    ),
                    const SizedBox(width: 6),
                    const CoinIcon(size: 24),
                  ],
                ),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Pressable(
              semanticLabel: 'Notifications',
              onTap: () async {
                await context.push('/notifications');
                ref.invalidate(unreadCountProvider);
              },
              child: Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.border),
                ),
                child: Badge(
                  isLabelVisible: count > 0,
                  label: Text('$count'),
                  child: const Icon(Icons.notifications_none_rounded),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.md),
        Text(name.isEmpty ? 'Hello there' : 'Hi $name', style: Theme.of(context).textTheme.headlineMedium),
        const Text('Here\'s where your cover stands today.', style: TextStyle(color: AppColors.textSecondary)),
      ],
    );
  }
}

class _ReviewBanner extends StatelessWidget {
  const _ReviewBanner({required this.count});
  final int count;

  @override
  Widget build(BuildContext context) => Pressable(
    onTap: () => context.go('/portfolio'),
    child: Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(color: AppColors.warningTint, borderRadius: BorderRadius.circular(AppSpacing.radius)),
      child: Row(
        children: [
          const Icon(Icons.fact_check_rounded, color: AppColors.warning),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              '$count ${count == 1 ? 'policy needs' : 'policies need'} a quick check from you',
              style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.warningText),
            ),
          ),
          const Icon(Icons.chevron_right_rounded, color: AppColors.warningText),
        ],
      ),
    ),
  );
}

/// Illustrated shortcuts to everything the app can do.
class _Services extends ConsumerWidget {
  const _Services();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    Future<void> withPolicy(String suffix, {Set<String>? types, required String empty}) async {
      final id = await pickPolicy(context, ref, types: types);
      if (!context.mounted) return;
      if (id == null) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(empty)));
        return;
      }
      context.push('/policy/$id$suffix');
    }

    final tiles = <Widget>[
      ServiceTile(
        icon: Icons.add_moderator_rounded,
        label: 'Add policy',
        color: AppColors.primary,
        onTap: () => context.push('/add'),
      ),
      ServiceTile(
        icon: Icons.fact_check_rounded,
        label: 'Coverage report',
        color: AppColors.motor,
        onTap: () async {
          final id = await pickPolicy(context, ref);
          if (!context.mounted) return;
          id == null ? context.push('/report/sample') : context.push('/policy/$id/report');
        },
      ),
      ServiceTile(
        icon: Icons.auto_awesome_rounded,
        label: 'Ask AI',
        color: AppColors.life,
        onTap: () => withPolicy('/ask', empty: 'Add a policy first, then you can ask questions about it.'),
      ),
      ServiceTile(
        icon: Icons.support_agent_rounded,
        label: 'Claim help',
        color: AppColors.warning,
        onTap: () => context.go('/explore'),
      ),
      ServiceTile(
        icon: Icons.family_restroom_rounded,
        label: 'Family',
        color: AppColors.health,
        onTap: () => context.push('/family'),
      ),
      ServiceTile(
        icon: Icons.groups_rounded,
        label: 'Nominees',
        color: AppColors.primaryDark,
        onTap: () => withPolicy('/nominees', empty: 'Add a policy first to record its nominees.'),
      ),
      ServiceTile(
        icon: Icons.compare_arrows_rounded,
        label: 'Compare',
        color: AppColors.motor,
        onTap: () => context.push('/compare'),
      ),
      ServiceTile(
        icon: Icons.emergency_rounded,
        label: 'Emergency card',
        color: AppColors.error,
        onTap: () => context.push('/emergency'),
      ),
    ];
    return GridView.count(
      crossAxisCount: 4,
      mainAxisSpacing: AppSpacing.md,
      crossAxisSpacing: AppSpacing.sm,
      childAspectRatio: 0.78,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      children: tiles,
    );
  }
}

class _RenewalCard extends StatelessWidget {
  const _RenewalCard({required this.item});
  final RenewalItem item;

  @override
  Widget build(BuildContext context) {
    final urgent = item.daysToExpiry <= 30;
    final color = AppColors.forPolicyType(item.policyType);
    return Pressable(
      onTap: () => context.push('/policy/${item.policyId}'),
      child: Container(
        width: 220,
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: urgent ? AppColors.warningTint : AppColors.surface,
          borderRadius: BorderRadius.circular(AppSpacing.radius),
          border: Border.all(color: urgent ? Colors.transparent : AppColors.border),
          boxShadow: urgent ? null : AppShadows.card,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(policyIcon(item.policyType), color: color, size: 20),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    item.insurer ?? policyTypeLabel(item.policyType),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
            const Spacer(),
            Text(
              '${item.daysToExpiry}',
              style: TextStyle(
                fontSize: 34,
                height: 1,
                fontWeight: FontWeight.w800,
                color: urgent ? AppColors.warningText : AppColors.textPrimary,
              ),
            ),
            Text(
              'days left · ends ${formatShortDate(item.endDate)}',
              style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _EarnStrip extends StatelessWidget {
  const _EarnStrip();

  @override
  Widget build(BuildContext context) => Pressable(
    onTap: () => context.push('/rewards'),
    child: Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFFFFE9B0), AppColors.goldTint]),
        borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
      ),
      child: const Row(
        children: [
          CoinIcon(size: 44),
          SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Earn coins for staying organised',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppColors.ink),
                ),
                Text(
                  'Add policies, nominees and family members.',
                  style: TextStyle(color: AppColors.goldText, fontSize: 13),
                ),
              ],
            ),
          ),
          Icon(Icons.arrow_forward_rounded, color: AppColors.goldText),
        ],
      ),
    ),
  );
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
          'Worth a look',
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
