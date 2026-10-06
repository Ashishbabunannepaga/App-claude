import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../app/theme/app_colors.dart';
import '../../core/ui/pressable.dart';
import '../../core/utils/formatters.dart';
import '../../core/widgets/async_states.dart';
import '../../core/widgets/policy_card.dart';
import '../policy/data/models.dart';
import '../policy/data/policy_repository.dart';

/// Everything needed in the first minutes of an emergency: national emergency numbers and the policy numbers to
/// quote, one tap away. Insurer helplines are printed on the policy document, so we point there rather than
/// guessing numbers.
class EmergencyScreen extends ConsumerWidget {
  const EmergencyScreen({super.key});

  Future<void> _call(BuildContext context, String number) async {
    final ok = await launchUrl(Uri(scheme: 'tel', path: number));
    if (!ok && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not open the dialler for $number')));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final policies = ref.watch(policiesProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Emergency card')),
      body: AsyncValueView(
        value: policies,
        onRetry: () => invalidatePolicies(ref),
        data: (all) {
          final live = all.where((p) => p.verified && p.status != 'expired').toList();
          return ListView(
            padding: const EdgeInsets.fromLTRB(AppSpacing.md, 0, AppSpacing.md, AppSpacing.xl),
            children: [
              Container(
                padding: const EdgeInsets.all(AppSpacing.lg),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF8E1B1F), AppColors.errorText],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.emergency_rounded, color: Colors.white, size: 36),
                    const SizedBox(height: AppSpacing.sm),
                    const Text(
                      'In an emergency, call first.',
                      style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Insurance questions can wait. Get help, then use the details below.',
                      style: TextStyle(color: Color(0xE6FFFFFF)),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    Row(
                      children: [
                        Expanded(
                          child: _CallButton(label: 'Emergency', number: '112', onTap: () => _call(context, '112')),
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        Expanded(
                          child: _CallButton(label: 'Ambulance', number: '108', onTap: () => _call(context, '108')),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SectionHeader('Your policy numbers'),
              if (live.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
                  child: Text(
                    'Add a policy and its number will show here, ready to quote at the hospital or to your insurer.',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                ),
              for (final p in live)
                Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                  child: _PolicyNumber(policy: p),
                ),
              const SectionHeader('Good to know'),
              const _Tip(
                icon: Icons.local_hospital_rounded,
                text: 'For planned cashless treatment, tell the hospital desk your insurer and policy number first.',
              ),
              const _Tip(
                icon: Icons.phone_in_talk_rounded,
                text: 'Your insurer\'s claims helpline is printed on your policy document and e-card. Keep it handy.',
              ),
              const _Tip(
                icon: Icons.timer_outlined,
                text: 'Many policies want an intimation within 24 hours of an emergency admission. Check the time limit in your wording.',
              ),
            ],
          );
        },
      ),
    );
  }
}

class _CallButton extends StatelessWidget {
  const _CallButton({required this.label, required this.number, required this.onTap});
  final String label;
  final String number;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Pressable(
    onTap: onTap,
    semanticLabel: 'Call $label $number',
    child: Container(
      padding: const EdgeInsets.symmetric(vertical: 14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(AppSpacing.radiusSm)),
      child: Column(
        children: [
          Text(
            number,
            style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: AppColors.errorText),
          ),
          Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textPrimary),
          ),
        ],
      ),
    ),
  );
}

class _PolicyNumber extends StatelessWidget {
  const _PolicyNumber({required this.policy});
  final Policy policy;

  @override
  Widget build(BuildContext context) {
    final number = policy.policyNumber;
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radius),
        border: Border.all(color: AppColors.border),
        boxShadow: AppShadows.card,
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: AppColors.tintForPolicyType(policy.policyType),
            child: Icon(policyIcon(policy.policyType), color: AppColors.forPolicyType(policy.policyType)),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(policy.displayName, style: const TextStyle(fontWeight: FontWeight.w800)),
                Text(
                  number ?? 'Policy number not added yet',
                  style: TextStyle(
                    fontSize: 15,
                    letterSpacing: number == null ? 0 : 0.5,
                    color: number == null ? AppColors.textSecondary : AppColors.textPrimary,
                  ),
                ),
                Text(
                  '${policyTypeLabel(policy.policyType)} · valid till ${formatDate(policy.endDate)}',
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                ),
              ],
            ),
          ),
          if (number != null)
            IconButton(
              tooltip: 'Copy policy number',
              icon: const Icon(Icons.copy_rounded),
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: number));
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Policy number copied')));
                }
              },
            ),
        ],
      ),
    );
  }
}

class _Tip extends StatelessWidget {
  const _Tip({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: AppSpacing.sm),
    child: Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(color: AppColors.surfaceTint, borderRadius: BorderRadius.circular(AppSpacing.radius)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppColors.primary),
          const SizedBox(width: AppSpacing.md),
          Expanded(child: Text(text)),
        ],
      ),
    ),
  );
}
