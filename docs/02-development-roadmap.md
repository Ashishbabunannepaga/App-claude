# Phase 2 — Development Roadmap (12 weeks)

**Team:** **Lead** = you (technical/product lead: backend, AI, DB, architecture) · **Mobile** = Flutter developer · **Intern** = AI & Software Engineering intern · **Design** = part-time UI/UX · **Legal** = external counsel.

Assumed start: Monday 5 Oct 2026 → target store submission in Week 11 (14–18 Dec 2026), public release by early Jan 2027 including review buffer. Indian festive season (Diwali ~8 Nov 2026) falls in Week 5 — plan reduced capacity.

Status legend: ✅ done in this repository · 🔲 to do.

---

## Week 0 (start immediately, runs in parallel all project long) — External dependencies

| Task | Owner | Acceptance |
|------|-------|-----------|
| D-U-N-S number for the company | Lead | Number issued (can take 1–3 weeks) |
| Apple Developer **organisation** account (US$99/yr) | Lead | Account approved |
| Google Play **organisation** account (US$25) + verification | Lead | Account verified |
| Company domain, support email, website with privacy policy URL | Lead | Live URLs |
| Privacy Policy, T&C, grievance officer (DPDP) | Legal | Signed-off drafts |
| IRDAI opinion that V1 (organise/understand own policies, no selling) is permissible | Legal | Written opinion |
| AI vendor DPAs / zero-retention terms; OCR vendor review | Lead + Legal | Vendor register |
| Collect 50–100 anonymised policy documents (health/life/motor, digital + scanned) | Intern | Dataset in private bucket with labels sheet |
| SMS provider + DLT template registration (TRAI requirement for OTP SMS in India) | Lead | DLT template approved — **long lead time, start now** |

## Week 1 — Foundation

| Tasks | Owner |
|-------|-------|
| ✅ Repo, folder structure, blueprint, roadmap | Lead |
| ✅ FastAPI skeleton, config, Postgres+pgvector, Alembic, docker-compose | Lead |
| ✅ Flutter project, theme tokens, router, network layer | Mobile |
| 🔲 Figma: design system + core screens (login, home, portfolio, add, verify, detail, chat) | Design |
| 🔲 Requirements freeze (this doc + blueprint signed off) | Lead |
| 🔲 Labelling sheet schema for the test dataset | Intern |

**Deliverables:** running backend `/health`, Flutter app boots on Android emulator + iOS simulator. **Acceptance:** CI green; one-command local setup documented.

## Week 2 — Authentication & data model

| Tasks | Owner |
|-------|-------|
| ✅ OTP request/verify, JWT + rotating refresh, logout, account deletion endpoint | Lead |
| ✅ User, policy, document, chunk, Q&A models + migration | Lead |
| ✅ Login/OTP/profile screens, secure token storage, auth guard, silent refresh | Mobile |
| ✅ Real SMS provider integration (behind `OtpSender`) | Lead |
| 🔲 Consent screen copy from Legal | Mobile + Legal |
| 🔲 Auth tests (rate limits, expiry, reuse detection) — extend | Intern |

**Dependencies:** DLT template for SMS. **Acceptance:** a new user can sign up on a real device; tokens survive app restart; logout revokes.

## Week 3 — Upload & storage

| Tasks | Owner |
|-------|-------|
| ✅ `POST /documents` with validation, sha256 dedupe, local + S3/R2 storage, signed URLs | Lead |
| ✅ Add-policy source chooser, file picker, upload progress, processing status polling | Mobile |
| ✅ Camera capture (`image_picker`) for photos | Mobile |
| 🔲 Staging infrastructure (DB, bucket, Redis, worker) | Lead |
| 🔲 Label first 30 documents (ground-truth fields) | Intern |

**Acceptance:** upload 20 MB PDF on 4G with progress; file is private in bucket; delete removes it.

## Week 4 — Extraction pipeline

| Tasks | Owner |
|-------|-------|
| ✅ Text extraction (pypdf) + OCR fallback (Tesseract) | Lead |
| ✅ Classification + AI structured extraction + regex validation + confidence | Lead |
| ✅ Verify/correct screen with low-confidence highlighting, manual entry | Mobile |
| 🔲 Type-specific detail schemas (health/life/motor) refined against dataset | Lead + Intern |
| 🔲 Extraction accuracy script vs labelled set | Intern |

**Acceptance:** ≥ 90% accuracy on the six core fields (number, insurer, start, end, premium, cover) on digital PDFs; ≥ 75% on scans; every failure recoverable via manual entry.

## Week 5 — Embeddings & RAG (festive week — lighter)

