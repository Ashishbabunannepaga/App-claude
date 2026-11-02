@echo off
cd /d "%~dp0"
echo === FULL RUN: the whole mailbox ===
echo This can take many hours. Keep Outlook open and stop the PC from sleeping.
echo You can close this window at any time - running it again continues where it stopped.
echo.
.venv\Scripts\python -m mailsorter all
pause
