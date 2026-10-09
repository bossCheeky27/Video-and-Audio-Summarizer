@echo off
title Lecture Summarizer
REM Starts the Lecture Summarizer web app (Windows) and opens it in the browser.
REM Keep this window open while using the app; close it or run stop.bat to stop.
if not defined PYTHON set "PYTHON=python"

cd /d "%~dp0lecture_summarizer"

REM APP_PORT, not PORT: setting PORT here would override what config.py reads from .env
set "APP_PORT="

for /f %%P in ('%PYTHON% -c "import config; print(config.PORT)"') do set "APP_PORT=%%P"
if not defined APP_PORT (
  echo ERROR: Could not start - run setup.bat first.
  pause
  exit /b 1
)
set "URL=http://localhost:%APP_PORT%"

REM If something is already listening on the port, just open the browser
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %APP_PORT% -State Listen -ErrorAction SilentlyContinue) { exit 1 }"
if errorlevel 1 (
  echo Lecture Summarizer already appears to be running. Opening %URL% ...
  start "" "%URL%"
  timeout /t 3 >nul
  exit /b 0
)

REM Open the browser once the server is listening (startup can take 30s+ while libraries load)
start "" /min powershell -NoProfile -WindowStyle Hidden -Command "for ($i=0; $i -lt 120; $i++) { if (Get-NetTCPConnection -LocalPort %APP_PORT% -State Listen -ErrorAction SilentlyContinue) { Start-Process '%URL%'; break }; Start-Sleep 1 }"

echo Starting Lecture Summarizer on %URL% - keep this window open while using the app.
echo Close this window or run stop.bat to shut it down.
echo.
%PYTHON% app.py

echo.
echo Lecture Summarizer has stopped.
pause
