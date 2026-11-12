# CapitUp client app — team handoff

**Read this first if you are new to the repo.** It covers what the app does, how the backend and the app fit
together, every API, and where things stand today. Install steps are in [`SETUP.md`](SETUP.md); this page links to
the other docs instead of repeating them.

*Status as of 12 Nov 2026, `develop` at PR #18. Owner: Ashish (tech lead). Update the "Current status" section
when you merge something that changes it.*

---

## 1. What the app is

CapitUp is an insurance broker (Hyderabad). This app lets **clients** keep all their policies in one place: health
(retail and group/GMC), motor, term and life. They upload a PDF or photo, the backend reads it with AI, and the app
explains the cover, answers questions from the client's own document, and reminds them before renewal.

For CapitUp, clients who **opt in** to being contacted become **leads in the LMS** (our Next.js CRM,
repo `CapitUpIndia_LMS_Web`). Nobody is contacted without that opt-in.

Goal: Google Play release under CapitUp's organisation account (D-U-N-S on file). Package name
`com.capitupindia.app` is final and can never change after the first upload.

## 2. Repo map

| Folder | What's in it |
|---|---|
| `backend/` | FastAPI API, database models, upload pipeline, AI providers, tests |
| `mobile/` | Flutter app (Android + iOS; `web/` only for screenshots) |
| `docs/` | This file, setup guide, blueprint, roadmap, troubleshooting, screenshots |
| `tools/` | Brand/icon generation, demo data and screenshot scripts |
| `docker-compose.yml` | Local Postgres (pgvector) + Redis only |
| `.github/workflows/` | `ci.yml` (tests on every PR), `android-apk.yml` (installable APK) |

