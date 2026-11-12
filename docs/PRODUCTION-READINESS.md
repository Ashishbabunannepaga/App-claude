# Production readiness: CapitUp client app

What has to be true before real clients use the app on Google Play. **Tick items as they're done** and keep the
owner column honest. Status as of 12 Nov 2026.

Legend: ✅ done · 🟡 partly · ⬜ not started · **P0** = blocks launch · **P1** = within a month of launch.

## 1. AI layer

| | Item | Status | Notes |
|---|---|---|---|
| P0 | Answers only from the client's own document, with page citations; "not found" instead of guessing | ✅ | Answers that cite nothing are replaced with "not found" |
| P0 | Insurers' names for the same cover (zero dep = depreciation reimbursement …) | ✅ | PRs #21, #22 |
| P0 | Government IDs (Aadhaar, PAN, bank account) masked before any AI call | ✅ | `app/ai/guardrails.py`. **Photos and scanned pages still go to the vision model as images**; see next row |
| P1 | Scanned/photo pages: decide whether images may go to OpenAI, or OCR on our server first (Tesseract/PaddleOCR) and send only masked text | ⬜ | Product + legal decision |
| P0 | Document text treated as data (prompt-injection guard) | ✅ | In every system prompt. A malicious PDF can only mislead its own uploader's results |
| P0 | Figures in answers checked against the policy text; unmatched → low confidence + log | ✅ | |
| P0 | Long documents keep schedule pages when trimmed (60k characters) | ✅ | Logged when it happens |
| P0 | Retries on rate limits / provider errors; clear "AI unavailable" message otherwise | ✅ | OpenAI, Claude, Gemini |
| P0 | **Accuracy test set**: 20–30 real policies (health retail + GMC, motor, term, life; text and scanned) with the correct values written down, run before every prompt or model change | ⬜ | Team members' own policies, stored outside the repo. Today we have 1 checked policy |
| P0 | Pin the model version (e.g. `gpt-4.1-mini-2025-04-14`) so answers don't change under us | ⬜ | `OPENAI_MODEL` in production `.env` |
| P0 | OpenAI: org account in CapitUp's name, monthly spend limit and alerts in the OpenAI dashboard | ⬜ | Usage per task is now logged (`app.ai.usage`) |
| P1 | OpenAI Zero Data Retention (no 30-day abuse-monitoring copy) | ⬜ | Apply to OpenAI; until then the privacy page says 30 days |
| P1 | Per-user daily AI budget (today: hourly limits of 30 uploads, 60 questions, 30 summaries) | 🟡 | Add a daily cap if costs spike |
| P1 | Follow-up questions ("what about my wife?") | ⬜ | Q&A is single-turn by design today: each question is answered on its own, so no conversation history builds up or leaks between questions |
| P1 | Human review queue for low-confidence extractions (ops team checks before the client sees it) | ⬜ | `/admin` shows failed documents only |

## 2. Backend and infrastructure

| | Item | Status | Notes |
|---|---|---|---|
| P0 | Production server (region India), managed Postgres with pgvector, automated daily backups + a tested restore | ⬜ | On hold. Data should stay in India (DPDP) |
| P0 | Object storage (S3 `ap-south-1` or Cloudflare R2) with encryption; `STORAGE_BACKEND=s3` | ⬜ | |
| P0 | Celery worker + beat + Redis (`TASKS_EAGER=false`, `RATE_LIMIT_BACKEND=redis`) | ⬜ | Renewal reminders and account purge need beat |
| P0 | `ENV=production` with strong `JWT_SECRET`, `OTP_HMAC_SECRET`, `ADMIN_API_TOKEN`, `LEADS_API_TOKEN` from a secrets manager | ⬜ | Server refuses to start with dev settings |
| P0 | HTTPS domain (e.g. `api.capitupindia.com`), CORS locked down | ⬜ | |
| P0 | Error tracking (Sentry `SENTRY_DSN`) and uptime check on `/health/ready` | ⬜ | Code is ready |
| P1 | `/admin` behind company SSO instead of a shared token | ⬜ | |
| P1 | Load test: 50 concurrent uploads, 200 questions/minute | ⬜ | |
| P1 | Security review / penetration test of the API | ⬜ | Auth, file upload, leads feed |

## 3. Login and messaging

| | Item | Status | Notes |
|---|---|---|---|
| P0 | Firebase project on the **Blaze** plan (Spark allows ~10 SMS a day) with a budget alert | ⬜ | Billing decision |
| P0 | Firebase **App Check** (Play Integrity) so bots can't trigger SMS on our bill | ⬜ | SMS fraud is a known cost risk |
| P0 | Remove the test phone number; keep only the Play-review demo login (`REVIEW_LOGIN_*`) | ⬜ | |
| P1 | Real push: `PUSH_SENDER=fcm` + service-account JSON on the server | ⬜ | Never in git or chat |

## 4. App and Play Store

| | Item | Status | Notes |
|---|---|---|---|
| P0 | Play Console organisation account (D-U-N-S) | ⬜ | Management |
| P0 | Upload/signing key created, backed up in two places, Play App Signing on | ⬜ | Losing it means a new listing |
| P0 | Release build pointed at the production API (`API_BASE_URL=https://…`), tested on 2–3 real phones | ⬜ | Release guard already blocks http:// |
| P0 | Play **Data safety** form: data collected (phone, policies, documents), shared with processors (OpenAI, Google), encryption, deletion | ⬜ | Must match the privacy page |
| P0 | **Account deletion web link** (Play requires one outside the app) | ⬜ | In-app deletion exists |
| P0 | Store listing: screenshots, description, content rating, target audience 18+ | ⬜ | `docs/screenshots/v2` |
| P1 | Native Hindi review of app strings | ⬜ | |

## 5. Legal and compliance

| | Item | Status | Notes |
|---|---|---|---|
| P0 | IRDAI broker licence number on the privacy page and in the app | ⬜ | Placeholder in `privacy.html` |
| P0 | Lawyer review of privacy policy and terms (DPDP Act 2023; IRDAI rules for intermediaries) | ⬜ | Lists OpenAI and Google/Firebase as processors |
| P0 | Data processing agreements accepted with OpenAI and Google | ⬜ | |
| P0 | Grievance officer name and contact in the app | 🟡 | Screen exists; needs the real person |
| P1 | Lead handling: sales team follows the contact-consent rules (no contact without opt-in; withdrawals respected within a day) | 🟡 | LMS enforces it every 15 minutes |

## 6. Operations

| | Item | Status | Notes |
|---|---|---|---|
| P0 | Runbook: AI provider down, database down, SMS failing, key leaked (rotate) | ⬜ | |
| P1 | Weekly review of failed documents and low-confidence answers from logs/admin | ⬜ | Feeds the accuracy test set |
| P1 | Cost dashboard: AI tokens per day (from `app.ai.usage` logs), SMS count, storage | ⬜ | |
