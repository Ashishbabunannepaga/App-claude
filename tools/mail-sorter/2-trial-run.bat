@echo off
cd /d "%~dp0"
echo === TRIAL RUN: emails from the last 30 days ===
echo Outlook must be open. Your emails are only read - nothing is moved or deleted.
echo.
.venv\Scripts\python -m mailsorter all --days 30
echo.
echo Open "Dashboard.html" and "Attachments Index.xlsx" in the output folder to check the result.
pause
