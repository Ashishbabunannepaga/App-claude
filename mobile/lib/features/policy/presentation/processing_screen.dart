import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/network/api_exception.dart';
import '../data/models.dart';
import '../data/policy_repository.dart';
import '../../../core/locale.dart';

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
  Timer? _deadline;
  PolicyDocument? _doc;
  String? _error;

  /// The server's answer to Try again ("still reading..."): stays while we keep watching.
  String? _notice;
  bool _timedOut = false;

  @override
  void initState() {
    super.initState();
    _start();
  }

  void _start() {
    _timedOut = false;
    _timer?.cancel();
    _deadline?.cancel();
    _timer = Timer.periodic(_interval, (_) => _poll());
    // Never a spinner forever: after the deadline, offer Try again or Home.
    _deadline = Timer(_timeout, () {
      _timer?.cancel();
      if (mounted && !(_doc?.isDone ?? false)) setState(() => _timedOut = true);
    });
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
        _deadline?.cancel();
        if (doc.status == 'extracted' && doc.policyId != null) {
          invalidatePolicies(ref);
          context.pushReplacement('/policy/${doc.policyId}/verify');
        }
      }
    } on ApiException catch (e) {
      // A dropped connection keeps polling: the message shows until the next read succeeds.
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _retry() async {
    try {
      await ref.read(policyRepositoryProvider).retry(widget.documentId);
      if (!mounted) return;
      setState(() {
        _doc = null;
        _error = null;
        _notice = null;
      });
      _start();
    } on ApiException catch (e) {
      // Still being read on the server: keep watching it rather than leaving the user stuck.
      if (!mounted) return;
      setState(() => _notice = e.message);
      _start();
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _deadline?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final doc = _doc;
    final failed = doc?.status == 'failed';
    final secondary = TextStyle(color: AppColors.textSecondary);
    return Scaffold(
      appBar: AppBar(title: Text(context.l10n.readingYourPolicy)),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (failed) ...[
              Icon(Icons.error_outline_rounded, size: 56, color: AppColors.error),
              const SizedBox(height: AppSpacing.md),
              Text(doc!.errorText, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: AppSpacing.lg),
              if (doc.canRetry)
                FilledButton(key: const Key('processing-retry'), onPressed: _retry, child: Text(context.l10n.tryAgain))
              else
                FilledButton(
                  key: const Key('processing-another-file'),
                  onPressed: () => context.pushReplacement('/add'),
                  child: Text(context.l10n.chooseAnotherFile),
                ),
              const SizedBox(height: AppSpacing.sm),
              OutlinedButton(
                onPressed: () => context.pushReplacement('/add/manual'),
                child: Text(context.l10n.enterManually),
              ),
            ] else if (_timedOut) ...[
              Icon(Icons.hourglass_bottom_rounded, size: 56, color: AppColors.textSecondary),
              const SizedBox(height: AppSpacing.md),
              Text(
                context.l10n.takingLonger,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: AppSpacing.lg),
              FilledButton(key: const Key('processing-retry'), onPressed: _retry, child: Text(context.l10n.tryAgain)),
              const SizedBox(height: AppSpacing.sm),
              OutlinedButton(onPressed: () => context.go('/'), child: Text(context.l10n.backToHome)),
            ] else ...[
              const Center(child: CircularProgressIndicator()),
              const SizedBox(height: AppSpacing.lg),
              Text(
                doc?.status == 'processing' ? context.l10n.readingDetails : context.l10n.preparingDocument,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: AppSpacing.sm),
              Text(context.l10n.underAMinute, textAlign: TextAlign.center, style: secondary),
            ],
            if (_notice != null && !failed) ...[
              const SizedBox(height: AppSpacing.md),
              Text(_notice!, key: const Key('processing-notice'), textAlign: TextAlign.center, style: secondary),
            ],
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.md),
              Text(_error!, key: const Key('processing-error'), textAlign: TextAlign.center, style: secondary),
            ],
          ],
        ),
      ),
    );
  }
}
