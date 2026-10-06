import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/demo_badge.dart';
import '../../auth/data/auth_controller.dart';
import '../../../core/widgets/async_states.dart';
import '../../../core/widgets/policy_card.dart';
import '../data/models.dart';
import '../data/policy_repository.dart';
import 'claim_guide.dart';
import 'policy_health_screen.dart';

class PolicyDetailScreen extends ConsumerWidget {
  const PolicyDetailScreen({super.key, required this.policyId});
  final String policyId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final policy = ref.watch(policyProvider(policyId));
    return Scaffold(
      appBar: AppBar(
        title: const Text('Policy'),
        actions: [if (policy.value != null) _Menu(policy: policy.value!)],
      ),
      body: AsyncValueView(
        value: policy,
        onRetry: () => ref.invalidate(policyProvider(policyId)),
        data: (p) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(policyProvider(policyId)),
          child: ListView(
            padding: const EdgeInsets.all(AppSpacing.md),
            children: [
              _Header(policy: p),
              if (!p.verified) ...[
                const SizedBox(height: AppSpacing.md),
                Card(
                  color: AppColors.warningTint,
                  child: ListTile(
                    leading: const Icon(Icons.fact_check_rounded, color: AppColors.warning),
                    title: const Text('Please review the extracted details'),
                    trailing: const Icon(Icons.chevron_right_rounded),
                    onTap: () => context.push('/policy/${p.id}/verify'),
                  ),
                ),
              ],
              const SizedBox(height: AppSpacing.md),
              _Actions(policy: p),
              if (p.policyType != 'other') ...[
                const SizedBox(height: AppSpacing.md),
                Card(
                  color: AppColors.surfaceTint,
                  child: ListTile(
                    leading: const Icon(Icons.fact_check_rounded, color: AppColors.secondary),
                    title: const Text('Coverage report', style: TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: const Text('What is covered, what has limits and what is not — item by item'),
                    trailing: const Icon(Icons.chevron_right_rounded),
                    onTap: () => context.push('/policy/${p.id}/report'),
                  ),
                ),
              ],
              if (p.policyType == 'health' || p.policyType == 'motor') _HealthCard(policyId: p.id),
              const SizedBox(height: AppSpacing.md),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.groups_rounded, color: AppColors.secondary),
                      title: const Text('Nominees', style: TextStyle(fontWeight: FontWeight.w600)),
                      subtitle: Text(
                        p.nominees.isEmpty
                            ? (p.policyType == 'life' ? 'No nominee recorded — add one' : 'Not recorded')
                            : p.nominees.map((n) => '${n.fullName} ${n.sharePercent}%').join(', '),
                        style: TextStyle(
                          color: p.nominees.isEmpty && p.policyType == 'life' ? AppColors.warning : null,
                        ),
                      ),
                      trailing: const Icon(Icons.chevron_right_rounded),
                      onTap: () => context.push('/policy/${p.id}/nominees'),
                    ),
                    if (p.documentId != null) ...[
                      const Divider(height: 1),
                      ListTile(
                        leading: const Icon(Icons.article_outlined, color: AppColors.secondary),
                        title: const Text('Policy clauses', style: TextStyle(fontWeight: FontWeight.w600)),
                        subtitle: const Text('Benefits, exclusions, waiting periods and limits — word for word'),
                        trailing: const Icon(Icons.chevron_right_rounded),
                        onTap: () => context.push('/policy/${p.id}/clauses'),
                      ),
                    ],
                  ],
                ),
              ),
              if (p.members.isNotEmpty) ...[
                const SectionHeader('Who is covered'),
                Wrap(
                  spacing: AppSpacing.sm,
                  runSpacing: AppSpacing.sm,
                  children: [
                    for (final m in p.members)
                      Chip(
                        avatar: const Icon(Icons.person_rounded, size: 18),
                        label: Text('${m.fullName} · ${humanise(m.relation)}'),
                      ),
                  ],
                ),
              ],
              const SectionHeader('Understand your policy'),
              _SummaryCard(policyId: p.id),
              const SectionHeader('Key details'),
              _KeyDetails(policy: p),
              if (p.details.isNotEmpty) ...[
                const SectionHeader('Coverage details'),
                _CoverageDetails(details: p.details),
              ],
              const SizedBox(height: AppSpacing.xl),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.policy});
  final Policy policy;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.forPolicyType(policy.policyType);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
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
                      Text(policy.displayName, style: Theme.of(context).textTheme.titleLarge),
                      Text(
                        '${policyTypeLabel(policy.policyType)} insurance${policy.planName != null ? ' · ${policy.planName}' : ''}',
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Text(formatInr(policy.sumInsured), style: Theme.of(context).textTheme.headlineMedium),
            Text(
              policy.policyType == 'motor' ? 'Insured declared value' : 'Cover',
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.md),
            StatusChip(policy: policy),
            const SizedBox(height: AppSpacing.sm),
            Text('Valid ${formatDate(policy.startDate)} – ${formatDate(policy.endDate)}'),
            Text(
              'Premium ${formatInr(policy.premium)}${policy.paymentFrequency != null ? ' (${humanise(policy.paymentFrequency!)})' : ''}',
            ),
          ],
        ),
      ),
    );
  }
}