| Tasks | Owner |
|-------|-------|
| ✅ Chunking, embeddings, pgvector search, Q&A endpoint with citations & refusal | Lead |
| ✅ Chat screen with citations, disclaimer, loading/error states | Mobile |
| 🔲 Golden Q&A set (10 questions × 30 policies) | Intern |

**Acceptance:** answers cite a page; out-of-document questions are refused, not invented.

## Week 6 — Intelligence quality

| Tasks | Owner |
|-------|-------|
| ✅ Policy summary ("Understand my policy") | Lead |
| 🔲 Hybrid retrieval (keyword + vector), prompt tuning, eval loop | Lead + Intern |
| 🔲 Cost & latency budget per question (target < 6 s p90) | Lead |
| ✅ Policy detail screen with type-specific sections | Mobile |

**Acceptance:** groundedness ≥ 95% and "correct or correctly-refused" ≥ 85% on the golden set.

## Week 7 — Portfolio, family, notifications

| Tasks | Owner |
|-------|-------|
| ✅ Portfolio summary API + home dashboard + portfolio screen | Lead + Mobile |
| ✅ Family members CRUD + link policy to insured members | Lead + Mobile |
| ✅ FCM/APNs setup, device token registration, processing-complete push | Mobile + Lead |
| ✅ Renewal reminder job (90/60/30/15/7/1 days, dedupe) | Lead |

**Dependencies:** Apple account (APNs key). **Acceptance:** reminder received on both platforms on a test policy with a near expiry date; never duplicated.

## Week 8 — Renewal, claims, policy health

| Tasks | Owner |
|-------|-------|
| ✅ Renewal card, "mark as renewed" → upload new policy | Mobile + Lead |
| ✅ Claim guidance content (health cashless/reimbursement, motor, life) + screens | Lead + Mobile |
| ✅ Rules-based Policy Health for health policies (P1) | Lead |
| ✅ Explore tab (guides, glossary, "coming soon" tiles) | Mobile |
| ✅ Profile: notifications, privacy, support, FAQ, delete account flow | Mobile |

**Acceptance:** **feature freeze** at end of week.

## Week 9 — Hardening I

| Tasks | Owner |
|-------|-------|
| 🔲 Security review: authZ tests on every endpoint, ✅ Redis rate limits, log scrubbing, pip-audit | Lead |
| 🔲 Crashlytics, Sentry, uptime alerts | Mobile + Lead |
| 🔲 Device matrix testing (low-end Android, small iPhone, tablets off) | Intern + Mobile |
| 🔲 Accessibility pass (contrast, text scaling, screen readers) | Mobile + Design |

## Week 10 — Hardening II

| Tasks | Owner |
|-------|-------|
| 🔲 Performance: cold start < 3 s, list rendering, API p95 < 500 ms (non-AI) | Mobile + Lead |
| 🔲 Full AI regression run, fix top failure modes | Lead + Intern |
| 🔲 Bug bash, UI polish | All |
| ✅ Admin panel (minimal, PII-masked) (P1) | Lead |

**Acceptance:** zero P0/P1 bugs open.

## Week 11 — Launch preparation & submission

| Tasks | Owner |
|-------|-------|
| 🔲 Production infra, backups, migrations, secrets | Lead |
| 🔲 Store listings, screenshots, descriptions, Data Safety, App Privacy, PrivacyInfo.xcprivacy | Mobile + Design |
| 🔲 Review demo account (server-side) + review notes | Lead |
| 🔲 Submit to Play (closed testing → production) and App Store | Mobile |

## Week 12 — Review & release

| Tasks | Owner |
|-------|-------|
| 🔲 Respond to review rejections, resubmit | Mobile + Lead |
| 🔲 Staged rollout (Play 10% → 100%), phased release (iOS) | Mobile |
| 🔲 Monitoring, on-call, feedback channel | All |

**Buffer:** Weeks 13–14 absorb store-review cycles and verification delays.

---

## Risk register (live)

| Risk | Mitigation |
|------|-----------|
| Scope creep | P0–P3 tags; anything new defaults to P2 unless it replaces a P0 |
| AI hallucination | Citation-required answers, post-validation, refusal path, golden-set eval |
| Poor OCR | Confidence flags + mandatory user verification + manual entry |
| SMS DLT delays | Start in Week 0; email OTP as fallback (P1) |
| Store account / D-U-N-S delays | Start Week 0 |
| Gmail restricted-scope verification | Deferred to V2 |
| Regulatory | No selling/recommendation in V1; legal opinion before any |
| Lead bottleneck | Mobile owns all Flutter; intern owns dataset + evaluation |
