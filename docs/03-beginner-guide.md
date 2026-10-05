# Beginner's guide — running, testing and changing InsureIQ

Written for someone new to mobile development. Read it top to bottom once; afterwards use it as a reference.

---

## 1. The big picture (what are all these pieces?)

```
 Your phone                           A server (your computer while developing, the cloud later)
┌──────────────────┐   internet    ┌─────────────────────────────────────────────────────────────┐
│  Mobile app      │ ───────────►  │  Backend API (Python/FastAPI)                               │
│  (Flutter/Dart)  │  HTTPS + JSON │   ├─ Database (PostgreSQL) – users, policies, clauses        │
│  screens, buttons│ ◄───────────  │   ├─ File storage – uploaded policy PDFs                     │
└──────────────────┘               │   ├─ Background worker – reads PDFs (OCR), extracts details  │
                                   │   └─ AI gateway – Claude / OpenAI / Gemini / our own models  │
                                   └─────────────────────────────────────────────────────────────┘
```

- **The app** (`mobile/`) only shows screens and talks to the backend. It never holds secrets or policy files.
- **The backend** (`backend/`) does the real work: login, storing documents, reading them, AI answers, reminders.
- **One Flutter codebase** produces **both** the Android app and the iPhone app.

## 2. What to install on your computer

| Tool | Why | Where |
|------|-----|-------|
| **Git** | Downloads the code and tracks changes | git-scm.com |
| **VS Code** | Code editor (install the *Flutter* and *Python* extensions) | code.visualstudio.com |
| **Flutter SDK** | Builds the mobile app | docs.flutter.dev/get-started/install |
| **Android Studio** | Gives you the Android SDK and the **emulator** (a virtual phone on your screen) | developer.android.com/studio |
| **Docker Desktop** | Runs the database (PostgreSQL) and Redis with one command | docker.com |
| **Python 3.11** | Runs the backend | python.org |
| **Xcode** (Mac only) | Needed only to build/run the iPhone app | Mac App Store |

After installing Flutter and Android Studio, open a terminal and run:

```bash
flutter doctor
```

It lists anything missing with instructions. Keep going until Android toolchain shows ✓
(it will ask you to run `flutter doctor --android-licenses` and press `y`).

> **Do you need to "connect Android Studio" to Claude?** No. Claude works in the cloud on the code in GitHub.
> You use Android Studio on *your* computer to run the app. The two meet through **GitHub**: Claude pushes code,
> you `git pull` it and run it.

## 3. Get the code

```bash
git clone https://github.com/Ashishbabunannepaga/App-claude.git
cd App-claude
git checkout claude/insurance-mobile-app-yzzj6c
```

Later, to get Claude's newest changes: `git pull`.

## 4. Start the backend (demo mode — no API keys needed)

