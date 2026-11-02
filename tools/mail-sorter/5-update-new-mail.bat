@echo off
cd /d "%~dp0"
rem Picks up attachments from the last 14 days. Safe to schedule weekly in Windows Task Scheduler.
.venv\Scripts\python -m mailsorter all --days 14
