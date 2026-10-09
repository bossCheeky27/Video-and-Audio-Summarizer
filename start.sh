#!/usr/bin/env bash
# Starts the Lecture Summarizer web app (macOS / Linux) and opens it in the browser.
# Runs in the foreground so you can watch progress; stop with Ctrl+C or ./stop.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT/lecture_summarizer"
PY="$ROOT/.venv/bin/python"
PID_FILE="$ROOT/.app.pid"

[ -x "$PY" ] || { echo "ERROR: .venv not found - run: bash setup.sh" >&2; exit 1; }
cd "$APP_DIR"

PORT="$("$PY" -c 'import config; print(config.PORT)')"
URL="http://localhost:$PORT"

port_open() { "$PY" -c "import socket,sys; s=socket.socket(); s.settimeout(0.5); sys.exit(s.connect_ex(('127.0.0.1', $PORT)))" 2>/dev/null; }

open_browser() {
  if   command -v open     >/dev/null 2>&1 && [ "$(uname -s)" = "Darwin" ]; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true
  else echo "Open $URL in your browser."
  fi
}

if port_open; then
  echo "Something is already running on port $PORT - opening $URL"
  open_browser
  exit 0
fi

# Open the browser once the server is listening (startup can take 30s+ while libraries load)
(
  for _ in $(seq 1 120); do
    if port_open; then open_browser; exit 0; fi
    sleep 1
  done
) &

echo "Starting Lecture Summarizer on $URL - press Ctrl+C (or run ./stop.sh) to stop."
echo
echo $$ > "$PID_FILE"
# exec keeps the same PID, so stop.sh can find the server through the PID file
exec "$PY" app.py
