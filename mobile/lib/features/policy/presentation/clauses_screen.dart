import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/async_states.dart';
import '../data/models.dart';
import '../data/policy_repository.dart';

const clauseTypes = ['benefit', 'exclusion', 'waiting_period', 'limit', 'condition', 'definition'];

String clauseLabel(String type) => switch (type) {
  'benefit' => 'Benefit',
  'exclusion' => 'Exclusion',
  'waiting_period' => 'Waiting period',
  'limit' => 'Limit',
  'condition' => 'Condition',
  'definition' => 'Definition',
  _ => 'Clause',
};

Color clauseColor(String type) => switch (type) {
  'benefit' => AppColors.accent,
  'exclusion' => AppColors.error,
  'waiting_period' => AppColors.warning,
  'limit' => const Color(0xFFB45309),
  'condition' => AppColors.secondary,
  _ => AppColors.textSecondary,
};

class ClauseTypeBadge extends StatelessWidget {
  const ClauseTypeBadge(this.type, {super.key});
  final String type;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
    decoration: BoxDecoration(color: clauseColor(type).withValues(alpha: 0.12), borderRadius: BorderRadius.circular(6)),
    child: Text(
      clauseLabel(type),
      style: TextStyle(color: clauseColor(type), fontSize: 11, fontWeight: FontWeight.w700),
    ),
  );
}

/// The policy wording split into typed clauses — the exact text, with page numbers.
class ClausesScreen extends ConsumerStatefulWidget {
  const ClausesScreen({super.key, required this.policyId});
  final String policyId;

  @override
  ConsumerState<ClausesScreen> createState() => _ClausesScreenState();
}

class _ClausesScreenState extends ConsumerState<ClausesScreen> {
  String? _type;
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final clauses = ref.watch(clausesProvider(widget.policyId));
    return Scaffold(
      appBar: AppBar(title: const Text('Policy clauses')),
      body: AsyncValueView(
        value: clauses,
        onRetry: () => ref.invalidate(clausesProvider(widget.policyId)),
        data: (all) {
          if (all.isEmpty) {
            return const EmptyView(
              icon: Icons.article_outlined,
              title: 'No clauses yet',
              message: 'Clauses are read from your uploaded policy document. Manually added policies have none.',
            );
          }
          final q = _query.toLowerCase();
          final shown = all
              .where((c) => _type == null || c.tags.contains(_type) || c.type == _type)
              .where((c) => q.isEmpty || c.text.toLowerCase().contains(q) || c.title.toLowerCase().contains(q))
              .toList();
          return ListView(
            padding: const EdgeInsets.all(AppSpacing.md),
            children: [
              TextField(
                onChanged: (v) => setState(() => _query = v),
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search_rounded),
                  hintText: 'Search the policy wording',
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    for (final t in [null, ...clauseTypes])
                      Padding(
                        padding: const EdgeInsets.only(right: AppSpacing.sm),
                        child: ChoiceChip(
                          label: Text(
                            t == null
                                ? 'All (${all.length})'
                                : '${clauseLabel(t)} (${all.where((c) => c.tags.contains(t) || c.type == t).length})',
                          ),
                          selected: _type == t,
                          onSelected: (_) => setState(() => _type = t),
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              if (shown.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(AppSpacing.lg),
                  child: Text('Nothing matches.', textAlign: TextAlign.center),
                ),
              for (final c in shown) _ClauseCard(c),
            ],
          );
        },
      ),
    );
  }
}

class _ClauseCard extends StatelessWidget {
  const _ClauseCard(this.clause);
  final Clause clause;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: AppSpacing.sm),
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                ClauseTypeBadge(clause.type),
                const Spacer(),
                Text(
                  [
                    if (clause.page != null) 'Page ${clause.page}',
                    if (clause.section != null) clause.section,
                  ].join(' · '),
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 11),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            // Titles derived from the first words would just repeat the text; show only real labels.
            if (!clause.title.endsWith('…') && clause.title != clause.text) ...[
              Text(clause.title, style: const TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 2),
            ],
            Text(clause.text, style: const TextStyle(height: 1.35)),
          ],
        ),
      ),
    ),
  );
}
