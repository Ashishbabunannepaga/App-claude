# CapitUp brand (v2)

Name: **CapitUp** (fixed by the owner; the company is CapitUp India). Not a candidate exercise.

## Checks (screening only, not legal clearance) — all TO RUN by the owner

| check | where | status |
| --- | --- | --- |
| India trademark (class 9, 36, 42) | ipindiaservices.gov.in public search | to run |
| US / EU / WIPO | tmsearch.uspto.gov, EUIPO eSearch, WIPO Global Brand Database | to run |
| domain | capitupindia.com (owned); check capitup.in / capitup.app | to run |
| App Store / Play name | search "CapitUp" | to run |
| handles | X, Instagram, LinkedIn, GitHub | to run |

Not run here: this environment cannot reach those sites. Do not announce the name as "cleared" until a trademark lawyer has searched.

## Palette (tokens in `replica/design/tokens.json`, 0 AA failures)

Derived from the CapitUp logo (gold + teal), and deliberately a different family from the app it was modelled on (blue).

| role | value | use |
| --- | --- | --- |
| ink | #0B2B2E | hero panels, dark surfaces |
| primary | #0B7A75 | buttons, links, active states |
| gold | #F5A81C | coins, highlights, "money" moments |
| surface-tint | #EAF5F3 | tiles, chips, quiet cards |
| health / life / motor | #E5484D / #6D5BD0 / #2F7DE1 | policy-type accents (icons, fills) |

Status colours are for icons and fills. Text uses the darker `*-text` tokens.

## Logo brief

- Idea: *a policy that grows with you*. The supplied logo (gold swoosh + teal arrow) already says this.
- Keep the supplied mark. Needs: tight-cropped SVG + PNG with no empty margin, a one-colour version, and a 1024 x 1024 app icon with no transparency (iOS).
- Must work at 16 px. Must not resemble the original app's mark (it is a shield; ours is a rising swoosh).
- In-app: `mobile/assets/brand/logo.png`, auto-trimmed at runtime (see `BrandLogo`).

## Voice

Three words: **plain, warm, upfront.**

| we do | we don't |
| --- | --- |
| "Your policy doesn't mention ambulance cover." | "Ambulance: N/A" (cold) |
| "Not found in your document" | "Not covered" when we only failed to find it (guessing) |
| "Add your first policy. It takes a minute." | "Unlock your insurance journey!" (hype) |
| "We'll remind you 30 days before it ends." | "Never miss a thing!" (over-promise) |
| "We don't sell insurance." | silence on money (hidden incentives) |

Ten most-seen strings rewritten in this voice live in `mobile/lib/core/copy.dart`.

## Sweep

`python3 .claude/skills/replica-brand/sweep.py . --config replica/brand.json` must report clean (it is run in CI-free mode; `replica/` is skipped by design).
