@echo off
title Stop Lecture Summarizer
REM Stops the Lecture Summarizer web app started with start.bat (Windows).
if not defined PYTHON set "PYTHON=python"

cd /d "%~dp0lecture_summarizer"
REM Separate variable: setting PORT here would override what config.py reads from .env
set "APP_PORT=5000"
for /f %%P in ('%PYTHON% -c "import config; print(config.PORT)" 2^>nul') do set "APP_PORT=%%P"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lecture_summarizer\stop_app.ps1" -Port %APP_PORT%
timeout /t 4
