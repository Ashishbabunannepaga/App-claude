@echo off
cd /d "%~dp0"
echo === Mail Sorter setup ===
where py >nul 2>nul || (echo Python is not installed. Install Python 3.12 from https://www.python.org/downloads/ and tick "Add python.exe to PATH". & pause & exit /b 1)
if not exist .venv py -3 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 (echo Setup FAILED - see the messages above. & pause & exit /b 1)
if not exist api-key.txt (
  echo # Paste your OpenAI API key on the line below this one, then save.> api-key.txt
  echo # Keep this file private - never email it or put it on the shared drive.>> api-key.txt
)
echo.
echo Setup done. Next: edit config.yaml (paths), then run 2-trial-run.bat
pause
