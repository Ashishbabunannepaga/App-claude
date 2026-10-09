# v2 validation (replica-entrepreneur, honest version)

## What this can and cannot tell you

The entrepreneur skill validates a clone against **real user reviews**. The store review feeds were blocked from this cloud environment (see `fixes.md`), so **no review evidence was collected and none is claimed**. Parity 100 is measured against our own feature list, which I wrote. It shows the gaps *we found* are closed. It does not show the app is what users want.

## What was verified (checked, not assumed)

| check | result |
| --- | --- |
| Colour contrast, 23 text/background pairs | 0 AA failures (`replica/design/tokens.json`) |
| Leftovers of the original's name/domains | clean sweep |
| Automated tests | 24 Flutter + 51 backend pass; analyzer clean |
| Small phone (320 x 640) layout | found and fixed 2 overflows (intro pages, logo row); regression tests added |
| Screen reader | found and fixed double announcement of labelled buttons |
| Reduced motion | all animations (hero text, carousel, shimmer, illustrations) stop when the system asks |
| Empty / loading / error states | skeletons, illustrated empty states, retry on error |

## Not verified (needs you or users)

1. **Real device feel**: scrolling smoothness and haptics on a mid-range Android phone. Checked only on web renders and emulator builds.
2. **Your real logo**: auto-trim is built, but I have not seen your file. If it has a white box background, the trim treats near-white as empty.
3. **Real users**: nobody outside this session has used v2.
4. **Hindi / regional UI**: still English (gap G14).

## 5-person test plan (one afternoon)

Give five people a phone with the app and these tasks, saying nothing else. Note where each hesitates for more than 5 seconds.

1. "Add your health policy." (target: under 2 minutes)
2. "Is maternity covered?" (target: finds it in the report in under 30 s)
3. "Your car's insurance runs out soon. What would you do?"
4. "Someone in your family is in hospital. Find what you need."
5. "How would you earn coins?"

Pass bar: 4 of 5 complete tasks 1, 2 and 4 unaided. Anything below that is the next fix list. Then run `/replica-entrepreneur` again with real reviews in `replica/reviews.csv`.
