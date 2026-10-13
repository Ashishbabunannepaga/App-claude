# Plan: Hindi UI (G14) and dark mode (G15)

Date: 2026-10-13. Status: plan only, not started. Measured on `develop`.

## Where the app is today

| Measure | Count |
|---|---|
| Hard-coded English strings in widgets (`Text('…')` literals) | 136, plus labels, snackbars and dialog text (estimate ~300 in total) |
| Hard-coded colours outside the theme (`Color(0x…)`) | 82, in 13 files |
| Localisation set up (`flutter_localizations`, ARB files) | No |
| Dark theme | No (`ThemeData` light only) |
| Already multilingual | AI answers and summaries (9 languages, set per user); Devanagari, Bengali, Gujarati fonts bundled |

## Hindi UI (about 3 working days of build + your review)

1. Add `flutter_localizations` and `gen-l10n` (ARB files `app_en.arb`, `app_hi.arb`).
2. Move every user-facing string into `app_en.arb`, screen by screen, starting with the core flow: welcome, login, home, coverage report, policy check, Ask AI.
3. Hindi strings: I draft them; **a native Hindi speaker on your side reviews them** (insurance terms such as "waiting period", "co-payment", "sum insured" need the words Indian policyholders actually use, often kept in English).
4. Language switch in Profile > Settings; the existing `preferred_language` field already drives AI answers, so the UI follows the same setting.
5. Tests: the layout sweep runs again in Hindi (Devanagari is taller; this is where overflow shows up).

## Dark mode (about 2 working days)

1. Dark token set in `replica/design/tokens.json` and `AppColors` (contrast-checked to WCAG AA).
2. Replace the 82 inline colours with theme roles, file by file.
3. `darkTheme` + `ThemeMode.system`, with a manual override in Settings.
4. Illustrations (`SceneArt`) get dark-surface variants; the brand teal and gold stay.
5. Tests: layout and accessibility sweeps in both themes; screenshots of the core screens in dark.

## Order

Hindi first (it matters more to the users CapitUp is for), then dark mode. Both after the Gemini real-policy test and the phone re-test, since fixes from those come first.

## What I need from you

- Go-ahead on the order above.
- A Hindi reviewer (a few hours, once the strings are drafted).
