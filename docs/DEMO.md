# Showing two demos from one phone

Both demos use the **same backend**, and they install side by side, so people can open either one and compare.

| Demo | Look | Branch | App on the phone |
|---|---|---|---|
| **v1** | CoverSure-style (navy, list screens) | `claude/insurance-mobile-app-yzzj6c` | "CapitUp" |
| **v2** | Modern illustrated (teal + gold) | `claude/capitup-demo-v1-v2` (this branch) | "CapitUp v2" |

Login for both: mobile `9876543210`, OTP `246810` (needs the demo settings in `backend\.env`, see the beginner guide).

## 1. Get both versions on your PC (once)

```powershell
cd C:\Users\babua\Documents\App-claude
git fetch origin
git checkout claude/capitup-demo-v1-v2
git pull

# A second folder holding the v1 branch, next to the first:
git worktree add ..\App-claude-v1 claude/insurance-mobile-app-yzzj6c
```

If Git says the branch doesn't exist locally, use:
`git worktree add ..\App-claude-v1 -b claude/insurance-mobile-app-yzzj6c origin/claude/insurance-mobile-app-yzzj6c`

## 2. Start the backend (leave it running)

```powershell
docker compose up -d
cd C:\Users\babua\Documents\App-claude\backend
.venv\Scripts\activate
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional sample policies (backend running): `python ..\tools\demo\make_pdfs.py ..\demo_pdfs` then `python ..\tools\demo\seed.py ..\demo_pdfs`.

## 3. Connect the phone over Wi-Fi (wireless debugging)

**On the PC**, find your Wi-Fi address (the phone and PC must be on the same Wi-Fi):

```powershell
ipconfig
```

Look under **Wireless LAN adapter Wi-Fi** for **IPv4 Address**, e.g. `192.168.1.20`. Or in one line:

```powershell
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like '*Wi-Fi*' -and $_.IPAddress -notlike '169.*' } | Select-Object -First 1).IPAddress
```

**On the phone (I2221):** Settings > Developer options > turn on **Wireless debugging**. The screen shows:

- **IP address & Port** (e.g. `192.168.1.50:41234`): used to connect.
- **Pair device with pairing code**: shows a *different* IP:port and a 6-digit code: used once to pair.

**Back on the PC:**

```powershell
$adb = "C:\Users\babua\AppData\Local\Android\sdk\platform-tools\adb.exe"

# Pair once (use the pairing address and type the 6-digit code when asked):
& $adb pair 192.168.1.50:PAIRING_PORT

# Connect (use "IP address & Port" from the main Wireless debugging screen):
& $adb connect 192.168.1.50:CONNECT_PORT

& $adb devices        # the phone must say "device", not "offline"
```

Replace `192.168.1.50` with the phone's address and the ports with what the phone shows. The connect port changes each time Wireless debugging is switched off and on, and the phone's address can change after a router restart.

In Android Studio you can do the same: the device drop-down > **Pair Devices Using Wi-Fi**.

## 4. Run a demo

One command per demo (from `C:\Users\babua\Documents\App-claude`):

```powershell
.\tools\demo\start-demo.ps1 -Variant v2 -Connect 192.168.1.50:CONNECT_PORT
.\tools\demo\start-demo.ps1 -Variant v1
```

Run **v2 first, press `q`, then run v1** (or the reverse). The first build of each takes 3 to 5 minutes. After that, **both apps stay installed**: open "CapitUp" (v1) or "CapitUp v2" from the phone's app list.

If the script is blocked, run once: `Set-ExecutionPolicy -Scope Process Bypass`.

### Doing it by hand instead

```powershell
$adb = "C:\Users\babua\AppData\Local\Android\sdk\platform-tools\adb.exe"
& $adb -s 192.168.1.50:CONNECT_PORT reverse tcp:8000 tcp:8000
cd C:\Users\babua\Documents\App-claude\mobile          # v2
flutter run -d 192.168.1.50:CONNECT_PORT --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

For v1, use `cd C:\Users\babua\Documents\App-claude-v1\mobile`.

### Without the USB-style port forward (use the PC's Wi-Fi address)

Run once as Administrator to let the phone reach the backend:

```powershell
New-NetFirewallRule -DisplayName "CapitUp API 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

Then run with `--dart-define=API_BASE_URL=http://192.168.1.20:8000/api/v1` (your PC's address from step 3).

## Reset the welcome screens on a demo

```powershell
& $adb -s 192.168.1.50:CONNECT_PORT shell pm clear com.insureiq.insureiq.v2   # v2
& $adb -s 192.168.1.50:CONNECT_PORT shell pm clear com.insureiq.insureiq      # v1
```

## Notes

- The side-by-side setup (a different app id and name for debug builds on this branch) could not be built in the cloud session, which has no Android SDK. It is a small Gradle change; tell me if the first build complains.
- Release builds keep the normal app id. The `.v2` suffix applies to debug builds only.
