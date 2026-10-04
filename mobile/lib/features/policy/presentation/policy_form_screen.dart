import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/async_states.dart';
import '../data/models.dart';
import '../data/policy_repository.dart';

enum PolicyFormMode { verify, manual, edit }

/// One form for: verifying AI-extracted details, manual entry, and editing.
class PolicyFormScreen extends ConsumerWidget {
  const PolicyFormScreen({super.key, required this.mode, this.policyId});
  final PolicyFormMode mode;
  final String? policyId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (policyId == null) return _PolicyForm(mode: mode);
    final policy = ref.watch(policyProvider(policyId!));
    return AsyncValueView(
      value: policy,
      onRetry: () => ref.invalidate(policyProvider(policyId!)),
      data: (p) => _PolicyForm(mode: mode, policy: p),
    );
  }
}

class _PolicyForm extends ConsumerStatefulWidget {
  const _PolicyForm({required this.mode, this.policy});
  final PolicyFormMode mode;
  final Policy? policy;

  @override
  ConsumerState<_PolicyForm> createState() => _PolicyFormState();
}

class _PolicyFormState extends ConsumerState<_PolicyForm> {
  static const _lowConfidence = 0.7;
  final _formKey = GlobalKey<FormState>();
  late String _type = widget.policy?.policyType ?? 'health';
  late String? _frequency = widget.policy?.paymentFrequency;
  late DateTime? _start = widget.policy?.startDate;
  late DateTime? _end = widget.policy?.endDate;
  late final _insurer = TextEditingController(text: widget.policy?.insurer);
  late final _plan = TextEditingController(text: widget.policy?.planName);
  late final _number = TextEditingController(text: widget.policy?.policyNumber);
  late final _premium = TextEditingController(text: _amount(widget.policy?.premium));
  late final _cover = TextEditingController(text: _amount(widget.policy?.sumInsured));
  bool _saving = false;
  String? _error;

  static String? _amount(double? v) => v?.toStringAsFixed(v.truncateToDouble() == v ? 0 : 2);

  @override
  void dispose() {
    for (final c in [_insurer, _plan, _number, _premium, _cover]) {
      c.dispose();
    }
    super.dispose();
  }

  /// Highlight fields the AI was unsure about (only when verifying an extraction).
  String? _hint(String field, bool hasValue) {
    if (widget.mode != PolicyFormMode.verify) return null;
    if (!hasValue) return 'Not found in document — please fill in';
    final c = widget.policy?.fieldConfidence[field] ?? 1;
    return c < _lowConfidence ? 'Please double-check this' : null;
  }

