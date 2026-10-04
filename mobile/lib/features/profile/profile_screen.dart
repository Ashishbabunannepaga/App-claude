import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../app/theme/app_colors.dart';
import '../../core/config/env.dart';
import '../../core/network/api_exception.dart';
import '../../core/widgets/policy_card.dart';
import '../auth/data/auth_controller.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
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
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    Widget tile(IconData icon, String title, {VoidCallback? onTap, String? subtitle, Color? color}) => ListTile(
      leading: Icon(icon, color: color ?? AppColors.textSecondary),
      title: Text(title, style: TextStyle(color: color)),
      subtitle: subtitle == null ? null : Text(subtitle),
      trailing: onTap == null ? null : const Icon(Icons.chevron_right_rounded),
      onTap: onTap,
      enabled: onTap != null,
    );

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          Card(
            child: ListTile(
              contentPadding: const EdgeInsets.all(AppSpacing.md),
              leading: CircleAvatar(
                radius: 28,
                child: Text(
                  (user?.fullName ?? '?').characters.first.toUpperCase(),
                  style: const TextStyle(fontSize: 22),
                ),
              ),
              title: Text(user?.fullName ?? '', style: Theme.of(context).textTheme.titleMedium),
              subtitle: Text(user?.phone ?? user?.email ?? ''),
            ),
          ),
          const SectionHeader('Account'),
          Card(
            child: Column(
              children: [
                tile(Icons.family_restroom_rounded, 'Family members', subtitle: 'Coming soon'),
                tile(Icons.notifications_none_rounded, 'Notifications', subtitle: 'Coming soon'),
                tile(Icons.lock_outline_rounded, 'App lock', subtitle: 'Coming soon'),
              ],
            ),
          ),
          const SectionHeader('Help & legal'),
          Card(
            child: Column(
              children: [
                tile(
                  Icons.help_outline_rounded,
                  'Support',
                  onTap: () => launchUrl(Uri(scheme: 'mailto', path: Env.supportEmail)),
                ),
                tile(
                  Icons.privacy_tip_outlined,
                  'Privacy policy',
                  onTap: () => launchUrl(Uri.parse(Env.privacyPolicyUrl)),
                ),
                tile(Icons.description_outlined, 'Terms & conditions', onTap: () => launchUrl(Uri.parse(Env.termsUrl))),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Card(
            child: Column(
              children: [
                tile(Icons.logout_rounded, 'Log out', onTap: () => ref.read(authControllerProvider.notifier).logout()),
                tile(
                  Icons.delete_forever_outlined,
                  'Delete account',
                  color: AppColors.error,
                  onTap: () => _confirmDelete(context, ref),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
