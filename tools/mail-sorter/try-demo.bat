@echo off
cd /d "%~dp0"
echo === DEMO with a fake mailbox (no Outlook needed, nothing real is touched) ===
if exist demo rmdir /s /q demo
.venv\Scripts\python -m mailsorter demo
.venv\Scripts\python -m mailsorter --demo classify
.venv\Scripts\python -m mailsorter --demo organize
.venv\Scripts\python -m mailsorter --demo report
start "" "demo\output\Dashboard.html"
pause
