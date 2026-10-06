import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme/app_colors.dart';
import '../../core/network/api_exception.dart';
import '../../core/ui/art.dart';
import '../../core/ui/pressable.dart';
import '../../core/utils/formatters.dart';
import '../../core/widgets/policy_card.dart';
import '../account/data/account_repository.dart';
import '../coverage/coverage_widgets.dart';
import '../policy/data/models.dart';
import '../policy/data/policy_repository.dart';

/// Everyday situations the hero cycles through. Each one is answered by the coverage report.
const heroScenarios = [
  'a maternity bill?',
  'a knee surgery?',
  'a flooded car engine?',
  'a 10-day ICU stay?',
  'your family\'s future?',
];

/// Picks one of the user's policies (skipping the sheet when there is only one) and returns its id.
/// [types] limits the choice, e.g. {'life'} for nominees.
Future<String?> pickPolicy(
  BuildContext context,
  WidgetRef ref, {
  Set<String>? types,
  String title = 'Which policy?',
}) async {
  final all = (ref.read(policiesProvider).value ?? const <Policy>[])
      .where((p) => p.verified && p.policyType != 'other' && (types == null || types.contains(p.policyType)))
      .toList();
  if (all.isEmpty) return null;
  if (all.length == 1) return all.first.id;
  return showModalBottomSheet<String>(
    context: context,
    showDragHandle: true,
    builder: (_) => SafeArea(
      child: ListView(
        shrinkWrap: true,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.sm),
            child: Text(title, style: Theme.of(context).textTheme.titleLarge),
          ),
          for (final p in all)
            ListTile(
              leading: CircleAvatar(
                backgroundColor: AppColors.tintForPolicyType(p.policyType),
                child: Icon(policyIcon(p.policyType), color: AppColors.forPolicyType(p.policyType)),
              ),
              title: Text(p.displayName),
              subtitle: Text(p.planName ?? policyTypeLabel(p.policyType)),
              onTap: () => Navigator.pop(context, p.id),
            ),
        ],
      ),
    ),
  );
}

/// The dark hero panel at the top of Home: rotating question, illustration and the main action.
class HomeHero extends ConsumerStatefulWidget {
  const HomeHero({super.key, required this.hasPolicies, this.summary});
  final bool hasPolicies;
  final PortfolioSummary? summary;

  @override
  ConsumerState<HomeHero> createState() => _HomeHeroState();
}

class _HomeHeroState extends ConsumerState<HomeHero> {
  Timer? _timer;
  int _i = 0;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _timer?.cancel();
    if (!(MediaQuery.maybeOf(context)?.disableAnimations ?? false)) {
      _timer = Timer.periodic(const Duration(milliseconds: 2800), (_) {
        if (mounted) setState(() => _i = (_i + 1) % heroScenarios.length);
      });
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _openReport() async {
    final id = await pickPolicy(context, ref);
    if (!mounted) return;
    id == null ? context.go('/portfolio') : context.push('/policy/$id/report');
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.summary;
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.ink, Color(0xFF0E4F52)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
        boxShadow: AppShadows.lift,
      ),
      child: Stack(
        children: [
          Positioned(right: -22, top: -18, child: SceneArt(Scene.shield, size: 180, backdrop: false)),
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 190,
                  child: Text(
                    'Will your policy cover',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                      height: 1.15,
                      letterSpacing: -0.4,
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 350),
                  transitionBuilder: (child, a) => FadeTransition(
                    opacity: a,
                    child: SlideTransition(
                      position: Tween(begin: const Offset(0, 0.4), end: Offset.zero).animate(a),
                      child: child,
                    ),
                  ),
                  child: Container(
                    key: ValueKey(_i),
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                    decoration: BoxDecoration(color: AppColors.gold, borderRadius: BorderRadius.circular(8)),
                    child: Text(
                      heroScenarios[_i],
                      style: const TextStyle(color: AppColors.ink, fontSize: 20, fontWeight: FontWeight.w800),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                if (widget.hasPolicies && s != null) ...[
                  Row(
                    children: [
                      _Stat('Health', formatInrCompact(s.healthCover)),
                      _Stat('Life', formatInrCompact(s.lifeCover)),
                      _Stat('Per year', formatInrCompact(s.totalAnnualPremium)),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.md),
                  FilledButton.icon(
                    style: FilledButton.styleFrom(backgroundColor: AppColors.gold, foregroundColor: AppColors.ink),
                    onPressed: _openReport,
                    icon: const Icon(Icons.fact_check_rounded),
                    label: const Text('See your coverage report'),
                  ),
                ] else ...[
                  FilledButton(
                    style: FilledButton.styleFrom(backgroundColor: AppColors.gold, foregroundColor: AppColors.ink),
                    onPressed: () => context.push('/add'),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Flexible(child: Text('Add a policy', overflow: TextOverflow.ellipsis)),
                        SizedBox(width: AppSpacing.sm),
                        CoinChip('+50'),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: const BorderSide(color: Color(0x66FFFFFF), width: 1.5),
                    ),
                    onPressed: () => context.push('/report/sample'),
                    child: const Text('See a sample report'),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
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
          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800),
        ),
        Text(label, style: const TextStyle(color: Color(0xCCFFFFFF), fontSize: 12)),
      ],
    ),
  );
}

/// "Ask about your cover" bar. Opens the assistant for one of the user's policies.
class AskBar extends ConsumerWidget {
  const AskBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => Pressable(
    semanticLabel: 'Ask about your cover',
    onTap: () async {
      final id = await pickPolicy(context, ref, title: 'Ask about which policy?');
      if (!context.mounted) return;
      if (id == null) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Add a policy first, then you can ask questions about it.')));
        return;
      }
      context.push('/policy/$id/ask');
    },
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radius),
        border: Border.all(color: AppColors.border),
        boxShadow: AppShadows.card,
      ),
      child: const Row(
        children: [
          Icon(Icons.auto_awesome_rounded, color: AppColors.primary),
          SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(
              'Ask anything about your cover',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ),
          Icon(Icons.mic_none_rounded, color: AppColors.textSecondary),
        ],
      ),
    ),
  );
}

