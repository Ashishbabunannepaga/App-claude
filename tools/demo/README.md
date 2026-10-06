# Demo data & screenshots

Regenerates the screenshots in `docs/screenshots/` (also a starting point for store screenshots).

1. Start the backend with demo settings (mock AI, fixed review login):
   ```bash
   cd backend
   export AI_PROVIDER=mock EMBEDDING_PROVIDER=hashing TASKS_EAGER=true \
     CORS_ORIGINS='["http://localhost:8080"]' \
     REVIEW_LOGIN_IDENTIFIER=+919876543210 REVIEW_LOGIN_CODE=246810 OTP_RESEND_COOLDOWN_SECONDS=0 \
     ADMIN_API_TOKEN=demo-admin-token-0123456789abcdef0123
   .venv/bin/alembic upgrade head && .venv/bin/uvicorn app.main:app --port 8000
   ```
2. Create sample policy PDFs and seed the demo account:
   ```bash
   .venv/bin/python ../tools/demo/make_pdfs.py /tmp/demo
   .venv/bin/python ../tools/demo/seed.py /tmp/demo > /tmp/demo/ids.txt
   ```
4. Build and serve the Flutter web preview:
   ```bash
   cd mobile
   flutter build web --no-web-resources-cdn --dart-define=API_BASE_URL=http://localhost:8000/api/v1
   (cd build/web && python3 -m http.server 8080)
   ```
5. Capture (needs Node + Playwright):
   ```bash
   node tools/demo/shots.js /tmp/shots /tmp/demo/ids.txt
   ```

The sample PDFs are fictional and contain no real personal data.
