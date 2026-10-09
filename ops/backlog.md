# Backlog — single source of truth

Format (one task per line, `|`-separated; the tool `ops/planner.py` reads and rewrites this file):

    - [ ] ID | P0-P3 | project | title | due=YYYY-MM-DD | carried=N | note

- `[ ]` open · `[x]` done · `[!]` blocked (never planned until you unblock it)
- **P0** must happen today/this week or the launch slips · **P1** important · **P2** normal · **P3** nice to have
- `due=` and `carried=` are optional. `carried` counts days a planned task was not finished; it raises the score.
- Seeded on 2026-10-08 from `docs/02-development-roadmap.md`, `docs/04-vision-plan.md` and `README.md`.
  Statuses are my best guess from the repo — correct anything already done.

## Launch blockers (long lead time — start early)

- [ ] CAP-001 | P0 | launch | SMS provider + DLT template registration (MSG91, TRAI) | due=2026-10-12 | carried=0 | Long lead time; OTP login needs it
- [ ] CAP-002 | P0 | launch | D-U-N-S number for the company | due=2026-10-12 | carried=0 | Takes 1-3 weeks; blocks Apple org account
- [ ] CAP-003 | P0 | launch | Apple Developer organisation account (US$99/yr) | due=2026-10-26 | carried=0 | Needs D-U-N-S
- [ ] CAP-004 | P1 | launch | Google Play organisation account (US$25) + verification | due=2026-10-26 | carried=0 |
- [ ] CAP-005 | P0 | legal | IRDAI opinion that V1 (organise/understand own policies, no selling) is permissible | due=2026-10-30 | carried=0 |
- [ ] CAP-006 | P1 | legal | Privacy Policy, T&C, grievance officer (DPDP) signed-off drafts | due=2026-10-30 | carried=0 |
- [ ] CAP-007 | P1 | legal | AI vendor DPAs / zero-retention terms; OCR vendor review | due=2026-11-06 | carried=0 |
- [ ] CAP-008 | P1 | launch | Company domain, support email, website with privacy policy URL | due=2026-10-30 | carried=0 |
- [ ] CAP-009 | P1 | data | Collect 50-100 anonymised policy documents with labels sheet | due=2026-11-13 | carried=0 | Feeds golden Q&A set and future fine-tuning

## App: keys, config, identity

- [ ] CAP-010 | P1 | app | Create Firebase project; set FCM_* env vars and FIREBASE_* dart-defines; upload APNs key | due=2026-10-16 | carried=0 | Push does not work without it
- [ ] CAP-011 | P1 | app | Switch to real AI (AI_PROVIDER=claude + ANTHROPIC_API_KEY, EMBEDDING_PROVIDER=openai) and test on 5 real policies | due=2026-10-20 | carried=0 | Real providers untested
- [ ] CAP-012 | P1 | app | Replace bundle ID com.insureiq.insureiq, app icon, final logo | due=2026-11-06 | carried=0 | Before first store upload
- [ ] CAP-013 | P2 | app | S3/R2 bucket for production storage (STORAGE_BACKEND=s3) | due=2026-11-13 | carried=0 |
- [ ] CAP-014 | P2 | app | Run replica-brand sweep for leftovers of the original app | carried=0 |

## Product: next code milestones (docs/04-vision-plan.md)

- [ ] CAP-020 | P1 | product | AI claim checklist per policy | carried=0 |
- [ ] CAP-021 | P1 | product | Emergency card (offline) with helplines and policy numbers | carried=0 |
- [ ] CAP-022 | P2 | product | App UI translation to Hindi via flutter gen-l10n | carried=0 |
- [ ] CAP-023 | P2 | product | Table-aware PDF parsing (docling / pdfplumber) | carried=0 |
- [ ] CAP-024 | P2 | product | Deploy ML worker (PaddleOCR + bge-m3) to staging; run re-embed script | carried=0 |
- [ ] CAP-025 | P3 | product | Voice questions (speech-to-text into the Q&A pipeline) | carried=0 |

## Quality and launch prep

- [ ] CAP-030 | P1 | quality | Golden Q&A set per policy type to measure every AI change | carried=0 |
- [ ] CAP-031 | P2 | quality | Run replica-test end-to-end pass; file bugs | carried=0 |
- [ ] CAP-032 | P2 | launch | Store listings and screenshots (replica-launch) | due=2026-12-04 | carried=0 |
- [ ] CAP-033 | P0 | launch | Feature freeze, then store submission (roadmap Week 11: 14-18 Dec) | due=2026-12-14 | carried=0 |
