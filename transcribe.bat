@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ====== CONFIG ======
set "WHISPER_MODEL=tiny"
set "WHISPER_LANG=en"
set "MOVE_DIR=%~dp0transcribed_lectures"
set "OUTPUT_DIR=%~dp0"
REM =====================

REM Run from the script's directory
cd /d "%~dp0"

REM Verify whisper is installed for this python
python -c "import whisper" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Whisper not available for this Python.
  echo Run: python -m pip install -U openai-whisper
  pause
  exit /b 1
)

if not exist "%MOVE_DIR%" mkdir "%MOVE_DIR%" >nul 2>nul

set "FOUND_ANY=0"

for %%F in (*.mp4 *.m4a *.mp3 *.wav) do (
  set "FOUND_ANY=1"
  echo.
  echo ============================================
  echo Transcribing: %%F
  echo ============================================

  set "BASENAME=%%~nF"
  set "OUTTXT=%OUTPUT_DIR%!BASENAME!.txt"

  if exist "!OUTTXT!" del /f /q "!OUTTXT!" >nul 2>nul

  REM Transcribe -> TXT
  if "%WHISPER_LANG%"=="" (
    python -m whisper "%%F" --model "%WHISPER_MODEL%" --task transcribe --output_format txt --output_dir %OUTPUT_DIR%
  ) else (
    python -m whisper "%%F" --model "%WHISPER_MODEL%" --language "%WHISPER_LANG%" --task transcribe --output_format txt --output_dir %OUTPUT_DIR%
  )

  REM Success check: file exists and not empty
  if not exist "!OUTTXT!" (
    echo ERROR: Transcript not created for %%F
    echo Skipping move.
    goto :continue_file
  )

  for %%S in ("!OUTTXT!") do set "SIZE=%%~zS"
  if "!SIZE!"=="0" (
    echo ERROR: Transcript file is empty for %%F
    echo Skipping move.
    goto :continue_file
  )

  echo Transcript created: "!OUTTXT!"  (bytes: !SIZE!)
  echo Moving source file to: "%MOVE_DIR%"
  move /y "%%F" "%MOVE_DIR%" >nul
  if errorlevel 1 (
    echo ERROR: Failed to move %%F
  ) else (
    echo Done.
  )

  :continue_file
)

if "%FOUND_ANY%"=="0" (
  echo No .mp4, .m4a, .mp3 or .wav files found in: "%~dp0"
)

echo.
echo Finished.
pause
endlocal