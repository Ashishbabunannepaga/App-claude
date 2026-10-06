import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme/app_colors.dart';
import '../../core/network/api_exception.dart';
import '../account/data/account_repository.dart';
import '../coverage/coverage_widgets.dart';
import '../../core/widgets/policy_card.dart';
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

class HomeHero extends ConsumerStatefulWidget {
  const HomeHero({super.key, required this.name, required this.hasPolicies});
  final String name;
  final bool hasPolicies;

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
    if (!MediaQuery.of(context).disableAnimations) {
      _timer = Timer.periodic(const Duration(milliseconds: 2600), (_) {
        if (mounted) setState(() => _i = (_i + 1) % heroScenarios.length);
      });
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _openOwnReport() async {
    final policies = (ref.read(policiesProvider).value ?? const <Policy>[])
        .where((p) => p.verified && p.policyType != 'other')
        .toList();
    if (policies.length == 1) {
      context.push('/policy/${policies.first.id}/report');
      return;
    }
    if (policies.isEmpty) {
      context.go('/portfolio');
      return;
    }
    final id = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (_) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.sm),
              child: Text('Which policy?', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            ),
            for (final p in policies)
              ListTile(
                leading: Icon(policyIcon(p.policyType), color: AppColors.forPolicyType(p.policyType)),
                title: Text(p.displayName),
                subtitle: Text(p.planName ?? p.policyType),
                onTap: () => Navigator.pop(context, p.id),
              ),
          ],
        ),
      ),
    );
    if (id != null && mounted) context.push('/policy/$id/report');
  }

  @override
  Widget build(BuildContext context) {
    final name = widget.name.isEmpty ? 'there' : widget.name;
    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFE6EEFF), Color(0xFFF7F9FD)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppColors.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, AppSpacing.md),
            child: Column(
              children: [
                Text(
                  'Hi $name, will your policy cover',
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, height: 1.2),
                ),
                const SizedBox(height: 6),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 350),
                  transitionBuilder: (child, a) => FadeTransition(
                    opacity: a,
                    child: SlideTransition(
                      position: Tween(begin: const Offset(0, 0.3), end: Offset.zero).animate(a),
                      child: child,
                    ),
                  ),
                  child: Container(
                    key: ValueKey(_i),
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
                    decoration: BoxDecoration(color: const Color(0xFFBDF0D3), borderRadius: BorderRadius.circular(6)),
                    child: Text(
                      heroScenarios[_i],
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: Color(0xFF0B5A36)),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                if (widget.hasPolicies) ...[
                  FilledButton.icon(
                    onPressed: _openOwnReport,
                    icon: const Icon(Icons.fact_check_rounded),
                    label: const Text('See your coverage report'),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  TextButton.icon(
                    onPressed: () => context.push('/add'),
                    icon: const Icon(Icons.add_rounded),
                    label: const Text('Add another policy'),
                  ),
                ] else ...[
                  FilledButton(
                    style: FilledButton.styleFrom(backgroundColor: AppColors.secondary),
                    onPressed: () => context.push('/add'),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('Add policy'),
                        SizedBox(width: AppSpacing.sm),
                        CoinChip('+50', dark: true),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      backgroundColor: AppColors.textPrimary,
                      foregroundColor: Colors.white,
                      side: BorderSide.none,
                    ),
                    onPressed: () => context.push('/report/sample'),
                    child: const Text('SEE A SAMPLE REPORT', style: TextStyle(letterSpacing: 0.8)),
                  ),
                ],
              ],
            ),
          ),
          InkWell(
            onTap: () => context.push('/report/sample'),
            child: const _Ticker(text: 'SAMPLE REPORT  •  WHAT YOUR POLICY REALLY COVERS  •  '),
          ),
        ],
      ),
    );
  }
}

/// A slow, endless ticker strip. Static when the system asks for reduced motion.
class _Ticker extends StatefulWidget {
  const _Ticker({required this.text});
  final String text;

  @override
  State<_Ticker> createState() => _TickerState();
}

class _TickerState extends State<_Ticker> with SingleTickerProviderStateMixin {
  late final _controller = AnimationController(vsync: this, duration: const Duration(seconds: 14));

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    MediaQuery.of(context).disableAnimations ? _controller.stop() : _controller.repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const style = TextStyle(color: AppColors.errorText, fontWeight: FontWeight.w800, letterSpacing: 3, fontSize: 13);
    final painter = TextPainter(
      text: TextSpan(text: widget.text, style: style),
      textDirection: TextDirection.ltr,
    )..layout();
    final w = painter.width;
    return Semantics(
      button: true,
      label: 'See a sample report',
      excludeSemantics: true,
      child: Container(
        height: 36,
        color: const Color(0xFFFFEFEF),
        child: ClipRect(
          child: AnimatedBuilder(
            animation: _controller,
            builder: (_, _) => OverflowBox(
              maxWidth: double.infinity,
              alignment: Alignment.centerLeft,
              child: Transform.translate(
                offset: Offset(-w * _controller.value, 0),
                child: Row(children: [for (var i = 0; i < 4; i++) Text(widget.text, style: style)]),
              ),
            ),
          ),
        ),
      ),
    );
  }
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
  Widget build(BuildContext context, WidgetRef ref) => Card(
    color: const Color(0xFFF1F0FF),
    child: InkWell(
      borderRadius: BorderRadius.circular(AppSpacing.radius),
      onTap: () => _request(context, ref),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Row(
          children: [
            const CircleAvatar(
              radius: 26,
              backgroundColor: Colors.white,
              child: Icon(Icons.support_agent_rounded, color: AppColors.life, size: 28),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('30-minute policy review', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                  const SizedBox(height: 2),
                  Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(color: AppColors.accent, borderRadius: BorderRadius.circular(6)),
                    child: const Text(
                      'ONE-ON-ONE',
                      style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w800),
                    ),
                  ),
                  const Text(
                    'Talk to an expert about your cover and clear next steps. No selling.',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded),
          ],
        ),
      ),
    ),
  );
}
