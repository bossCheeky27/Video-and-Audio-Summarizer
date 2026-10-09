#!/usr/bin/env bash
# Installs everything needed for this repo on macOS / Linux.
# Packages go into a virtual environment at ./.venv (system pip installs are blocked
# on recent Ubuntu/Debian and Homebrew Python). Windows users: run setup.bat instead.
#
# Usage: bash setup.sh
#   USE_CUDA=1 bash setup.sh   # Linux: install the CUDA build of PyTorch instead of CPU-only
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
APP_DIR="$ROOT/lecture_summarizer"
OS="$(uname -s)"

step() { printf '\n============================================\n%s\n============================================\n' "$1"; }
warn() { printf 'WARNING: %s\n' "$1" >&2; }
fail() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }

# Run as root directly, otherwise through sudo (if present)
as_root() {
  if [ "$(id -u)" -eq 0 ]; then "$@"
  elif command -v sudo >/dev/null 2>&1; then sudo "$@"
  else return 1
  fi
}

step "[1/5] Python"
PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 \
     && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
    PYTHON="$candidate"; break
  fi
done
if [ -z "$PYTHON" ]; then
  if [ "$OS" = "Darwin" ]; then
    fail "Python 3.9+ not found. Install it with: brew install python  (or from https://www.python.org/downloads/)"
  else
    fail "Python 3.9+ not found. Install it with your package manager, e.g.: sudo apt install python3 python3-venv"
  fi
fi
echo "Using $("$PYTHON" -c 'import sys; print(sys.executable, sys.version.split()[0])')"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Creating virtual environment in .venv ..."
  if ! "$PYTHON" -m venv "$VENV"; then
    rm -rf "$VENV"
    fail "Could not create a virtual environment. On Debian/Ubuntu install it with: sudo apt install python3-venv"
  fi
else
  echo "Virtual environment .venv already exists."
fi
PY="$VENV/bin/python"
"$PY" -m pip install --upgrade pip --quiet

step "[2/5] Web app packages (lecture_summarizer)"
"$PY" -m pip install -r "$APP_DIR/requirements.txt"

step "[3/5] openai-whisper (used by transcribe.sh) - first install downloads PyTorch"
if [ "$OS" = "Linux" ] && [ "${USE_CUDA:-0}" != "1" ] && ! "$PY" -c 'import torch' 2>/dev/null; then
  # Default Linux wheels bundle CUDA (several GB); the CPU build is ~200MB and is all Whisper needs here
  echo "Installing CPU-only PyTorch (set USE_CUDA=1 to get the CUDA build instead)..."
  "$PY" -m pip install torch --index-url https://download.pytorch.org/whl/cpu
fi
"$PY" -m pip install -U openai-whisper

step "[4/5] FFmpeg"
if command -v ffmpeg >/dev/null 2>&1; then
  echo "FFmpeg already installed."
elif [ "$OS" = "Darwin" ]; then
  if command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  else
    warn "FFmpeg not found and Homebrew is not installed. Install Homebrew from https://brew.sh then run: brew install ffmpeg"
  fi
else
  echo "FFmpeg not found - installing with your package manager (may ask for your password)..."
  if   command -v apt-get >/dev/null 2>&1; then as_root apt-get update && as_root apt-get install -y ffmpeg
  elif command -v dnf     >/dev/null 2>&1; then as_root dnf install -y ffmpeg
  elif command -v pacman  >/dev/null 2>&1; then as_root pacman -S --noconfirm ffmpeg
  elif command -v zypper  >/dev/null 2>&1; then as_root zypper install -y ffmpeg
  else false
  fi || warn "Could not install FFmpeg automatically. Install it with your package manager (package name: ffmpeg)."
fi

step "[5/5] Gemini API key (.env)"
if [ -f "$APP_DIR/.env" ]; then
  echo "lecture_summarizer/.env already exists."
else
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "Created lecture_summarizer/.env from .env.example."
  echo "ACTION NEEDED: open it and set GEMINI_API_KEY (get one at https://aistudio.google.com/app/apikey)."
fi

chmod +x "$ROOT"/*.sh 2>/dev/null || true

echo
echo "Verifying imports..."
"$PY" -W ignore -c "import flask, faster_whisper, google.generativeai, pdfplumber, PIL, dotenv, numpy, whisper; print('All packages OK.')"
command -v ffmpeg >/dev/null 2>&1 || warn "FFmpeg is still missing - transcription will not work until it is installed."

echo
echo "Setup complete."
echo " - Web app:      ./start.sh   (stop with Ctrl+C or ./stop.sh)"
echo " - Batch script: put .mp4/.m4a/.mp3/.wav files next to transcribe.sh and run ./transcribe.sh"