class _Actions extends StatelessWidget {
  const _Actions({required this.policy});
  final Policy policy;

  @override
  Widget build(BuildContext context) {
    Widget action(IconData icon, String label, VoidCallback onTap) => Expanded(
      child: Card(
        child: InkWell(
          borderRadius: BorderRadius.circular(AppSpacing.radius),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
            child: Column(
              children: [
                Icon(icon, color: AppColors.secondary),
                const SizedBox(height: AppSpacing.xs),
                Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ),
      ),
    );
    return Row(
      children: [
        action(Icons.chat_bubble_rounded, 'Ask AI', () => context.push('/policy/${policy.id}/ask')),
        const SizedBox(width: AppSpacing.sm),
        action(Icons.event_repeat_rounded, 'Renewal', () => _showRenewal(context, policy)),
        const SizedBox(width: AppSpacing.sm),
        action(Icons.support_agent_rounded, 'Claim help', () => _showClaimGuide(context, policy.policyType)),
      ],
    );
  }

  void _showRenewal(BuildContext context, Policy p) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (_) => _RenewalSheet(policyId: p.id),
    );
  }

  void _showClaimGuide(BuildContext context, String type) {
    final guide = claimGuides[type] ?? claimGuides['other']!;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.75,
        builder: (context, controller) => ListView(
          controller: controller,
          padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.xl),
          children: [
            Text(guide.title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpacing.md),
            for (final (i, step) in guide.steps.indexed)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(radius: 14, child: Text('${i + 1}', style: const TextStyle(fontSize: 12))),
                title: Text(step),
              ),
            const SectionHeader('Documents usually required'),
            for (final d in guide.documents)
              ListTile(
                contentPadding: EdgeInsets.zero,
                dense: true,
                leading: const Icon(Icons.check_circle_outline_rounded, color: AppColors.accent),
                title: Text(d),
              ),
            const SizedBox(height: AppSpacing.md),
            const Text(
              'Always follow the claim process stated in your policy and by your insurer.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryCard extends ConsumerWidget {
  const _SummaryCard({required this.policyId});
  final String policyId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summary = ref.watch(summaryProvider(policyId));
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: summary.when(
          loading: () => const Padding(
            padding: EdgeInsets.all(AppSpacing.md),
            child: LoadingView(message: 'Reading your policy…'),
          ),
          error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(summaryProvider(policyId))),
          data: (s) => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DemoAiBadge(provider: s.provider),
              Text(s.headline, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: AppSpacing.sm),
              for (final point in s.keyPoints) _Bullet(point, Icons.check_circle_rounded, AppColors.accent),
              if (s.watchOuts.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.sm),
                const Text('Watch out for', style: TextStyle(fontWeight: FontWeight.w600)),
                for (final w in s.watchOuts) _Bullet(w, Icons.warning_amber_rounded, AppColors.warning),
              ],
              const SizedBox(height: AppSpacing.sm),
              Text(s.disclaimer, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
            ],
          ),
        ),
      ),
    );
  }
}

class _Bullet extends StatelessWidget {
  const _Bullet(this.text, this.icon, this.color);
  final String text;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: color),
        const SizedBox(width: AppSpacing.sm),
        Expanded(child: Text(text)),
      ],
    ),
  );
}

class _KeyDetails extends StatelessWidget {
  const _KeyDetails({required this.policy});
  final Policy policy;

