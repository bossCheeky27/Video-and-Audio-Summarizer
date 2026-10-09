#!/usr/bin/env bash
# Stops the Lecture Summarizer web app started with start.sh (macOS / Linux).
# Flask debug mode runs a reloader parent + a server child, so both are stopped.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT/.app.pid"

is_app() { ps -o command= -p "$1" 2>/dev/null | grep -q 'app\.py'; }

PID=""
if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE")"
  is_app "$PID" || PID=""
fi

# Fallback: find whatever is listening on the app's port, if it is our app.py
if [ -z "$PID" ] && command -v lsof >/dev/null 2>&1 && [ -x "$ROOT/.venv/bin/python" ]; then
  PORT="$(cd "$ROOT/lecture_summarizer" && "$ROOT/.venv/bin/python" -c 'import config; print(config.PORT)' 2>/dev/null || true)"
  for p in $(lsof -ti "tcp:${PORT:-5000}" -sTCP:LISTEN 2>/dev/null); do
    if is_app "$p"; then
      # Prefer the reloader parent so it can't respawn the server
      parent="$(ps -o ppid= -p "$p" | tr -d ' ')"
      if [ -n "$parent" ] && is_app "$parent"; then PID="$parent"; else PID="$p"; fi
      break
    fi
  done
fi

if [ -z "$PID" ]; then
  echo "Lecture Summarizer is not running."
  rm -f "$PID_FILE"
  exit 0
fi

echo "Stopping Lecture Summarizer (PID $PID)..."
CHILDREN="$(pgrep -P "$PID" 2>/dev/null || true)"
kill $CHILDREN "$PID" 2>/dev/null || true

for _ in $(seq 1 10); do
  alive=""
  for p in $CHILDREN $PID; do kill -0 "$p" 2>/dev/null && alive=1; done
  [ -z "$alive" ] && break
  sleep 0.5
done
[ -n "$alive" ] && kill -9 $CHILDREN "$PID" 2>/dev/null

rm -f "$PID_FILE"
echo "Done."
