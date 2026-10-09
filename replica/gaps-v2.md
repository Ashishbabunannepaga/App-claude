# Gap list for CapitUp v2 (replica-diff)

Compared: (a) the original's screens we have on file, (b) the "modern, illustrated, food-delivery-grade" bar you asked for, (c) our v0.3 app.
Parity before this round: 98.6 on the original's feature list. The gaps below are mostly *experience* gaps, which the feature score can't see.

| # | gap | type | priority | plan |
|---|-----|------|----------|------|
| G1 | Logo too small: the supplied PNG has empty margin, so any height looks tiny | bug (user-reported) | must | runtime auto-trim of transparent margin, then size by visible logo |
| G2 | Loading is a spinner everywhere | experience | must | shimmer skeletons shaped like the real content |
| G3 | Home is a list; no visual hook or illustration | experience | must | hero panel + illustrated service grid (bento) |
| G4 | Welcome pages are one icon in a circle | experience | must | full-colour illustrated pages, animated, per-page tint |
| G5 | No emergency card (the original has an emergency button in its header) | feature | must | offline-friendly card: policy numbers (tap to copy), 112 / 108, insurer helpline "see your policy" |
| G6 | Flat bottom bar, Add is buried | experience | should | floating pill nav with a centre Add button |
| G7 | No search/ask entry on Home | experience | should | "Ask about your cover" bar |
| G8 | Policy cards are plain list tiles | experience | should | type-tinted cards with art, validity ring, status chip |
| G9 | No touch feedback | experience | should | pressable scale + light haptics |
| G10 | Empty states are an icon + text | experience | should | illustrated empty states |
| G11 | Add-ons are not collapsible on the report | feature | could | collapsible section |
| G12 | Scenario carousel doesn't auto-advance | experience | could | slow auto-advance, pauses on touch, off for reduced motion |
| G13 | Coins arrive silently | experience | could | animated "+50" toast |
| G14 | App screens English only | feature | next | move strings to l10n (Hindi first) |
| G15 | No dark mode | experience | next | tokens already role-based; add dark set |

Out of scope on purpose (same as before): Buy tab, brand gift cards, coin-to-rupee value.
