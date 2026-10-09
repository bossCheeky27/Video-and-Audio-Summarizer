@echo off
setlocal EnableExtensions
title Lecture Transcripts - Setup

REM Uses "python" on PATH. To use a specific install: set PYTHON=C:\Path\to\python.exe
REM (start.bat, stop.bat and transcribe.bat use the same "python" on PATH)
if not defined PYTHON set "PYTHON=python"

cd /d "%~dp0"

"%PYTHON%" --version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python not found. Install Python 3 from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" during install, then run this again.
  pause
  exit /b 1
)
"%PYTHON%" -c "import sys; print('Using Python: ' + sys.executable)"
echo.

echo ============================================
echo [1/4] Web app packages (lecture_summarizer)
echo ============================================
"%PYTHON%" -m pip install -r "lecture_summarizer\requirements.txt"
if errorlevel 1 goto :pip_failed

echo.
echo ============================================
echo [2/4] openai-whisper (used by transcribe.bat)
echo       First install downloads PyTorch - this can take a while.
echo ============================================
"%PYTHON%" -m pip install -U openai-whisper
if errorlevel 1 goto :pip_failed

echo.
echo ============================================
echo [3/4] FFmpeg
echo ============================================
where ffmpeg >nul 2>nul
if not errorlevel 1 (
  echo FFmpeg already installed.
  goto :ffmpeg_done
)
where winget >nul 2>nul
if errorlevel 1 (
  echo WARNING: FFmpeg not found and winget is unavailable.
  echo Install FFmpeg manually from https://ffmpeg.org/download.html and add it to PATH.
  goto :ffmpeg_done
)
echo FFmpeg not found - installing with winget...
winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
  echo WARNING: FFmpeg install failed. Install it manually from https://ffmpeg.org/download.html
) else (
  echo FFmpeg installed. Open a new terminal window so it is picked up on PATH.
)
:ffmpeg_done

echo.
echo ============================================
echo [4/4] Gemini API key (.env)
echo ============================================
if exist "lecture_summarizer\.env" (
  echo lecture_summarizer\.env already exists.
) else (
  copy /y "lecture_summarizer\.env.example" "lecture_summarizer\.env" >nul
  echo Created lecture_summarizer\.env from .env.example.
  echo ACTION NEEDED: open it and set GEMINI_API_KEY ^(get one at https://aistudio.google.com/app/apikey^).
)

echo.
echo Verifying imports...
"%PYTHON%" -W ignore -c "import flask, faster_whisper, google.generativeai, pdfplumber, PIL, dotenv, numpy, whisper; print('All packages OK.')"
if errorlevel 1 goto :pip_failed

echo.
echo Setup complete.
echo  - Web app:      run start.bat (stop it with stop.bat)
echo  - Batch script: drop .mp4/.m4a/.mp3/.wav files next to transcribe.bat and run it
pause
exit /b 0

:pip_failed
echo.
echo ERROR: Package installation failed - see the messages above.
pause
exit /b 1
