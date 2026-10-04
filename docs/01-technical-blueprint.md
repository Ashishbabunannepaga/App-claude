# Phase 1 — Technical Blueprint

> Working codename: **InsureIQ** (placeholder — replace product name, bundle IDs and branding before store submission).
> Every feature below is tagged **P0** (must have for V1), **P1** (should have if time permits), **P2** (V1.1/V2), **P3** (future).

---

## 1. Final V1 feature list

| # | Feature | Priority | Notes |
|---|---------|----------|-------|
| 1 | Mobile-number OTP login (India, +91) | P0 | SMS provider behind an interface (MSG91 / Twilio). Dev uses a console sender. |
| 2 | Email OTP login | P1 | Same OTP pipeline, different sender. |
| 3 | Secure sessions (short-lived access JWT + rotating refresh token) | P0 | Tokens in Keychain / Android Keystore via `flutter_secure_storage`. |
| 4 | Logout, logout-all-devices | P0 | Refresh tokens revoked server-side. |
| 5 | Account deletion (in-app) | P0 | Required by both stores and by DPDP. Hard-deletes documents + data after a 7-day grace window. |
| 6 | Basic profile (name, DOB, email, mobile, city/state) | P0 | Minimal data. |
| 7 | Family members (self, spouse, child, parent, other) | P1 | Policies can be linked to insured members. |
| 8 | Upload policy PDF | P0 | ≤ 20 MB, PDF only for the core flow. |
| 9 | Upload JPG/PNG (photo of policy) | P0 | Goes through OCR. |
| 10 | Scan document with camera (edge detection, multi-page) | P1 | `image_picker` camera in P0; true scanner UX in P1. |
| 11 | Manual policy entry | P0 | Same verification form as extraction, empty. |
| 12 | Document processing status, retry, delete, replace | P0 | |
| 13 | Text extraction (digital PDFs) + OCR (scans/images) | P0 | |
| 14 | Policy type classification (health / life / motor / other) | P0 | |
| 15 | AI structured extraction with per-field confidence | P0 | Cross-checked by deterministic regex validators. |
| 16 | User verification/correction of extracted fields | P0 | Policy is not "active" until user confirms. |
| 17 | Portfolio (grouped by type) + dashboard totals | P0 | |
| 18 | Policy detail screen | P0 | |
| 19 | AI policy summary ("Understand my policy") | P0 | Generated once per policy, cached. |
| 20 | AI Q&A grounded in the user's document (RAG) with citations | P0 | Refuses when the answer is not in the document. |
| 21 | Renewal tracking + push reminders (90/60/30/15/7 days, configurable) | P0 | |
| 22 | In-app notification inbox | P1 | |
| 23 | Claim assistance — static, per-policy-type guidance + insurer helpline | P0 | Content-driven, not AI, in V1. |
| 24 | Policy Health — simplified rules-based check for health policies | P1 | Rules over extracted fields (room rent, co-pay, restoration, etc.). |
| 25 | App lock (biometric / device PIN) | P1 | `local_auth`. |
| 26 | Privacy notice, consent capture, T&C, grievance officer contact | P0 | DPDP. |
| 27 | Admin panel (read-mostly ops view) | P1 | Minimal: users count, processing failures, support requests. PII masked. |
| 28 | Support / FAQ | P0 | Static FAQ + mailto/support form. |
| 29 | Crash reporting + analytics (privacy-safe, no policy content) | P0 | Firebase Crashlytics; analytics events without PII. |

## 2. V1 features explicitly excluded

| Feature | Priority | Reason |
|---------|----------|--------|
| Gmail policy discovery | P2 | Google restricted-scope OAuth verification (CASA security assessment) can take weeks — a launch-timeline risk. |
| DigiLocker integration | P2 | Requires partner onboarding/approval. |
| Insurance buying / comparison / recommendations / lead generation | P3 | Regulated by IRDAI — needs legal structure first. |
| Pro subscription (₹999/yr) & in-app payments | P3 | Monetisation after product-market fit; also store billing rules. |
| Rewards / coins | P3 | |
| Wellness (doctor, lab, pharmacy, nutrition) | P3 | |
| Motor Club (FASTag, challan, PUC) | P3 | |
| Utility/bill payments | P3 | |
| Unclaimed amount discovery | P3 | |
| AI claim assistant, claim tracking, hospital network | P2 | V1 has static claim guidance only. |
| Advanced gap analysis / AI health score | P2 | V1 has rules-based check only. |
| Local/self-hosted LLMs | P3 | Abstraction exists; no implementation. |
| Multi-language UI (Hindi etc.) | P2 | Strings are externalised from day 1 so this is cheap later. |
| Web app | P3 | |

