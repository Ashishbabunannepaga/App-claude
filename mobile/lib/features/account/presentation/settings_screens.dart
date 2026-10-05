import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/config/env.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/security/app_lock.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/policy_card.dart';
import '../../auth/data/auth_controller.dart';
import '../../policy/data/policy_repository.dart';
import '../data/account_repository.dart';

void _snack(BuildContext context, String text) =>
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));

class EditProfileScreen extends ConsumerStatefulWidget {
  const EditProfileScreen({super.key});

  @override
  ConsumerState<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends ConsumerState<EditProfileScreen> {
  late final _user = ref.read(authControllerProvider).user!;
  late final _name = TextEditingController(text: _user.fullName);
  late final _city = TextEditingController(text: _user.city);
  late final _state = TextEditingController(text: _user.state);
  late DateTime? _dob = _user.dateOfBirth;
  bool _saving = false;

  @override
  void dispose() {
    for (final c in [_name, _city, _state]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ref.read(authControllerProvider.notifier).updateProfile({
        'full_name': _name.text.trim(),
        'city': _city.text.trim().isEmpty ? null : _city.text.trim(),
        'state': _state.text.trim().isEmpty ? null : _state.text.trim(),
        'date_of_birth': _dob?.toIso8601String().substring(0, 10),
      });
      if (mounted) Navigator.pop(context);
    } on ApiException catch (e) {
      if (mounted) _snack(context, e.message);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Personal details')),
    body: ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        TextField(
          controller: _name,
          textCapitalization: TextCapitalization.words,
          decoration: const InputDecoration(labelText: 'Full name'),
        ),
        const SizedBox(height: AppSpacing.md),
        InputDecorator(
          decoration: const InputDecoration(labelText: 'Mobile number', enabled: false),
          child: Text(_user.phone ?? _user.email ?? ''),
        ),
        const SizedBox(height: AppSpacing.md),
        OutlinedButton.icon(
          icon: const Icon(Icons.cake_outlined),
          label: Text(_dob == null ? 'Date of birth' : formatDate(_dob)),
          onPressed: () async {
            final picked = await showDatePicker(
              context: context,
              initialDate: _dob ?? DateTime(1990),
              firstDate: DateTime(1920),
              lastDate: DateTime.now(),
            );
            if (picked != null) setState(() => _dob = picked);
          },
        ),
        const SizedBox(height: AppSpacing.md),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _city,
                decoration: const InputDecoration(labelText: 'City'),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: TextField(
                controller: _state,
                decoration: const InputDecoration(labelText: 'State'),
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.lg),
        FilledButton(onPressed: _saving ? null : _save, child: const Text('Save')),
      ],
    ),
  );
}

class NotificationSettingsScreen extends ConsumerWidget {
  const NotificationSettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    Future<void> update(String field, bool value) async {
      try {
        await ref.read(authControllerProvider.notifier).updateProfile({field: value});
      } on ApiException catch (e) {
        if (context.mounted) _snack(context, e.message);
      }
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  value: user?.notifyRenewals ?? true,
                  onChanged: (v) => update('notify_renewals', v),
                  title: const Text('Renewal reminders'),
                  subtitle: const Text('90, 60, 30, 15, 7 and 1 day before a policy expires'),
                ),
                SwitchListTile(
                  value: user?.notifyProcessing ?? true,
                  onChanged: (v) => update('notify_processing', v),
                  title: const Text('Policy updates'),
                  subtitle: const Text('When a document has been read and is ready to review'),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          const Text(
            'We never send promotional notifications, and notifications never show your policy numbers, '
            'amounts or health details.',
            style: TextStyle(color: AppColors.textSecondary),
          ),
        ],
      ),
    );
  }
}