  InputDecoration _decoration(String label, String field, bool hasValue) {
    final hint = _hint(field, hasValue);
    return InputDecoration(
      labelText: label,
      helperText: hint,
      helperStyle: const TextStyle(color: AppColors.warning),
      enabledBorder: hint == null
          ? null
          : OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AppColors.warning, width: 1.5),
            ),
    );
  }

  Map<String, dynamic> _fields() {
    String? text(TextEditingController c) => c.text.trim().isEmpty ? null : c.text.trim();
    String? day(DateTime? d) => d?.toIso8601String().substring(0, 10);
    return {
      'policy_type': _type,
      'insurer': text(_insurer),
      'plan_name': text(_plan),
      'policy_number': text(_number),
      'start_date': day(_start),
      'end_date': day(_end),
      'premium': text(_premium),
      'sum_insured': text(_cover),
      'payment_frequency': _frequency,
    };
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    if (_start != null && _end != null && !_start!.isBefore(_end!)) {
      setState(() => _error = 'Start date must be before end date.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    final repo = ref.read(policyRepositoryProvider);
    try {
      final saved = switch (widget.mode) {
        PolicyFormMode.verify => await repo.confirm(widget.policy!.id, _fields()),
        PolicyFormMode.edit => await repo.update(widget.policy!.id, _fields()),
        PolicyFormMode.manual => await repo.createManual(_fields()),
      };
      invalidatePolicies(ref, saved.id);
      if (!mounted) return;
      if (widget.mode == PolicyFormMode.edit) {
        context.pop();
      } else {
        context.go('/policy/${saved.id}');
      }
    } on ApiException catch (e) {
      setState(() => _error = e.fields.isNotEmpty ? e.fields.values.first : e.message);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _pickDate(bool isStart) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: (isStart ? _start : _end) ?? now,
      firstDate: DateTime(now.year - 40),
      lastDate: DateTime(now.year + 60),
    );
    if (picked != null) setState(() => isStart ? _start = picked : _end = picked);
  }

  @override
  Widget build(BuildContext context) {
    final title = switch (widget.mode) {
      PolicyFormMode.verify => 'Check your policy details',
      PolicyFormMode.manual => 'Enter policy details',
      PolicyFormMode.edit => 'Edit policy details',
    };
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.md),
          children: [
            if (widget.mode == PolicyFormMode.verify)
              Card(
                color: const Color(0xFFFFF7E6),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Text(
                    'We read these details from your document. Please check them carefully — '
                    'fields marked in amber need your attention.',
                    style: TextStyle(color: Colors.brown.shade700),
                  ),
                ),
              ),
            const SizedBox(height: AppSpacing.md),
            DropdownButtonFormField<String>(
              initialValue: _type,
              decoration: const InputDecoration(labelText: 'Insurance type'),
              items: const [
                'health',
                'life',
                'motor',
                'other',
              ].map((t) => DropdownMenuItem(value: t, child: Text(policyTypeLabel(t)))).toList(),
              onChanged: (v) => setState(() => _type = v ?? _type),
            ),
            const SizedBox(height: AppSpacing.md),
            TextFormField(
              controller: _insurer,
              textCapitalization: TextCapitalization.words,
              decoration: _decoration('Insurer', 'insurer', _insurer.text.isNotEmpty),
              validator: (v) => (v ?? '').trim().isEmpty ? 'Insurer is required' : null,
            ),
            const SizedBox(height: AppSpacing.md),
            TextFormField(controller: _plan, decoration: _decoration('Plan name', 'plan_name', true)),
            const SizedBox(height: AppSpacing.md),
            TextFormField(
              controller: _number,
              decoration: _decoration('Policy number', 'policy_number', _number.text.isNotEmpty),
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                Expanded(
                  child: _DateField('Start date', _start, () => _pickDate(true), _hint('start_date', _start != null)),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(child: _DateField('End date', _end, () => _pickDate(false), _hint('end_date', _end != null))),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            TextFormField(
              controller: _cover,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))],
              decoration: _decoration(
                _type == 'motor'
                    ? 'IDV (₹)'
                    : _type == 'life'
                    ? 'Sum assured (₹)'
                    : 'Sum insured (₹)',
                'sum_insured',
                _cover.text.isNotEmpty,
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            TextFormField(
              controller: _premium,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))],
              decoration: _decoration('Premium (₹)', 'premium', _premium.text.isNotEmpty),
            ),
            const SizedBox(height: AppSpacing.md),
            DropdownButtonFormField<String?>(
              initialValue: _frequency,
              decoration: const InputDecoration(labelText: 'Premium frequency'),
              items: const [
                null,
                'annual',
                'half_yearly',
                'quarterly',
                'monthly',
                'single',
              ].map((f) => DropdownMenuItem(value: f, child: Text(f == null ? 'Not sure' : humanise(f)))).toList(),
              onChanged: (v) => setState(() => _frequency = v),
            ),
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.md),
              Text(_error!, style: const TextStyle(color: AppColors.error)),
            ],
            const SizedBox(height: AppSpacing.lg),
            FilledButton(
              onPressed: _saving ? null : _save,
              child: Text(widget.mode == PolicyFormMode.verify ? 'Confirm & add policy' : 'Save'),
            ),
            const SizedBox(height: AppSpacing.lg),
          ],
        ),
      ),
    );
  }
}

class _DateField extends StatelessWidget {
  const _DateField(this.label, this.value, this.onTap, this.hint);
  final String label;
  final DateTime? value;
  final VoidCallback onTap;
  final String? hint;

  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    borderRadius: BorderRadius.circular(12),
    child: InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        helperText: hint,
        helperMaxLines: 2,
        helperStyle: const TextStyle(color: AppColors.warning),
        suffixIcon: const Icon(Icons.calendar_today_rounded, size: 18),
      ),
      child: Text(value == null ? 'Select' : formatDate(value)),
    ),
  );
}