## 3. Complete screen map

```
Splash ─► Onboarding (3 slides, P1) ─► Consent & Privacy ─► Login (phone) ─► OTP ─► Profile setup
                                                                                        │
┌──────────────────────────────── Bottom navigation ───────────────────────────────────┘
│
├── Home
│   ├── Coverage summary card
│   ├── Upcoming renewal card ─► Policy detail
│   ├── Quick actions: Add policy · Ask AI · Claim help · Family
│   ├── Policies by type
│   └── Insights (P1)
│
├── Portfolio
│   ├── Tabs/filters: All · Health · Life · Motor · Other
│   ├── Policy card ─► Policy detail
│   │                   ├── Summary (Understand policy)
│   │                   ├── Coverage details (type-specific sections)
│   │                   ├── Policy health (P1)
│   │                   ├── Ask AI ─► Chat (per-policy)
│   │                   ├── Renewal ─► Renewal info + reminder settings
│   │                   ├── Claim help ─► Claim guide
│   │                   ├── Document ─► Viewer / Replace / Delete
│   │                   └── Edit details ─► Verify form
│   └── + Add policy
│
├── Add policy (modal flow)
│   ├── Choose source: Upload PDF · Photo/Scan · Manual
│   ├── Upload progress
│   ├── Processing status (polling) ─► failure ─► Retry / Manual
│   └── Verify extracted details ─► Policy added
│
├── Explore
│   ├── Claim guides by type
│   ├── Insurance glossary / "Know your policy" articles
│   └── Coming soon tiles (Gmail import, DigiLocker, Wellness) — clearly labelled, no fake flows
│
└── Profile
    ├── Personal details · Family members (P1)
    ├── Notifications settings
    ├── App lock (P1)
    ├── Privacy & data (download my data P1, consent, delete account)
    ├── Terms · Privacy policy · Grievance officer
    ├── Support · FAQ
    └── Logout
```

## 4. User journeys

**J1 — First-time user adds first policy (the core loop, P0)**
1. Install → consent screen (privacy notice, purpose of processing) → phone + OTP.
2. Profile setup (name, optional DOB) → Home empty state with one primary CTA: *Add your first policy*.
3. Upload PDF → progress bar → "Reading your policy…" (status polling, typically 20–60 s).
4. Verify screen shows extracted fields; low-confidence fields highlighted amber; user fixes, confirms.
5. Policy detail → *Understand policy* summary → *Ask AI* → "Is maternity covered?" → grounded answer with page citation.

**J2 — Extraction fails / poor scan:** processing status `failed` or confidence low → user offered *Retry*, *Upload clearer copy*, or *Enter manually* (pre-filled with whatever was extracted).

**J3 — Renewal:** 30 days before expiry → push "Your Star Health policy expires in 30 days" → deep-link to policy → renewal card shows date, last premium, insurer contact. User marks *Renewed* → prompted to upload the new policy.

**J4 — Claim help:** Policy detail → Claim help → type-specific steps, document checklist, insurer helpline / TPA from extracted data.

**J5 — Delete account:** Profile → Privacy → Delete account → OTP re-confirm → account disabled immediately, data purged after 7 days (job), confirmation email/SMS.

## 5. Flutter architecture

