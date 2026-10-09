import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/brand.dart';
import '../../../core/security/app_lock.dart';
import '../../../core/ui/art.dart';

final onboardingDoneProvider = NotifierProvider<OnboardingController, bool>(OnboardingController.new);

class OnboardingController extends Notifier<bool> {
  static const _key = 'onboarding_done';

  @override
  bool build() => ref.read(sharedPrefsProvider).getBool(_key) ?? false;

  Future<void> complete() async {
    await ref.read(sharedPrefsProvider).setBool(_key, true);
    state = true;
  }
}

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _Page {
  const _Page(this.scene, this.bg, this.title, this.body);
  final Scene scene;
  final Color bg;
  final String title;
  final String body;
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _controller = PageController();
  int _page = 0;

  static const _pages = [
    _Page(
      Scene.organise,
      AppColors.surfaceTint,
      'All your cover, one place',
      'Health, life and motor policies for the whole family, kept safe and easy to find.',
    ),
    _Page(
      Scene.ask,
      Color(0xFFFFF3D6),
      'Ask in plain words',
      'Every answer points to the page it came from, or tells you it isn\'t in your policy.',
    ),
    _Page(
      Scene.remind,
      Color(0xFFEDEAFB),
      'Renewals never sneak up',
      'A gentle nudge well before your policy ends, so you are never left uncovered.',
    ),
    _Page(
      Scene.family,
      Color(0xFFFDECEC),
      'Family and nominees, sorted',
      'See who is covered, who gets what, and what to do if something happens.',
    ),
  ];

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _finish() => ref.read(onboardingDoneProvider.notifier).complete();

  @override
  Widget build(BuildContext context) {
    final last = _page == _pages.length - 1;
    final reduce = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    return AnimatedContainer(
      duration: reduce ? Duration.zero : const Duration(milliseconds: 350),
      color: _pages[_page].bg,
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.sm, 0),
                child: Row(
                  children: [
                    const Expanded(
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: FittedBox(fit: BoxFit.scaleDown, child: BrandLogo(height: 44)),
                      ),
                    ),
                    TextButton(onPressed: _finish, child: const Text('Skip')),
                  ],
                ),
              ),
              Expanded(
                child: PageView.builder(
                  controller: _controller,
                  itemCount: _pages.length,
                  onPageChanged: (i) => setState(() => _page = i),
                  itemBuilder: (context, i) {
                    final p = _pages[i];
                    return LayoutBuilder(
                      builder: (context, box) {
                        // The illustration takes what the screen can spare, so small phones never overflow.
                        final art = (box.maxHeight * 0.52).clamp(120.0, 320.0);
                        return SingleChildScrollView(
                          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
                          child: ConstrainedBox(
                            constraints: BoxConstraints(minHeight: box.maxHeight),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                SceneArt(p.scene, size: art),
                                const SizedBox(height: AppSpacing.md),
                                Semantics(
                                  header: true,
                                  child: Text(
                                    p.title,
                                    textAlign: TextAlign.center,
                                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 28),
                                  ),
                                ),
                                const SizedBox(height: AppSpacing.md),
                                Text(
                                  p.body,
                                  textAlign: TextAlign.center,
                                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 16, height: 1.45),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  for (var i = 0; i < _pages.length; i++)
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 220),
                      margin: const EdgeInsets.all(4),
                      width: i == _page ? 28 : 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: i == _page ? AppColors.primary : AppColors.primary.withValues(alpha: 0.25),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                ],
              ),
              Padding(
                padding: const EdgeInsets.all(AppSpacing.lg),
                child: FilledButton(
                  onPressed: () => last
                      ? _finish()
                      : _controller.nextPage(duration: const Duration(milliseconds: 320), curve: Curves.easeOutCubic),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(last ? 'Get started' : 'Next'),
                      const SizedBox(width: 8),
                      const Icon(Icons.arrow_forward_rounded, size: 20),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