```bash
docker compose up -d                 # starts PostgreSQL + Redis in the background
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      Mac/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                 # Windows: copy .env.example .env
alembic upgrade head                 # creates the database tables
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs — this page lists every API the app uses, and you can try them.
Login codes (OTP) are printed in this terminal in demo mode.

Optional demo data (the same account as the screenshots): see `tools/demo/README.md`.

## 5. Run the app

### On the Android emulator (easiest)
1. Android Studio → *More actions* → **Virtual Device Manager** → *Create device* → Pixel 8 → Next → Finish → ▶.
2. In a new terminal:
   ```bash
   cd mobile
   flutter pub get
   flutter run
   ```
   The emulator reaches your computer's backend at `10.0.2.2:8000` automatically.

### On your own Android phone
1. Phone: *Settings → About phone →* tap **Build number** 7 times (this unlocks Developer options).
2. *Settings → Developer options →* turn on **USB debugging**. Connect the phone with a USB cable and allow the prompt.
3. Find your computer's Wi-Fi IP address (Windows: `ipconfig`, Mac: *System Settings → Wi-Fi → Details*), e.g. `192.168.1.20`.
   Phone and computer must be on the same Wi-Fi.
4. ```bash
   flutter devices                     # your phone should be listed
   flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8000/api/v1
   ```

**Hot reload:** while `flutter run` is running, edit a screen file, save, and press `r` in the terminal —
the change appears on the phone in about a second without losing your place.

### Without installing anything: download the APK from GitHub
GitHub → repository → **Actions** → *Android APK* → **Run workflow** → enter your backend URL → wait ~10 min →
open the run → download **insureiq-apk** → copy the `.apk` to an Android phone → open it
(allow "install unknown apps"). This needs a backend reachable from the internet (see §9).

### iPhone
Requires a Mac with Xcode: `cd mobile && open ios/Runner.xcworkspace`, choose your Apple ID under
*Signing & Capabilities*, plug in the iPhone, press ▶. For testers without a cable, use **TestFlight**
(needs the Apple Developer account from Week 0 of the roadmap).

## 6. How the code is organised — "where do I change X?"

| I want to change… | Look in |
|---|---|
| Colours, fonts, spacing | `mobile/lib/app/theme/` |
| Which screen opens for which link | `mobile/lib/app/router.dart` |
| The home screen | `mobile/lib/features/home/home_screen.dart` |
| Policy screens (add, verify, detail, health, nominees, clauses) | `mobile/lib/features/policy/presentation/` |
| Ask-AI chat | `mobile/lib/features/assistant/ask_screen.dart` |
| Text of claim guides | `mobile/lib/features/policy/presentation/claim_guide.dart` |
| API endpoints | `backend/app/api/v1/` |
| Business rules (insights, health check, comparison) | `backend/app/services/` |
| How documents are read (OCR, extraction, clauses) | `backend/app/processing/` |
| AI prompts and providers | `backend/app/ai/` |
| Database tables | `backend/app/models/entities.py` + a migration in `backend/alembic/versions/` |

Inside `mobile/lib/features/<feature>/`: `data/` = talking to the backend, `presentation/` = screens.

## 7. The daily loop (how professionals work)

```bash
git pull                                  # 1. get the latest code
# 2. make one small change
cd mobile && flutter analyze && flutter test        # 3. check the app
cd ../backend && pytest -q && ruff check .          # 4. check the backend
git add -A && git commit -m "Explain what changed"  # 5. save a checkpoint
git push                                  # 6. share it — GitHub Actions re-runs every check automatically
```

If a check fails, read the **first** error message; it usually names the file and line.

## 8. Glossary

| Word | Meaning |
|---|---|
| **API** | The set of URLs the app calls on the backend (e.g. `POST /api/v1/policies/{id}/ask`). |
| **JSON** | The text format the app and backend exchange. |
| **OTP** | One-time password — the 6-digit login code sent by SMS. |
| **JWT / token** | A signed "pass" the app sends with each request to prove who you are. |
| **Migration** | A script that changes the database structure safely (`alembic upgrade head` applies them). |
| **OCR** | Reading text from a photo or scanned PDF. |
| **RAG** | Retrieval-augmented generation: find the relevant parts of *your* document first, then let the AI answer only from them. |
| **Embedding** | A list of numbers representing the meaning of a text, used to find relevant passages. |
| **Clause** | One rule from the policy wording (a benefit, exclusion, waiting period…). |
| **Emulator** | A virtual Android phone on your computer. |
| **APK / AAB** | Android app files. APK = install directly; AAB = what you upload to the Play Store. |
| **CI** | Continuous integration: GitHub automatically runs all tests on every push. |
| **Hot reload** | Instantly applying code changes to the running app. |

## 9. Going live (summary)

1. Host the backend (e.g. AWS Mumbai region or Render/Railway for the beta) with a real database and storage bucket.
2. Set the production settings listed in the README (*Needs your accounts / keys before launch*). The server refuses
   to start in production while any demo-only setting is still on — that is deliberate.
3. Build the store versions: `flutter build appbundle` (Android) and archive in Xcode (iOS).
4. Fill in the store listings, privacy forms and screenshots (`tools/demo/` can regenerate screenshots).

## 10. Working with Claude effectively

- Ask for **one feature or fix at a time**, and say who it's for and what "done" looks like.
- When something breaks, paste the **exact error text** or a screenshot, plus what you did just before.
- Ask for tests with every change ("…and add tests") — they protect what already works.
- Ask *"explain this file to me like I'm new"* for any file you want to understand.
- Review the screenshots or run the app after each change; small, frequent feedback beats big batches.
