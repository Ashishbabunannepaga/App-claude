# Running the demo on your phone

Login: mobile `9876543210`, OTP `246810` (needs the demo settings in `backend\.env`, see the beginner guide).

## 1. Get the latest code

```powershell
cd C:\Users\babua\Documents\App-claude
git fetch origin
git checkout main
git pull
```

## 2. Start the backend (leave it running)

```powershell
docker compose up -d
cd C:\Users\babua\Documents\App-claude\backend
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.ai_check          # optional: checks your AI key (see "Real AI" below)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional sample policies (backend running): `python ..\tools\demo\make_pdfs.py ..\demo_pdfs` then `python ..\tools\demo\seed.py ..\demo_pdfs`.

## 3. Connect the phone over Wi-Fi (once per session)

On the phone (I2221): Settings > Developer options > **Wireless debugging** on. Then on the PC:

```powershell
$adb = "C:\Users\babua\AppData\Local\Android\sdk\platform-tools\adb.exe"
& $adb pair PHONE_IP:PAIRING_PORT       # once; type the 6-digit code ("Pair device with pairing code")
& $adb connect PHONE_IP:CONNECT_PORT    # "IP address & Port" on the Wireless debugging screen
& $adb devices                          # the phone must say "device"
```

Replace `PHONE_IP:...` with the numbers the phone shows. If `adb devices` already lists the phone (a long
`adb-...._adb-tls-connect._tcp` name), skip this step.

In Android Studio you can do the same: the device drop-down > **Pair Devices Using Wi-Fi**.

## 4. Run the app

```powershell
.\tools\demo\start-demo.ps1
```

It finds the phone (an open emulator is ignored), forwards port 8000 so the phone reaches the backend,
and runs the app. The first build takes 3 to 5 minutes. If the script is blocked, run once:
`Set-ExecutionPolicy -Scope Process Bypass`.

By hand instead (copy the phone's name from `adb devices`):

```powershell
$phone = "adb-XXXX._adb-tls-connect._tcp"
& $adb -s $phone reverse tcp:8000 tcp:8000
cd C:\Users\babua\Documents\App-claude\mobile
flutter run -d $phone --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Real AI (Gemini)

1. Create a key at https://aistudio.google.com/apikey (your own Google account).
2. In `backend\.env` set:
   ```
   AI_PROVIDER=gemini
   EMBEDDING_PROVIDER=gemini
   GEMINI_API_KEY=your-key-here
   ```
3. Restart the backend, then run `python -m app.scripts.ai_check`. Both lines should say `[OK]`.
4. Policies uploaded before the switch keep their old (mock) search index: run
   `python -m app.scripts.reembed` once, or re-upload them.

Never paste the key into chat, code or Git. `.env` is ignored by Git.

## Reset the welcome screens

```powershell
& $adb -s $phone shell pm clear com.insureiq.insureiq
```