const _faqs = [
  (
    'Is my data safe?',
    'Your documents are stored encrypted and are only accessible to you. We do not sell your data or share it '
        'with insurers or agents.',
  ),
  (
    'How does the AI answer my questions?',
    'It reads only your own policy document and shows the page its answer came from. If the answer is not in your '
        'document it will say so instead of guessing.',
  ),
  (
    'The details extracted from my policy are wrong. What do I do?',
    'Open the policy, tap the ⋮ menu and choose "Edit details". Anything you correct is saved as confirmed by you.',
  ),
  (
    'Which documents can I upload?',
    'PDF policy documents work best. You can also upload a clear photo (JPG/PNG) up to 20 MB. Password-protected '
        'PDFs must be unlocked first.',
  ),
  (
    'Do you sell insurance?',
    'No. InsureIQ helps you organise and understand the policies you already have. We do not sell or recommend '
        'insurance products.',
  ),
  (
    'How do I delete my account?',
    'Profile → Privacy & data → Delete account. Your data is permanently deleted after 7 days.',
  ),
];

class SupportScreen extends ConsumerStatefulWidget {
  const SupportScreen({super.key});

  @override
  ConsumerState<SupportScreen> createState() => _SupportScreenState();
}

class _SupportScreenState extends ConsumerState<SupportScreen> {
  final _message = TextEditingController();
  String _category = 'question';
  bool _sending = false;

  @override
  void dispose() {
    _message.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    setState(() => _sending = true);
    try {
      await ref.read(accountRepositoryProvider).contactSupport(_category, _message.text.trim());
      _message.clear();
      if (mounted) _snack(context, 'Thanks — we\'ll get back to you within 2 working days.');
    } on ApiException catch (e) {
      if (mounted) _snack(context, e.message);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Help & support')),
    body: ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        const SectionHeader('Frequently asked questions'),
        Card(
          child: Column(
            children: [
              for (final (q, a) in _faqs)
                ExpansionTile(
                  shape: const Border(),
                  title: Text(q, style: const TextStyle(fontWeight: FontWeight.w600)),
                  childrenPadding: const EdgeInsets.fromLTRB(AppSpacing.md, 0, AppSpacing.md, AppSpacing.md),
                  expandedAlignment: Alignment.centerLeft,
                  children: [Text(a)],
                ),
            ],
          ),
        ),
        const SectionHeader('Contact us'),
        DropdownButtonFormField<String>(
          initialValue: _category,
          decoration: const InputDecoration(labelText: 'Topic'),
          items: const [
            DropdownMenuItem(value: 'question', child: Text('A question')),
            DropdownMenuItem(value: 'problem', child: Text('Something isn\'t working')),
            DropdownMenuItem(value: 'feedback', child: Text('Feedback')),
            DropdownMenuItem(value: 'privacy', child: Text('Privacy / my data')),
            DropdownMenuItem(value: 'grievance', child: Text('Complaint (grievance)')),
          ],
          onChanged: (v) => setState(() => _category = v ?? _category),
        ),
        const SizedBox(height: AppSpacing.md),
        TextField(
          controller: _message,
          minLines: 4,
          maxLines: 8,
          maxLength: 4000,
          onChanged: (_) => setState(() {}),
          decoration: const InputDecoration(hintText: 'How can we help?'),
        ),
        FilledButton(onPressed: _message.text.trim().length < 5 || _sending ? null : _send, child: const Text('Send')),
        const SizedBox(height: AppSpacing.md),
        TextButton.icon(
          onPressed: () => launchUrl(Uri(scheme: 'mailto', path: Env.supportEmail)),
          icon: const Icon(Icons.mail_outline_rounded),
          label: const Text('Email us instead'),
        ),
      ],
    ),
  );
}

class PrivacyScreen extends ConsumerWidget {
  const PrivacyScreen({super.key});

  Future<void> _export(BuildContext context, WidgetRef ref) async {
    try {
      final json = await ref.read(accountRepositoryProvider).exportData();
      await SharePlus.instance.share(
        ShareParams(
          files: [
            XFile.fromData(Uint8List.fromList(json.codeUnits), mimeType: 'application/json', name: 'my-data.json'),
          ],
          fileNameOverrides: const ['insureiq-my-data.json'],
          subject: 'My InsureIQ data',
        ),
      );
    } on ApiException catch (e) {
      if (context.mounted) _snack(context, e.message);
    }
  }