- **Flutter (stable 3.x) + Dart 3**, single codebase for Android & iOS.
- **State management:** Riverpod (`flutter_riverpod`), without code generation to keep the build simple.
- **Navigation:** `go_router` with a `ShellRoute` for bottom navigation and auth redirect guard.
- **Networking:** `dio` with interceptors: auth header, silent refresh-on-401 (single-flight), error mapping to typed `AppException`.
- **Secure storage:** `flutter_secure_storage` (Keychain / EncryptedSharedPreferences) for tokens only. No policy data cached on device in V1 except in memory.
- **Config:** `--dart-define` for `API_BASE_URL`, `ENV`. **No secrets in the app** — the app only knows the public API URL.
- **Layering (feature-first):** `presentation` (widgets, controllers) → `data` (repositories, API DTOs). Domain models are plain immutable Dart classes with `fromJson`.
- **Design system:** `lib/app/theme/` — color tokens, typography, spacing; reusable widgets in `lib/core/widgets/` (AppButton, AppCard, StatusChip, EmptyState, ErrorState, LoadingState, MoneyText).
- **Every async screen** renders loading / error (with retry) / empty / data via `AsyncValue.when`.
- **Push:** `firebase_messaging` (FCM on Android, APNs via FCM on iOS) — added in Week 7.
- **Crash reporting:** Firebase Crashlytics (Week 9).

## 6. Backend architecture

```
                 ┌──────────────┐
 Flutter app ───►│  API (FastAPI)│──► PostgreSQL 16 + pgvector
   HTTPS/JWT     │  uvicorn/gunicorn   (users, policies, chunks, embeddings, audit)
                 └──────┬───────┘
                        │ enqueue
                        ▼
                 ┌──────────────┐      ┌───────────────────────┐
                 │ Redis (broker)│◄────►│ Celery workers         │──► Object storage (S3 / R2)
                 └──────────────┘      │  - process_document    │──► AI Gateway ─► Claude / OpenAI / Gemini
                                       │  - embed_chunks        │──► OCR (Tesseract → cloud OCR P1)
                                       │  - renewal_reminders   │──► FCM
                                       └───────────────────────┘
```

- **Python 3.11, FastAPI, SQLAlchemy 2.0 (sync), Alembic, Pydantic v2.**
- Modular monolith: `app/api` (routers), `app/services` (business logic), `app/models` (ORM), `app/schemas` (API DTOs), `app/ai` (gateway & providers), `app/processing` (pipeline), `app/storage`, `app/workers`.
- Sync SQLAlchemy is deliberate: simpler, shared by API and Celery, adequate at V1 scale.
- **Background jobs:** Celery + Redis. In dev/tests `TASKS_EAGER=true` runs jobs inline.
- **Provider abstractions** (swap by env var, no code change): `AIProvider`, `EmbeddingProvider`, `OCRProvider`, `StorageBackend`, `OtpSender`, `PushSender`.

## 7. Database ER diagram

```mermaid
erDiagram
    users ||--o{ refresh_tokens : has
    users ||--o{ family_members : has
    users ||--o{ device_tokens : has
    users ||--o{ documents : uploads
    users ||--o{ policies : owns
    users ||--o{ notifications : receives
    documents ||--o| policies : "source of"
    policies ||--o{ policy_chunks : "split into"
    policies ||--o{ qa_messages : "asked about"
    family_members }o--o{ policies : "insured under (policy_members)"

    users { uuid id PK; string phone UK; string email UK; string full_name; date date_of_birth; string city; string state; timestamptz consent_at; timestamptz deleted_at }
    otp_challenges { uuid id PK; string identifier; string code_hash; int attempts; timestamptz expires_at; timestamptz consumed_at }
    refresh_tokens { uuid id PK; uuid user_id FK; string token_hash UK; timestamptz expires_at; timestamptz revoked_at }
    documents { uuid id PK; uuid user_id FK; string storage_key; string content_type; int size_bytes; string sha256; string status; string error; int page_count; text extracted_text; string extraction_method }
    policies { uuid id PK; uuid user_id FK; uuid document_id FK; string policy_type; string insurer; string plan_name; string policy_number; date start_date; date end_date; numeric premium; numeric sum_insured; string payment_frequency; string status; bool verified; float extraction_confidence; jsonb field_confidence; jsonb details; text summary }
    policy_chunks { uuid id PK; uuid policy_id FK; int chunk_index; int page; string section; text content; vector embedding }
    qa_messages { uuid id PK; uuid policy_id FK; uuid user_id FK; text question; text answer; jsonb citations; string confidence; bool answerable }
    notifications { uuid id PK; uuid user_id FK; uuid policy_id FK; string kind; string dedupe_key UK; timestamptz scheduled_for; timestamptz sent_at; timestamptz read_at }
    audit_logs { uuid id PK; uuid user_id; string action; string entity; uuid entity_id; jsonb meta; string ip; timestamptz created_at }
```