/// One illustrated tile in the services grid.
class ServiceTile extends StatelessWidget {
  const ServiceTile({super.key, required this.icon, required this.label, required this.color, required this.onTap});
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Pressable(
    onTap: onTap,
    semanticLabel: label,
    child: Column(
      children: [
        Container(
          width: 64,
          height: 64,
          decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(22)),
          child: Stack(
            alignment: Alignment.center,
            children: [
              Positioned(
                right: 6,
                top: 6,
                child: Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(color: color.withValues(alpha: 0.2), shape: BoxShape.circle),
                ),
              ),
              Icon(icon, color: color, size: 30),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          textAlign: TextAlign.center,
          maxLines: 2,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, height: 1.15),
        ),
      ],
    ),
  );
}

/// Request a call with an insurance expert. Goes to the support queue (category expert_review).
class ExpertReviewCard extends ConsumerWidget {
  const ExpertReviewCard({super.key});

  Future<void> _request(BuildContext context, WidgetRef ref) async {
    final note = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Request a policy review'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'An insurance expert will call you on your registered number to walk through your policies. '
              'We won\'t try to sell you anything.',
            ),
            const SizedBox(height: AppSpacing.md),
            TextField(
              controller: note,
              maxLines: 3,
              decoration: const InputDecoration(hintText: 'What would you like help with? (optional)'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Request call')),
        ],
      ),
    );
    final text = note.text.trim();
    note.dispose();
    if (ok != true || !context.mounted) return;
    try {
      await ref
          .read(accountRepositoryProvider)
          .contactSupport('expert_review', text.length >= 5 ? text : 'Please review my policies.');
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Request sent. Our team will call you on your registered number.')),
        );
      }
    } on ApiException catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) => Pressable(
    onTap: () => _request(context, ref),
    child: Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: const Color(0xFFEDEAFB),
        borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
      ),
      child: Row(
        children: [
          const CircleAvatar(
            radius: 28,
            backgroundColor: Colors.white,
            child: Icon(Icons.support_agent_rounded, color: AppColors.life, size: 30),
          ),
          const SizedBox(width: AppSpacing.md),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Talk to an expert', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                SizedBox(height: 2),
                Text(
                  'A 30-minute walk through your cover and what to do next. No selling.',
                  style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
                ),
              ],
            ),
          ),
          const Icon(Icons.arrow_forward_rounded),
        ],
      ),
    ),
  );
}