Other docs: [`SETUP.md`](SETUP.md) (install and run, Windows included) ·
[`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) · [`01-technical-blueprint.md`](01-technical-blueprint.md) (original design) ·
[`BRANCHES.md`](BRANCHES.md) · [`DEMO.md`](DEMO.md).

## 3. Architecture

```
Flutter app ──HTTPS + JWT──► FastAPI (/api/v1) ──► PostgreSQL 16 + pgvector
     │                          │
     │ Firebase Phone Auth      ├─► Background jobs (inline in dev, Celery + Redis in production)
     │ (SMS + ID token)         │      ├─► Storage: local folder (dev) / S3 or Cloudflare R2
     └──────────────────────────┤      ├─► OCR: Tesseract → vision model fallback (OpenAI / Gemini)
                                │      └─► AI gateway: OpenAI | Claude | Gemini | offline mock
                                └─► /api/v1/partner/leads ◄── LMS cron (every 15 min, token-protected)
```

Every external service sits behind an interface chosen by an environment variable, so a vendor can be swapped
without code changes. The app holds **no secrets**, only the API URL and Firebase's public config.

## 4. Backend (`backend/`)

**Stack:** Python 3.11 (CI also runs 3.10), FastAPI, SQLAlchemy 2, Alembic, psycopg 3, Celery, pypdf/pypdfium2,
Tesseract (optional), httpx for AI calls. Lint/format: `ruff`. Tests: `pytest` (**140 passing**).

| Folder | Responsibility |
|---|---|
| `app/api/v1/` | HTTP routes, one file per area (see §6) |
| `app/services/` | Business logic: auth, policies, Q&A, coverage report, insights, rewards, notifications, push, consent |
| `app/processing/` | Upload pipeline: text extraction, OCR, AI extraction, validation, chunking, clause library |
| `app/ai/` | `gateway.py` picks the provider; `providers/` (openai, claude, gemini, mock); `prompts.py`; `embeddings.py` |
| `app/models/entities.py` | All database tables (§7) |
| `app/core/` | Settings (`config.py`), DB session, errors, security/JWT, rate limits, Sentry |
| `app/workers/` | Celery app and tasks, including scheduled jobs |
| `app/storage/` | Local and S3/R2 file storage |
| `app/static/` | `/privacy`, `/terms` pages and the `/admin` dashboard |
| `app/scripts/` | `ai_check` (test AI keys), `reembed` (after changing embeddings), `backfill_clauses` |
| `alembic/versions/` | Migrations `0001`–`0005` |

### How an upload is processed

`POST /documents` → file is checked (type sniffed, size ≤ 40 MB, ≤ 200 pages; scanned PDFs: first 30 pages OCR'd, ≤ 10 photos joined into one PDF),
de-duplicated by SHA-256, stored, then `process_document` runs in the background
(`app/processing/pipeline.py`):

1. **Text:** PDF text layer via pypdf. If a page has under 50 characters on average, treat it as scanned and OCR it.
   Print-locked PDFs open; PDFs needing a real password are refused. NUL and control characters are stripped.
2. **OCR:** `OCR_PROVIDER` (default Tesseract). If Tesseract isn't installed, falls back to the vision model of the
   configured AI provider (OpenAI or Gemini). With neither, the code is `ocr_unavailable`.
3. **Not a policy?** A keyword signal (`heuristics.py`) plus the AI's classification reject bank statements and
   similar (`not_a_policy`), so no junk draft policy is created.
4. **AI extraction** → `validate_extraction` checks each field is grounded in the text and gives per-field confidence.
5. A **draft policy** is saved (fields the user already confirmed are never overwritten), then text chunks with
   embeddings (for Ask AI) and the clause library (benefits, exclusions, waiting periods…).
6. Status becomes `extracted` or `failed` with an `error_code`, and the user gets a notification.

Uploading the **same file again after a failure** re-runs it; an already-read file is not read twice.
`POST /documents/{id}/retry` does the same, and also rescues documents stuck for 5+ minutes.

**Document status:** `uploaded → processing → extracted | failed`.
**Error codes the app shows messages for:** `pdf_password_protected`, `pdf_too_many_pages`, `pdf_unreadable`,
`no_text_found`, `ocr_unavailable`, `not_a_policy`, `ai_unavailable`, `processing_failed` (unexpected; check the log).

### Configuration (`backend/.env`, template `backend/.env.example`)

| Setting | Dev default | What it controls |
|---|---|---|
| `DATABASE_URL`, `REDIS_URL` | local Docker | Database and job queue |
| `TASKS_EAGER` | `true` | Run jobs inline (dev). Must be `false` in production, with a Celery worker + beat |
| `AI_PROVIDER` | `mock` | `openai` (current choice for testing), `claude`, `gemini`, `mock` |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | – / `gpt-4.1-mini` | OpenAI calls (extraction, summaries, Ask AI, vision OCR) |
| `EMBEDDING_PROVIDER` | `hashing` (fake) | `openai` / `gemini` / `local`. Run `python -m app.scripts.reembed` after changing it |
| `OCR_PROVIDER` | `tesseract` | `tesseract`, `openai`, `gemini`, `paddle`, `none` |
| `FIREBASE_PROJECT_ID` | unset | Enables phone login through Firebase (project `capitup-683ca`) |
| `OTP_SENDER` | `console` | Fallback OTP: codes print in the backend log. `msg91` needs DLT registration |
| `REVIEW_LOGIN_IDENTIFIER` / `_CODE` | unset | Fixed demo login for Play review and the demo scripts |
| `LEADS_API_TOKEN` | unset | Turns on the LMS leads feed; same value goes into the LMS as `APP_LEADS_TOKEN` |
| `STORAGE_BACKEND` | `local` | `s3` + bucket settings for production |
| `PUSH_SENDER` | `log` | `fcm` + service-account JSON for real push |
| `ADMIN_API_TOKEN` | unset | Protects `/admin` |

With `ENV=production` the server **refuses to start** if any dev-only setting is still on (mock AI, console OTP,
local storage, log push, in-memory rate limits, weak secrets, eager tasks).

**Scheduled jobs (Celery beat):** renewal reminders daily at 09:00 (90/60/30/15/7/1 days before expiry), and the
purge of accounts deleted more than 7 days ago, every 6 hours.

## 5. Mobile app (`mobile/`)

**Stack:** Flutter (Dart ≥ 3.13), Riverpod (state), go_router (navigation), Dio (HTTP), flutter_secure_storage
(tokens), Firebase Auth + Messaging, local_auth (app lock). Translations through gen-l10n: `lib/l10n/app_en.arb`
and `app_hi.arb` (English + Hindi, about 530 strings). Light/dark mode follows the phone.

| Folder | Responsibility |
|---|---|
| `lib/app/router.dart` | All screens and their paths |
| `lib/core/config/env.dart` | API URL. In debug builds without `API_BASE_URL` it finds the PC backend (`10.0.2.2:8000` on the emulator) |
| `lib/core/network/` | Dio client: adds the token, refreshes it on 401, maps API errors |
| `lib/core/` (other) | Brand, theme, push, app lock, storage, shared widgets |
| `lib/features/<area>/` | One folder per area: `data/` (repository + models), `presentation/` (screens) |

**Screens (routes):** splash, welcome, login, OTP, profile setup · home `/` · portfolio · explore · profile ·
add policy `/add` (PDF, photos with multi-page camera loop, manual) → processing `/add/processing/:documentId` →
verify `/policy/:id/verify` · policy detail `/policy/:id` with edit, Ask AI, health check, coverage report, nominees,
clauses · sample report · rewards · emergency card · family · insights · compare · notifications · settings
(notifications incl. the contact-consent switch, profile) · support · privacy.

**Login:** if Firebase is configured, the app sends the SMS through Firebase, then exchanges Firebase's ID token
at `POST /auth/firebase`. Without Firebase (or for email) it uses the backend's own OTP. Firebase config comes from
`mobile/firebase.json` (git-ignored; copy `firebase.example.json`):

```
flutter run --dart-define-from-file=firebase.json
```

Tests: `flutter analyze && flutter test` (618 passing at the last full run; widget, state, Hindi layout and
accessibility tests in `test/`).

## 6. API reference

Base path `/api/v1`. Interactive docs at **`http://localhost:8000/docs`** (disabled in production). Auth is
`Authorization: Bearer <access token>` unless marked otherwise. Access tokens last 15 minutes; refresh tokens
30 days and rotate on every use (reusing an old one revokes the session).

**Errors** always look like `{"error": {"code": "<stable_code>", "message": "<safe to show>"}}`. The app maps
`code` to a translated message, so **never rename a code**; add a new one instead.

| Area | Method + path | Purpose |
|---|---|---|
| Auth (no token) | `POST /auth/otp/request` | Send an OTP to a phone or email (backend OTP path) |
| | `POST /auth/otp/verify` | Verify OTP → tokens. Creates the user on first sign-in (needs `consent`; `contact_consent` optional) |
| | `POST /auth/firebase` | Sign in with a Firebase ID token (verified phone). Same body flags as above |
| | `POST /auth/refresh` | New access + refresh token |
| | `POST /auth/logout` | Revoke the refresh token |
| Me | `GET/PATCH/DELETE /me` | Profile, settings (incl. `contact_consent`), delete account (7-day grace) |
| | `GET /me/export` | Everything we hold about the user (DPDP right of access) |
| | `POST /me/devices`, `DELETE /me/devices/{token}` | Push tokens |
| | `GET/POST /me/family`, `PATCH/DELETE /me/family/{id}` | Family members |
| Documents | `POST /documents` | Upload (`file`, optional `pages[]` photos) → document with `status` |
| | `GET /documents/{id}` | Poll status, `error_code`, `policy_id` |
| | `POST /documents/{id}/retry` | Re-process a failed or stuck document |
| | `GET /documents/{id}/url` | Short-lived signed URL to view the file |
| | `DELETE /documents/{id}` | Delete |
| Policies | `GET/POST /policies` | List; create manually |
| | `GET/PATCH/DELETE /policies/{id}` | Detail, edit, delete |
| | `POST /policies/{id}/confirm` | User reviewed/corrected extracted fields |
| | `GET /policies/{id}/summary` | Plain-language summary (cached per language) |
| | `POST /policies/{id}/ask`, `GET /policies/{id}/messages` | Ask AI from the policy, with page citations; history |
| | `GET /policies/{id}/health` | Rules-based policy check (health, motor) |
| | `GET /policies/{id}/coverage-report` | Essentials / important / extras checklist with page refs |
| | `GET /policies/{id}/clauses` | Clause library |
| | `GET/POST /policies/{id}/nominees`, `PUT/DELETE …/{nominee_id}` | Nominees |
| | `PUT /policies/{id}/renewal` | Renewed / not renewing / pending (stops or restarts reminders) |
| | `GET /policies/compare` | Side-by-side of the user's own policies |
| Portfolio | `GET /portfolio/summary`, `GET /portfolio/insights` | Home dashboard totals; gap insights |
| Other | `GET /coverage/demo/{policy_type}` | Sample report for new users |
| | `GET /rewards` | Coins for organising (no cash value) |
| | `GET /notifications`, `/unread-count`, `POST /{id}/read`, `POST /read-all` | Inbox |
| | `POST /support` | Support request |
| | `POST /client-errors` | App crash/error reports |
| LMS (header `X-Leads-Token`) | `GET /partner/leads?cursor=` | Opted-in users only, keyset-paginated. Withdrawn users come back as `withdrawn` with no personal data |
| Admin (token) | `GET /admin/stats`, `/admin/documents/failed`, `/admin/support`, `PATCH /admin/support/{id}` | Ops dashboard data (PII masked); page at `/admin` |
| Public | `GET /health`, `/health/ready`, `/privacy`, `/terms` | Uptime checks and legal pages |

## 7. Data model

Tables (all in `app/models/entities.py`): `users` (incl. consent and contact-consent timestamps),
`otp_challenges`, `refresh_tokens`, `family_members`, `documents`, `policies` (fields + per-field confidence +
`details` JSON), `policy_chunks` (text + pgvector embedding), `policy_clauses`, `qa_messages`, `nominees`,
`notifications`, `device_tokens`, `support_requests`, `reward_events`, `audit_logs` (logins, uploads, consent changes).

**Changing the schema:** edit `entities.py`, then `alembic revision --autogenerate -m "…"`, review the file, and
`alembic upgrade head`. CI fails if migrations and models disagree.

## 8. LMS integration (leads)

1. At sign-up (checkbox) or later (Settings → Notifications switch) the user opts in to "CapitUp may contact me".
   It is off by default and audited with its version (`contact_consent_version`).
2. The LMS (`CapitUpIndia_LMS_Web`, Cloudflare Workers + D1) shows them under **Admin → App leads**. Handing one
   over creates a Retail lead linked by `app_user_id`.
3. Every 15 minutes the LMS cron reads the feed; users who withdrew consent get a do-not-contact note and the lead
   moves to Closed Lost.
4. LMS secrets: `APP_API_URL`, `APP_LEADS_TOKEN` (must equal the backend's `LEADS_API_TOKEN`).

## 9. How we work

- **Branches** ([`BRANCHES.md`](BRANCHES.md)): branch `feature/<name>` or `fix/<name>` from `develop`, open a PR into
  `develop`, merge once CI is green. `main` is only fast-forwarded after a phone test.
- **CI** runs on every PR: backend tests on Python 3.10 and 3.11 against Postgres with pgvector, migration check,
  ruff; Flutter analyze + tests; debug and release APK builds. Don't merge red.
- **Before you push:** `pytest -q && ruff check . && ruff format --check .` in `backend/`;
  `flutter analyze && flutter test` in `mobile/`.
- **Every behaviour change gets a test.** For a bug, write the test that fails first.
- **Never commit secrets:** `.env`, `firebase.json`, `google-services.json`, `key.properties`, `*.jks`, API keys,
  service-account JSON. Never put a real client's policy in the repo or the test data; test with your own or
  synthetic documents (`tools/demo/make_pdfs.py`).

## 10. Current status

**Done and working on the emulator**
- Firebase phone login (Spark plan: test numbers plus about 10 real SMS a day; SMS region set to India).
- Upload of PDFs and photos, including all edge cases: print-locked PDFs, password PDFs, page limit, size limit,
  non-policies, multi-photo, stuck documents, NUL characters, re-upload after failure.
- OpenAI as the AI and OCR provider (`gpt-4.1-mini`) when Tesseract isn't installed.
- Opt-in contact consent and the leads feed into the LMS (LMS side merged and deployed).
- CapitUp logo and app icon; English + Hindi; dark mode.

**In progress**
- Real-AI accuracy test: upload 3–5 real policies (health, motor, term) owned by team members, compare the review
  screen against the PDF, and fix extraction rules field by field. The first motor PDF (13 pages) now gets through
  the pipeline; its field check is pending.

**Full launch checklist:** [`PRODUCTION-READINESS.md`](PRODUCTION-READINESS.md) (AI, infrastructure, login, Play Store, legal, operations).

**Not started / waiting on someone** (from the 73-task delivery plan, Play launch target 24 Dec)

| Item | Owner | Notes |
|---|---|---|
| Play Console organisation account | Ashish / management | D-U-N-S ready |
| Release signing key (`.jks`) | Ashish | Back it up; losing it means a new app listing |
| Production server, database, storage | On hold | Testing is local-only for now |
| Real push notifications (FCM) | Dev | Needs the service-account JSON on the server, never in chat or git |
| IRDAI broker licence number in `privacy.html` | Management | Placeholder bracket still there |
| Legal review of privacy page and terms | Management + lawyer | Lists OpenAI and Firebase as processors |
| Native Hindi review of app strings | Anyone fluent | `mobile/lib/l10n/app_hi.arb` |
| OpenAI Zero Data Retention (optional) | Ashish | Apply to OpenAI before launch if we want no 30-day retention |
| MSG91 + DLT for our own SMS | Optional | Only if we move off Firebase SMS |

## 11. Known gotchas (Windows dev PC)

- **Stop the backend with Ctrl+C, never by closing the window.** Closing leaves a hidden Python process on port 8000
  that keeps answering with old code. Check with `netstat -ano | findstr :8000`; clear it with:
  `Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'uvicorn|spawn_main' } | % { Stop-Process -Id $_.ProcessId -Force }`
- **Run only one backend.** If your backend window shows no request lines while you use the app, the app is talking
  to a different one.
- **Postgres must be running:** "Database unreachable" means run `docker compose up -d` in the repo root.
  `wsl --shutdown` or a Docker restart stops it.
- **Keep 15 GB+ free on C:.** A full disk breaks Flutter builds and uploads. Docker build cache is the usual
  culprit: `docker builder prune -a -f`.
- **Gradle errors like "Directory does not exist" or "resource not found"** after a cleanup mean a half-deleted cache:
  `gradlew --stop`, delete `%USERPROFILE%\.gradle\caches` fully, `flutter clean`, build again.
- More in [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

## 12. Who to ask

Ashish (tech lead) for access, keys and decisions: GitHub, Firebase project `capitup-683ca`, OpenAI key, LMS.
Keys are shared one-to-one, never in group chats, issues or commits.