  @override
  Widget build(BuildContext context) {
    final rows = <(String, String)>[
      ('Policy number', policy.policyNumber ?? '—'),
      ('Insurer', policy.insurer ?? '—'),
      ('Plan', policy.planName ?? '—'),
      ('Start date', formatDate(policy.startDate)),
      ('End date', formatDate(policy.endDate)),
      ('Premium', formatInr(policy.premium)),
      ('Cover', formatInr(policy.sumInsured)),
    ];
    return Card(
      child: Column(
        children: [
          for (final (label, value) in rows)
            ListTile(
              dense: true,
              title: Text(label, style: const TextStyle(color: AppColors.textSecondary)),
              trailing: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 200),
                child: Text(
                  value,
                  textAlign: TextAlign.right,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _CoverageDetails extends StatelessWidget {
  const _CoverageDetails({required this.details});
  final Map<String, dynamic> details;

  @override
  Widget build(BuildContext context) => Card(
    child: Column(
      children: [
        for (final e in details.entries)
          ListTile(
            title: Text(humanise(e.key), style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Text(e.value is List ? (e.value as List).join(', ') : e.value.toString()),
          ),
      ],
    ),
  );
}

class _Menu extends ConsumerWidget {
  const _Menu({required this.policy});
  final Policy policy;

  Future<void> _openDocument(BuildContext context, WidgetRef ref) async {
    try {
      final url = await ref.read(policyRepositoryProvider).documentUrl(policy.documentId!);
      await launchUrl(url, mode: LaunchMode.inAppBrowserView);
    } on ApiException catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _delete(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Delete this policy?'),
        content: const Text('The policy, its document and your questions about it will be permanently deleted.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(c, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(policyRepositoryProvider).delete(policy.id);
      invalidatePolicies(ref);
      if (context.mounted) context.go('/portfolio');
    } on ApiException catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) => PopupMenuButton<String>(
    onSelected: (v) => switch (v) {
      'edit' => context.push('/policy/${policy.id}/edit'),
      'doc' => _openDocument(context, ref),
      'delete' => _delete(context, ref),
      _ => null,
    },
    itemBuilder: (_) => [
      const PopupMenuItem(value: 'edit', child: Text('Edit details')),
      if (policy.documentId != null) const PopupMenuItem(value: 'doc', child: Text('View document')),
      const PopupMenuItem(value: 'delete', child: Text('Delete policy')),
    ],
  );
}

class _HealthCard extends ConsumerWidget {
  const _HealthCard({required this.policyId});
  final String policyId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final health = ref.watch(healthProvider(policyId)).value;
    if (health == null || !health.available) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.md),
      child: Card(
        child: ListTile(
          contentPadding: const EdgeInsets.all(AppSpacing.md),
          leading: ScoreRing(score: health.score!, size: 52),
          title: const Text('Policy health', style: TextStyle(fontWeight: FontWeight.w600)),
          subtitle: Text(
            health.attention.isEmpty && health.notCovered.isEmpty
                ? 'No issues found in the details we read'
                : '${health.attention.length + health.notCovered.length} things to know about',
          ),
          trailing: const Icon(Icons.chevron_right_rounded),
          onTap: () => context.push('/policy/$policyId/health'),
        ),
      ),
    );
  }
}

class _RenewalSheet extends ConsumerWidget {
  const _RenewalSheet({required this.policyId});
  final String policyId;

  Future<void> _set(BuildContext context, WidgetRef ref, String status) async {
    try {
      await ref.read(policyRepositoryProvider).setRenewal(policyId, status);
      invalidatePolicies(ref, policyId);
      if (!context.mounted) return;
      Navigator.pop(context);
      if (status == 'renewed') {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Marked as renewed. Add your new policy document to keep things up to date.'),
            action: SnackBarAction(label: 'Add', onPressed: () => context.push('/add')),
          ),
        );
      }
    } on ApiException catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final p = ref.watch(policyProvider(policyId)).value;
    final remindersOn = ref.watch(authControllerProvider).user?.notifyRenewals ?? true;
    if (p == null) return const SizedBox(height: 200, child: LoadingView());
    final days = p.daysToExpiry;
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Renewal', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpacing.md),
            Text(
              days == null
                  ? 'Add the policy end date to track renewal.'
                  : days < 0
                  ? 'This policy expired on ${formatDate(p.endDate)}.'
                  : 'Renews on ${formatDate(p.endDate)} — $days days left.',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: AppSpacing.xs),
            Text('Last premium: ${formatInr(p.premium)}'),
            const SizedBox(height: AppSpacing.md),
            if (p.renewalStatus == 'pending')
              Row(
                children: [
                  Icon(
                    remindersOn ? Icons.notifications_active_rounded : Icons.notifications_off_outlined,
                    size: 18,
                    color: AppColors.textSecondary,
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Text(
                      remindersOn
                          ? 'We\'ll remind you 90, 60, 30, 15, 7 and 1 day before expiry.'
                          : 'Renewal reminders are turned off in settings.',
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                  ),
                ],
              )
            else
              Text(
                p.renewalStatus == 'renewed' ? '✓ Marked as renewed' : 'Marked as not renewing',
                style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.w600),
              ),
            const SizedBox(height: AppSpacing.lg),
            if (p.renewalStatus == 'pending') ...[
              FilledButton(
                onPressed: () => _set(context, ref, 'renewed'),
                child: const Text('I\'ve renewed this policy'),
              ),
              const SizedBox(height: AppSpacing.sm),
              OutlinedButton(
                onPressed: () => _set(context, ref, 'not_renewing'),
                child: const Text('I\'m not renewing'),
              ),
            ] else
              OutlinedButton(onPressed: () => _set(context, ref, 'pending'), child: const Text('Undo')),
          ],
        ),
      ),
    );
  }
}
