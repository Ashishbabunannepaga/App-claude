# InsureIQ — AI-powered personal insurance intelligence

> Working codename. Replace the name, bundle IDs (`com.insureiq.insureiq`) and branding before store submission.

A cross-platform (Android + iOS) app that lets people keep all their insurance policies in one place, understand what they are covered for, ask questions answered **from their own policy document**, and never miss a renewal.

V1 core loop: **Add policy → Read → Understand → Ask → Track → Renew**

| | |
|---|---|
| 📐 Technical blueprint (Phase 1) | [`docs/01-technical-blueprint.md`](docs/01-technical-blueprint.md) |
| 🗓️ 12-week roadmap (Phase 2) | [`docs/02-development-roadmap.md`](docs/02-development-roadmap.md) |
| 🐍 Backend (FastAPI + PostgreSQL/pgvector) | [`backend/`](backend) |
| 📱 Mobile (Flutter, Android + iOS) | [`mobile/`](mobile) |

## What works today (first vertical slice)

```
Login (phone OTP) → Profile → Add policy → Upload PDF/photo → Text extraction / OCR
→ AI structured extraction + validation + confidence → User verifies/corrects
→ Policy detail + AI summary → Ask AI (RAG, page citations, refuses when not in document)
→ Portfolio dashboard + upcoming renewals
```

Also: manual policy entry, retry/delete documents, signed document URLs, refresh-token rotation with reuse detection, account deletion (7-day grace + purge job), claim guidance content, audit log.

### Clearly marked MOCK / TODO

| Item | Status |
|------|--------|
| `AI_PROVIDER=mock`, `EMBEDDING_PROVIDER=hashing` | **MOCK** — offline heuristics so the flow runs without API keys. Refused when `ENV=production`. Set `AI_PROVIDER=claude` (or `openai`) + key for real extraction/answers. |
| OTP SMS | Console sender (**DEV ONLY**, prints OTP to the server log). MSG91/Twilio = TODO Week 2 (needs DLT template). |
| Rate limiting | In-process; Redis-backed = TODO Week 9. |
| Push notifications / renewal reminders | TODO Week 7 (UI says "coming soon"). |
| Family members, app lock, notification settings, Gmail import, policy health | Shown as "Coming soon" — no fake flows. |
| Privacy / terms / support URLs | Placeholders in `mobile/lib/core/config/env.dart` (`--dart-define` to override). |

## Run locally

### Backend

Requirements: Python 3.11, PostgreSQL 16 with pgvector, Tesseract (for scanned docs/photos). Easiest: `docker compose up -d` (Postgres + Redis).

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp .env.example .env              # dev defaults: mock AI, local storage, console OTP
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs   — OTP codes appear in this terminal's log
```

Tests (need a database `insure_test`, override with `TEST_DATABASE_URL`):

```bash
.venv/bin/pytest -q
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```

Production-like processing uses Celery: set `TASKS_EAGER=false` and run
`celery -A app.workers.celery_app worker -l info` (+ `beat` for scheduled jobs).

### Mobile

Requirements: Flutter (stable), Android Studio / Xcode.

```bash
cd mobile
flutter pub get
flutter run                                   # Android emulator → http://10.0.2.2:8000, iOS sim → localhost
flutter run --dart-define=API_BASE_URL=https://api.staging.example.com/api/v1 --dart-define=ENV=staging
flutter analyze && flutter test
```

The app contains **no secrets** — only the public API URL.

## Architecture in one picture

```
Flutter app ──HTTPS/JWT──► FastAPI ──► PostgreSQL + pgvector
                              │
                              └─► Celery worker ─► Object storage (S3 / R2)
                                               ─► AI Gateway ─► Claude | OpenAI | (Gemini, local: future)
                                               ─► OCR (Tesseract → cloud OCR)
```

AI providers, embeddings, OCR, storage and OTP senders are all behind interfaces selected by environment variables, so vendors can be swapped without code changes.
