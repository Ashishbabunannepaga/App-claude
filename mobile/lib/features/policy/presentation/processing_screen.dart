import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/network/api_exception.dart';
import '../data/models.dart';
import '../data/policy_repository.dart';

/// Polls document status until extraction finishes or fails.
class ProcessingScreen extends ConsumerStatefulWidget {
  const ProcessingScreen({super.key, required this.documentId});
  final String documentId;

  @override
  ConsumerState<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends ConsumerState<ProcessingScreen> {
  static const _interval = Duration(seconds: 2);
  static const _timeout = Duration(minutes: 3);

  Timer? _timer;
  PolicyDocument? _doc;
  String? _error;
  late DateTime _startedAt;

  @override
  void initState() {
    super.initState();
    _start();
  }

  void _start() {
    _startedAt = DateTime.now();
    _timer?.cancel();
    _timer = Timer.periodic(_interval, (_) => _poll());
    _poll();
  }

  Future<void> _poll() async {
    try {
      final doc = await ref.read(policyRepositoryProvider).document(widget.documentId);
      if (!mounted) return;
      setState(() {
        _doc = doc;
        _error = null;
      });
      if (doc.isDone) {
        _timer?.cancel();
        if (doc.status == 'extracted' && doc.policyId != null) {
          invalidatePolicies(ref);
          context.pushReplacement('/policy/${doc.policyId}/verify');
        }
      } else if (DateTime.now().difference(_startedAt) > _timeout) {
        _timer?.cancel();
        setState(() => _error = 'This is taking longer than usual. We\'ll keep working on it — check back shortly.');
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _retry() async {
    try {
      await ref.read(policyRepositoryProvider).retry(widget.documentId);
      setState(() => _doc = null);
      _start();
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final failed = _doc?.status == 'failed';
    return Scaffold(
      appBar: AppBar(title: const Text('Reading your policy')),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (failed) ...[
              const Icon(Icons.error_outline_rounded, size: 56, color: AppColors.error),
              const SizedBox(height: AppSpacing.md),
              Text(_doc!.errorText, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: AppSpacing.lg),
              FilledButton(onPressed: _retry, child: const Text('Try again')),
              const SizedBox(height: AppSpacing.sm),
              OutlinedButton(
                onPressed: () => context.pushReplacement('/add/manual'),
                child: const Text('Enter details manually'),
              ),
            ] else ...[
              const Center(child: CircularProgressIndicator()),
              const SizedBox(height: AppSpacing.lg),
              Text(
                _doc?.status == 'processing' ? 'Extracting policy details…' : 'Preparing your document…',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: AppSpacing.sm),
              const Text(
                'This usually takes under a minute.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.textSecondary),
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.md),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