  Future<void> _delete(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Delete your account?'),
        content: const Text(
          'Your account will be disabled now. All your policies, documents and data will be permanently '
          'deleted after 7 days. Logging in again within 7 days cancels the deletion.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(c, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: const Text('Delete account'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(authControllerProvider.notifier).deleteAccount();
    } on ApiException catch (e) {
      if (context.mounted) _snack(context, e.message);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
    appBar: AppBar(title: const Text('Privacy & data')),
    body: ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        const Card(
          child: Padding(
            padding: EdgeInsets.all(AppSpacing.md),
            child: Text(
              'We use your policy documents only to show, explain and remind you about your own insurance. '
              'Documents are encrypted, never sold, and never shared with insurers or agents. '
              'AI processing uses providers contractually barred from training on your data.',
            ),
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        Card(
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.download_rounded),
                title: const Text('Download my data'),
                subtitle: const Text('A copy of your profile, policies and questions'),
                onTap: () => _export(context, ref),
              ),
              ListTile(
                leading: const Icon(Icons.privacy_tip_outlined),
                title: const Text('Privacy policy'),
                onTap: () => launchUrl(Uri.parse(Env.privacyPolicyUrl)),
              ),
              const ListTile(
                leading: Icon(Icons.gavel_rounded),
                title: Text('Grievance officer'),
                subtitle: Text(Env.grievanceOfficer),
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        Card(
          child: ListTile(
            leading: const Icon(Icons.delete_forever_outlined, color: AppColors.error),
            title: const Text('Delete account', style: TextStyle(color: AppColors.error)),
            subtitle: const Text('Permanently delete all your data'),
            onTap: () => _delete(context, ref),
          ),
        ),
      ],
    ),
  );
}

/// App lock toggle row for the profile screen (hidden where biometrics aren't available).
class AppLockTile extends ConsumerWidget {
  const AppLockTile({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (kIsWeb) return const SizedBox.shrink();
    final lock = ref.watch(appLockProvider);
    return SwitchListTile(
      secondary: const Icon(Icons.lock_outline_rounded, color: AppColors.textSecondary),
      title: const Text('App lock'),
      subtitle: const Text('Use fingerprint, face or device PIN to open the app'),
      value: lock.enabled,
      onChanged: (v) async {
        final ok = await ref.read(appLockProvider.notifier).setEnabled(v);
        if (!ok && context.mounted) _snack(context, 'Set up a screen lock on your phone first.');
      },
    );
  }
}

const answerLanguages = {
  'en': 'English',
  'hi': 'हिन्दी (Hindi)',
  'mr': 'मराठी (Marathi)',
  'ta': 'தமிழ் (Tamil)',
  'te': 'తెలుగు (Telugu)',
  'kn': 'ಕನ್ನಡ (Kannada)',
  'bn': 'বাংলা (Bengali)',
  'gu': 'ગુજરાતી (Gujarati)',
  'ml': 'മലയാളം (Malayalam)',
};

/// Language for AI summaries and answers. The app's own screens stay in English for now.
class LanguageTile extends ConsumerWidget {
  const LanguageTile({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final current = ref.watch(authControllerProvider).user?.preferredLanguage ?? 'en';
    return ListTile(
      leading: const Icon(Icons.translate_rounded, color: AppColors.textSecondary),
      title: const Text('AI answer language'),
      subtitle: Text(answerLanguages[current] ?? 'English'),
      trailing: const Icon(Icons.chevron_right_rounded),
      onTap: () async {
        final picked = await showModalBottomSheet<String>(
          context: context,
          showDragHandle: true,
          builder: (c) => SafeArea(
            child: ListView(
              shrinkWrap: true,
              children: [
                const Padding(
                  padding: EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.sm),
                  child: Text(
                    'Summaries and answers about your policies will be written in this language. '
                    'You can ask questions in it too.',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                ),
                for (final e in answerLanguages.entries)
                  ListTile(
                    title: Text(e.value),
                    trailing: e.key == current ? const Icon(Icons.check_rounded, color: AppColors.accent) : null,
                    onTap: () => Navigator.pop(c, e.key),
                  ),
              ],
            ),
          ),
        );
        if (picked == null || picked == current) return;
        try {
          await ref.read(authControllerProvider.notifier).updateProfile({'preferred_language': picked});
          ref.invalidate(summaryProvider);
        } on ApiException catch (e) {
          if (context.mounted) _snack(context, e.message);
        }
      },
    );
  }
}
