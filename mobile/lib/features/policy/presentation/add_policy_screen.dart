import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/network/api_exception.dart';
import '../data/policy_repository.dart';

const _maxBytes = 20 * 1024 * 1024;

class AddPolicyScreen extends ConsumerStatefulWidget {
  const AddPolicyScreen({super.key});

  @override
  ConsumerState<AddPolicyScreen> createState() => _AddPolicyScreenState();
}

class _AddPolicyScreenState extends ConsumerState<AddPolicyScreen> {
  double? _progress;
  String? _error;

  Future<void> _pick({required bool images}) async {
    setState(() => _error = null);
    final file = await FilePicker.pickFile(
      type: images ? FileType.image : FileType.custom,
      allowedExtensions: images ? null : ['pdf'],
    );
    if (file == null) return;
    final size = await file.length();
    if (size != null && size > _maxBytes) {
      setState(() => _error = 'File must be under 20 MB.');
      return;
    }
    final ext = file.extension?.toLowerCase();
    if (!['pdf', 'jpg', 'jpeg', 'png'].contains(ext)) {
      setState(() => _error = 'Please choose a PDF, JPG or PNG file.');
      return;
    }
    await _upload(await file.readAsBytes(), file.name);
  }

  Future<void> _capture() async {
    setState(() => _error = null);
    final photo = await ImagePicker().pickImage(source: ImageSource.camera, imageQuality: 85, maxWidth: 2400);
    if (photo == null) return;
    await _upload(await photo.readAsBytes(), photo.name);
  }

  Future<void> _upload(Uint8List bytes, String name) async {
    setState(() => _progress = 0);
    try {
      final doc = await ref
          .read(policyRepositoryProvider)
          .upload(bytes, name, onProgress: (p) => mounted ? setState(() => _progress = p) : null);
      if (!mounted) return;
      context.pushReplacement('/add/processing/${doc.id}');
    } on ApiException catch (e) {
      setState(() {
        _error = e.message;
        _progress = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final uploading = _progress != null;
    return Scaffold(
      appBar: AppBar(title: const Text('Add a policy')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          const Text(
            'Upload your policy document and we\'ll read it for you. Make sure it shows the policy number, '
            'start and end dates, premium, cover amount and insurer/plan name.',
            style: TextStyle(color: AppColors.textSecondary),
          ),
          const SizedBox(height: AppSpacing.lg),
          if (uploading) ...[
            Text('Uploading… ${(_progress! * 100).round()}%'),
            const SizedBox(height: AppSpacing.sm),
            LinearProgressIndicator(value: _progress),
          ] else ...[
            _SourceTile(
              icon: Icons.picture_as_pdf_rounded,
              title: 'Upload policy PDF',
              subtitle: 'Recommended · Best accuracy',
              onTap: () => _pick(images: false),
            ),
            if (!kIsWeb)
              _SourceTile(
                icon: Icons.photo_camera_rounded,
                title: 'Take a photo',
                subtitle: 'Place the policy on a flat, well-lit surface',
                onTap: _capture,
              ),
            _SourceTile(
              icon: Icons.photo_library_rounded,
              title: 'Upload a photo of the policy',
              subtitle: 'JPG or PNG',
              onTap: () => _pick(images: true),
            ),
            // TODO(P2): multi-page scanner with edge detection.
            _SourceTile(
              icon: Icons.edit_note_rounded,
              title: 'Enter details manually',
              subtitle: 'No document needed',
              onTap: () => context.pushReplacement('/add/manual'),
            ),
            const _SourceTile(icon: Icons.mail_outline_rounded, title: 'Import from Gmail', subtitle: 'Coming soon'),
          ],
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.md),
            Text(_error!, style: const TextStyle(color: AppColors.error)),
          ],
          const SizedBox(height: AppSpacing.lg),
          const Row(
            children: [
              Icon(Icons.lock_outline_rounded, size: 16, color: AppColors.textSecondary),
              SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  'Your documents are encrypted and only visible to you.',
                  style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SourceTile extends StatelessWidget {
  const _SourceTile({required this.icon, required this.title, required this.subtitle, this.onTap});
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: AppSpacing.sm),
    child: Card(
      child: ListTile(
        enabled: onTap != null,
        contentPadding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm),
        leading: Icon(icon, color: onTap != null ? AppColors.secondary : AppColors.textSecondary, size: 32),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle),
        trailing: onTap != null ? const Icon(Icons.chevron_right_rounded) : null,
        onTap: onTap,
      ),
    ),
  );
}
