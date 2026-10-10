# Deploy checklist: CapitUp

Date: 2026-10-10  Branch: `develop`  Go from user: **not yet** (preflight only, nothing deployed)

Status key: ✅ done and checked here · 🟡 done in code, you must finish an account step · ❌ blocker, not done

## Preflight

| Check | Result |
|---|---|
| Backend tests | ✅ 65 passed (`pytest`), lint and format clean (`ruff`) |
| App tests | ✅ 208 passed (`flutter test`), `flutter analyze` clean. Includes layout sweeps at 320–412 px and 1.0–1.6× text, and accessibility checks |
| Real-device test | 🟡 first phone run done on the Vivo I2221 (10 Oct); the fixes from it are in. One more full pass after these changes |
| Open S1/S2 bugs | ✅ none known. Fixed from the phone test: blank gap under Home tiles, "LIC" as insurer on non-LIC policies, missing start date, ₹1 sum insured accepted without a warning |
| Parity | ✅ 100/100, must-haves 7 of 7 (self-assessed against our own feature list) |
| Rebrand sweep | ✅ clean (`sweep.py` exit 0) |
| Store listing lint | ❌ not written yet (`/replica-launch`) |
| Production build: backend | 🟡 `Dockerfile` present (gunicorn + uvicorn, non-root user); not built here (no Docker in the cloud session) |
| Production build: app | 🟡 not built here (no Android SDK in the cloud session). Run `flutter build appbundle` on your PC, see below |
| Privacy policy and terms | 🟡 served by the backend at `/privacy` and `/terms`, every processor listed. **DRAFT**: fill the [brackets] and get a lawyer's review (DPDP Act 2023) |
| Account deletion | ✅ in the app (Profile > Privacy); data purged after the grace period by the scheduled job |
| App icon, name, splash | ✅ CapitUp. 🟡 Export a 1024 px icon for the store from the trimmed logo |
| Release signing | 🟡 reads `android/key.properties`; you create the upload key (below). Without it Play rejects the bundle |
| Release guard | ✅ a production build refuses to start with an http:// API or placeholder support/grievance details |
| Production config guard | ✅ backend refuses to start in production with mock AI, hashing embeddings, console OTP, local storage, log push, in-memory rate limits, weak secrets or eager tasks |

## Decisions that are yours

1. **App id.** It is still `com.insureiq.insureiq` (the first project name). It can never change after the first Play upload. Change it now to something like `in.capitup.app`, or keep it. Tell me and I will rename it everywhere.
2. **Host** for the API, worker and database. With Indian users' financial documents, use an India region: Google Cloud Run + Cloud SQL (Mumbai), AWS (Mumbai), or Render/Railway (Singapore is the nearest they offer). The `Dockerfile` runs on all of them.
3. **Gemini tier.** On Google's free tier, prompts can be used to improve Google's products. For real users' policies, use a paid (billing-enabled) key, whose terms say inputs are not used for training, and state that in the privacy policy.

## What you do (accounts and keys; I never create accounts or touch keys)

### AI
- [ ] Create a Gemini key at https://aistudio.google.com/apikey, with billing on for production.
- [ ] Local test: put it in `backend\.env` (`AI_PROVIDER=gemini`, `EMBEDDING_PROVIDER=gemini`, `GEMINI_API_KEY=...`), then run `python -m app.scripts.ai_check`. Both lines should say `[OK]`.
- [ ] Upload 3–5 real policies (health, motor, life) and check the "Check your policy details" screen for each.

### Production services
- [ ] Postgres 16 with the `pgvector` extension, separate from dev, daily backups on.
- [ ] Redis (rate limits + Celery queue).
- [ ] Object storage: Cloudflare R2 or S3 bucket (private), keys with access to that bucket only.
- [ ] SMS: MSG91 account, DLT-registered OTP template (Indian telecom rule; takes days).
- [ ] Firebase project for push (FCM service account JSON).
- [ ] Domain, e.g. `capitup.in`, with `api.` pointing at the host.

### Environment variables on the host (names from `backend/.env.example`)
`ENV=production`, `DATABASE_URL`, `REDIS_URL`, `TASKS_EAGER=false`, `JWT_SECRET` (64 random chars), `OTP_HMAC_SECRET`, `OTP_SENDER=msg91`, `MSG91_AUTH_KEY`, `MSG91_TEMPLATE_ID`, `STORAGE_BACKEND=s3`, `S3_BUCKET`, `S3_ENDPOINT_URL` (R2), `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AI_PROVIDER=gemini`, `EMBEDDING_PROVIDER=gemini`, `GEMINI_API_KEY`, `PUSH_SENDER=fcm`, `FCM_PROJECT_ID`, `FCM_SERVICE_ACCOUNT_JSON`, `RATE_LIMIT_BACKEND=redis`, `CORS_ORIGINS=[]`. Do **not** set `REVIEW_LOGIN_*` except for a store-review account.

### Processes to run on the host
- API: the Dockerfile's default command
- Worker: `celery -A app.workers.celery_app worker -l info`
- Scheduler: `celery -A app.workers.celery_app beat -l info` (renewal reminders, account purge)
- Before each release: `alembic upgrade head`

### Android release (on your PC)
```powershell
# once: create the upload key (keep the .jks and passwords safe; losing them blocks updates)
keytool -genkey -v -keystore C:\Users\babua\capitup-upload.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
# then create mobile\android\key.properties (never commit it):
#   storeFile=C:/Users/babua/capitup-upload.jks
#   storePassword=...
#   keyAlias=upload
#   keyPassword=...
cd C:\Users\babua\Documents\App-claude\mobile
flutter build appbundle --release --dart-define=ENV=production --dart-define=API_BASE_URL=https://api.YOURDOMAIN/api/v1 --dart-define=SUPPORT_EMAIL=support@YOURDOMAIN --dart-define=GRIEVANCE_OFFICER="Name, grievance@YOURDOMAIN"
```
Upload `build\app\outputs\bundle\release\app-release.aab` to Play Console > Internal testing ($25 one-time developer account).

## Watch (after launch)
- [ ] Uptime check on `https://api.YOURDOMAIN/health`
- [ ] Error tracking (Sentry, free tier) on the API and the app; no policy text in reports
- [ ] Alert on Gemini errors (`ai_unavailable` failures in the logs) and quota
- [ ] Do the core flow on the live API from the phone: sign in, upload, check details, report, ask AI

## Not done yet (next)
- Store listing and screenshots (`/replica-launch`)
- Crash reporting in the app (Crashlytics or Sentry)
- Dark mode, Hindi UI