Type-specific data (health room-rent, waiting periods; life riders; motor IDV, add-ons…) lives in `policies.details` (JSONB) validated by Pydantic schemas per policy type. This avoids 3 sparse tables and lets the schema evolve without migrations while the extraction model matures.

## 8. API specification (v1)

Base: `/api/v1`. JSON. Auth: `Authorization: Bearer <access_token>`. Errors: `{"error": {"code": "...", "message": "..."}}`. Full OpenAPI auto-generated at `/docs` (disabled in production).

| Method | Path | Purpose | Slice |
|--------|------|---------|-------|
| POST | `/auth/otp/request` | `{identifier}` → sends OTP. Rate-limited per identifier & IP. | ✅ |
| POST | `/auth/otp/verify` | `{identifier, code, consent}` → `{access_token, refresh_token, user, is_new_user}` | ✅ |
| POST | `/auth/refresh` | `{refresh_token}` → new pair (rotation; reuse of a revoked token revokes the family) | ✅ |
| POST | `/auth/logout` | revoke refresh token | ✅ |
| GET/PATCH | `/me` | profile | ✅ |
| DELETE | `/me` | schedule account deletion | ✅ |
| GET/POST/PATCH/DELETE | `/me/family[/{id}]` | family members | Wk 7 |
| POST | `/me/devices` | register push token | Wk 7 |
| POST | `/documents` | multipart upload → `{document}`; enqueues processing | ✅ |
| GET | `/documents/{id}` | status: `uploaded → processing → extracted / failed` + `policy_id` | ✅ |
| POST | `/documents/{id}/retry` | re-run pipeline | ✅ |
| GET | `/documents/{id}/url` | short-lived signed download URL | ✅ |
| DELETE | `/documents/{id}` | delete file + chunks | ✅ |
| GET | `/policies` | list (filter `type`) | ✅ |
| POST | `/policies` | manual entry | ✅ |
| GET/PATCH/DELETE | `/policies/{id}` | detail / verify-correct / delete | ✅ |
| POST | `/policies/{id}/confirm` | user verified extraction → `verified=true` | ✅ |
| GET | `/policies/{id}/summary` | AI summary (generated & cached) | ✅ |
| POST | `/policies/{id}/ask` | `{question}` → `{answer, answerable, confidence, citations[{page, section, excerpt}], disclaimer}` | ✅ |
| GET | `/policies/{id}/messages` | Q&A history | ✅ |
| GET | `/portfolio/summary` | totals, counts by type, upcoming renewals | ✅ |
| GET | `/policies/{id}/health` | rules-based health check | Wk 8 |
| GET | `/claims/guide?type=health` | claim guidance content | Wk 8 |
| GET/PATCH | `/notifications` | inbox | Wk 7 |
| GET | `/health` | liveness | ✅ |

## 9. Authentication architecture

- Identifier = E.164 phone (or email, P1). OTP = 6 digits, **stored as HMAC-SHA256** (never plaintext), 5-minute TTL, max 5 attempts, resend cooldown 30 s, max 5 requests/hour/identifier and per-IP limit.
- On verify: create user if new (consent timestamp + policy version recorded), issue **access JWT (HS256, 15 min)** with `sub`, `jti`, `type=access`, and an opaque **refresh token (30 days)** stored hashed. Rotation on every refresh; reuse detection revokes all of the user's tokens.
- Mobile stores tokens in secure storage; dio interceptor refreshes on 401 once, then logs out.
- Store review accounts: a server-side allow-listed **demo phone number with a fixed OTP**, configured only via environment variable (`REVIEW_LOGIN_IDENTIFIER`/`REVIEW_LOGIN_CODE`), never in the app.
- JWT signing key comes from the secrets manager; rotate via `kid` (P1).

## 10. Document processing architecture

