import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/widgets/async_states.dart';
import '../../policy/data/models.dart';
import '../data/account_repository.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  IconData _icon(String kind) => switch (kind) {
    'renewal' => Icons.event_repeat_rounded,
    'processing_done' => Icons.task_alt_rounded,
    'processing_failed' => Icons.error_outline_rounded,
    _ => Icons.notifications_none_rounded,
  };

  Future<void> _open(BuildContext context, WidgetRef ref, AppNotification n) async {
    if (!n.isRead) {
      await ref.read(accountRepositoryProvider).markRead(n.id);
      ref.invalidate(notificationsProvider);
      ref.invalidate(unreadCountProvider);
    }
    if (n.deepLink != null && context.mounted) context.push(n.deepLink!);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(notificationsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          TextButton(
            onPressed: () async {
              await ref.read(accountRepositoryProvider).markAllRead();
              ref.invalidate(notificationsProvider);
              ref.invalidate(unreadCountProvider);
            },
            child: const Text('Mark all read'),
          ),
        ],
      ),
      body: AsyncValueView(
        value: items,
        onRetry: () => ref.invalidate(notificationsProvider),
        data: (list) => list.isEmpty
            ? const EmptyView(
                icon: Icons.notifications_none_rounded,
                title: 'You\'re all caught up',
                message: 'Renewal reminders and policy updates will appear here.',
              )
            : RefreshIndicator(
                onRefresh: () async => ref.invalidate(notificationsProvider),
                child: ListView.separated(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  itemCount: list.length,
                  separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.sm),
                  itemBuilder: (_, i) {
                    final n = list[i];
                    return Card(
                      color: n.isRead ? AppColors.surface : const Color(0xFFF0F5FF),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.xs),
                        leading: Icon(
                          _icon(n.kind),
                          color: n.kind == 'processing_failed' ? AppColors.error : AppColors.secondary,
                        ),
                        title: Text(
                          n.title,
                          style: TextStyle(fontWeight: n.isRead ? FontWeight.w500 : FontWeight.w700),
                        ),
                        subtitle: Text('${n.body}\n${DateFormat('d MMM, h:mm a').format(n.createdAt)}'),
                        isThreeLine: true,
                        trailing: n.isRead ? null : const CircleAvatar(radius: 5, backgroundColor: AppColors.secondary),
                        onTap: () => _open(context, ref, n),
                      ),
                    );
                  },
                ),
              ),
      ),
    );
  }
}
