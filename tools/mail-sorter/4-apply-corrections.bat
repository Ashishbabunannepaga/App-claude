@echo off
cd /d "%~dp0"
echo === Apply category corrections typed into "Attachments Index.xlsx" ===
echo Close the Excel file first.
.venv\Scripts\python -m mailsorter import-review
.venv\Scripts\python -m mailsorter organize
.venv\Scripts\python -m mailsorter report
pause