```
POST /documents ─► validate (type sniffing by magic bytes, ≤ 20 MB, page limit 60)
               ─► sha256 (dedupe per user) ─► store in object storage (private bucket, SSE)
               ─► documents.status = uploaded ─► enqueue process_document
Worker:
  1. status = processing
  2. Text extraction
       PDF: pypdf text layer per page; if < 50 chars/page avg → treat as scanned → rasterise → OCR
       Image: OCR (Tesseract in V1; cloud OCR e.g. Google Document AI / AWS Textract as P1 upgrade)
  3. Classification: AI (+ keyword fallback) → health | life | motor | other
  4. Structured extraction: AI with JSON schema for the detected type; per-field confidence
  5. Validation: regex cross-check (policy number seen verbatim in text, dates parse & start < end,
     amounts plausible); disagreement lowers confidence
  6. Chunking (≈ 1,000 chars with 150 overlap, page-aware, heading-aware) → embeddings → policy_chunks
  7. Create draft policy (verified=false) → documents.status = extracted
  8. (Wk 7) push "Your policy is ready to review"
Any exception → status = failed with a user-safe error code; retry allowed (max 3 automatic retries for transient errors).
```

## 11. AI / RAG architecture

- **AI Gateway** (`app/ai/gateway.py`) exposes task-level methods: `classify`, `extract_policy`, `summarise`, `answer_question`. Each task has a versioned prompt in `app/ai/prompts.py`.
- **Providers** implement one interface `AIProvider.complete_json(system, user, schema_hint) -> dict`: `ClaudeProvider`, `OpenAIProvider`, `GeminiProvider` (P1), `LocalProvider` (P3), and `MockProvider` (dev/tests, **clearly marked MOCK** — uses deterministic heuristics, never used in production; startup refuses `AI_PROVIDER=mock` when `ENV=production`).
- **Embeddings**: `EmbeddingProvider` — OpenAI `text-embedding-3-small` (1536-d) by default; `HashingEmbedder` (MOCK, dev only).
- **RAG Q&A flow**
  1. Authorise: policy belongs to user.
  2. Embed question → pgvector cosine top-k (k=6) restricted to `policy_id` + keyword boost for exact terms (e.g. "maternity", "room rent").
  3. Context = structured fields + retrieved chunks, each labelled `[C1]…[C6]` with page numbers.
  4. LLM must return JSON `{answerable, answer, citations:[ids], confidence}` and is instructed to answer **only** from context and say it cannot find it otherwise.
  5. **Post-validation**: citations must reference provided chunk ids; if `answerable` but no valid citation → downgrade to "couldn't confirm from your document". Answers always carry a disclaimer ("Based on your policy document. Confirm with your insurer before making a claim decision.").
  6. Store Q&A for evaluation (users can 👍/👎 — P1).
- **Evaluation** (intern): golden set of questions per test policy with expected answers & pages; nightly script computing extraction field accuracy and Q&A groundedness.
- **Data handling with AI vendors**: use API tiers with zero-data-retention / no-training terms; document in DPDP vendor register; strip phone/email from prompts where not needed.

## 12. Storage architecture

- Private bucket (S3 or Cloudflare R2, `ap-south-1`/India region preferred for data residency comfort). Server-side encryption. No public ACLs.
- Keys: `users/{user_id}/documents/{document_id}.{ext}` — never contain names or policy numbers.
- Downloads only via **pre-signed URLs, 5-minute expiry**, issued after ownership check.
- Local filesystem backend for development only.
- Lifecycle: deleted documents removed immediately; account deletion purges prefix `users/{user_id}/`.

## 13. Notification architecture

- `device_tokens` table (FCM token, platform). iOS uses APNs through FCM (one integration).
- Celery beat job `renewal_reminders` runs daily 09:00 IST: for each verified, active policy compute days-to-expiry; for offsets `[90, 60, 30, 15, 7, 1]` (configurable per user, P1) create a `notifications` row with `dedupe_key = policy_id:renewal:offset` (unique → never double-sends) and push it.
- Event notifications: processing complete/failed.
- Quiet hours 21:00–09:00 IST; max 1 marketing-free push per day per user. No promotional pushes in V1.
- Push payloads contain **no policy details** — just "A policy needs your attention" style text + deep link id.

## 14. Security architecture

