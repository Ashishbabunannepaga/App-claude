@echo off
cd /d "%~dp0"
echo === What would the AI step cost? (nothing is sent - this only counts) ===
.venv\Scripts\python -m mailsorter estimate
pause