| Control | Implementation |
|---------|----------------|
| Transport | HTTPS only (TLS 1.2+), HSTS at load balancer |
| Secrets | Env vars injected from secrets manager (AWS Secrets Manager / Doppler); `.env` only for local dev, git-ignored |
| AuthN | OTP + JWT + rotating refresh tokens (see §9) |
| AuthZ | Every query filtered by `user_id` from token in the service layer; ownership tests in the test suite |
| Rate limiting | Per-IP and per-identifier for OTP; per-user for uploads and AI Q&A (Redis-backed in prod) |
| Input validation | Pydantic schemas; upload magic-byte sniffing, size/page limits; PDFs parsed in workers, not API |
| Data at rest | RDS/Cloud SQL encryption, bucket SSE, encrypted backups |
| Data in logs | No document text, OTPs, tokens or policy numbers in logs; structured logs with request id |
| Audit | `audit_logs` for login, upload, view document URL, delete, account deletion, admin access |
| Mobile | Tokens in secure storage; no policy data persisted on device; certificate pinning P1; app lock P1; screenshots allowed (P2 to restrict on doc viewer) |
| Admin | Separate role, SSO + MFA, PII masked by default |
| Deletion | Account delete → disable → purge job after 7 days (DB rows + storage prefix + vectors) |
| Monitoring | Sentry/Crashlytics, uptime checks, alerting on processing failure rate |
| Dependency hygiene | Dependabot/pip-audit, pinned versions |

## 15. Deployment architecture

- **Containers**: one image for API and worker (different commands). 
- **V1 hosting recommendation (simple, India region):** AWS `ap-south-1` — ECS Fargate (api ×2, worker ×1–2, beat ×1), RDS PostgreSQL 16 with pgvector, ElastiCache Redis, S3. Alternative cheaper path: Render/Railway + Neon/Supabase Postgres + R2 — acceptable for beta, re-evaluate for production data residency.
- **Environments:** `dev` (local), `staging` (TestFlight / Play internal testing), `production`.
- **CI (GitHub Actions):** backend lint + tests against Postgres+pgvector service; Flutter analyze + test; build artefacts on tags.
- **Migrations:** Alembic, run as a one-off task before deploy.
- **Backups:** RDS automated daily + PITR 7 days; S3 versioning on the documents bucket (with lifecycle to honour deletions).

## 16. Android / iOS release architecture

- Flavors via `--dart-define=ENV=staging|production` and separate API URLs; same bundle ID with staging distributed through internal tracks.
- **Android:** App Bundle (`.aab`), Play App Signing, upload keystore stored in CI secrets; internal → closed → production tracks. Data Safety form mirrors §14.
- **iOS:** Xcode automatic signing for dev; CI uses App Store Connect API key + `fastlane match` (P1). TestFlight → App Review. App Privacy labels; `PrivacyInfo.xcprivacy` manifest; account deletion in-app (Guideline 5.1.1(v)); demo login supplied in review notes.
- Versioning: `version: x.y.z+build` in `pubspec.yaml`, build number from CI run.
- Min OS: Android 7.0 (API 24), iOS 13+ (set per final plugin requirements).

## 17. Development folder structure

```
.
├── README.md
├── docs/
│   ├── 01-technical-blueprint.md      ← this file
│   └── 02-development-roadmap.md
├── backend/
│   ├── pyproject.toml / requirements*.txt
│   ├── alembic.ini, alembic/versions/
│   ├── app/
│   │   ├── main.py                     FastAPI app factory
│   │   ├── core/                       config, db, security, errors, rate limiting
│   │   ├── models/                     SQLAlchemy ORM
│   │   ├── schemas/                    Pydantic request/response models
│   │   ├── api/v1/                     routers: auth, me, documents, policies, portfolio
│   │   ├── services/                   business logic (auth, otp, policies, portfolio, qa)
│   │   ├── ai/                         gateway, prompts, providers/{claude,openai,mock}, embeddings
│   │   ├── processing/                 text extraction, OCR, chunking, validators, pipeline
│   │   ├── storage/                    local + S3/R2 backends
│   │   └── workers/                    celery app + tasks
│   ├── tests/
│   └── .env.example
├── mobile/
│   ├── pubspec.yaml
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app/                        app.dart, router.dart, theme/
│   │   ├── core/                       config, network, storage, utils, widgets/
│   │   └── features/
│   │       ├── auth/        {data, presentation}
│   │       ├── home/
│   │       ├── portfolio/
│   │       ├── policy/      add, processing, verify, detail
│   │       ├── assistant/   ask AI
│   │       ├── explore/
│   │       └── profile/
│   ├── android/  ios/
│   └── test/
├── docker-compose.yml                  postgres+pgvector, redis (local dev)
└── .github/workflows/                  CI
```
