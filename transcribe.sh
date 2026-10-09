#!/usr/bin/env bash
# Batch-transcribes every .mp4/.m4a/.mp3/.wav next to this script into a .txt (macOS / Linux).
# Successfully transcribed source files are moved into transcribed_lectures/.
# Windows equivalent: transcribe.bat
set -uo pipefail

# ====== CONFIG ======
WHISPER_MODEL="tiny"
WHISPER_LANG="en"     # empty = auto-detect
# =====================

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOVE_DIR="$ROOT/transcribed_lectures"
OUTPUT_DIR="$ROOT"
PY="$ROOT/.venv/bin/python"

cd "$ROOT"

if [ ! -x "$PY" ] || ! "$PY" -c 'import whisper' >/dev/null 2>&1; then
  echo "ERROR: Whisper not available. Run: bash setup.sh" >&2
  exit 1
fi

mkdir -p "$MOVE_DIR"

shopt -s nullglob nocaseglob
files=( *.mp4 *.m4a *.mp3 *.wav )
shopt -u nocaseglob

if [ ${#files[@]} -eq 0 ]; then
  echo "No .mp4, .m4a, .mp3 or .wav files found in: $ROOT"
  exit 0
fi

lang_args=()
[ -n "$WHISPER_LANG" ] && lang_args=(--language "$WHISPER_LANG")

for f in "${files[@]}"; do
  echo
  echo "============================================"
  echo "Transcribing: $f"
  echo "============================================"

  out_txt="$OUTPUT_DIR/${f%.*}.txt"
  rm -f "$out_txt"

  "$PY" -m whisper "$f" --model "$WHISPER_MODEL" ${lang_args[@]+"${lang_args[@]}"} \
    --task transcribe --output_format txt --output_dir "$OUTPUT_DIR"

  if [ ! -s "$out_txt" ]; then
    echo "ERROR: Transcript missing or empty for $f - skipping move."
    continue
  fi

  echo "Transcript created: $out_txt ($(wc -c < "$out_txt" | tr -d ' ') bytes)"
  echo "Moving source file to: $MOVE_DIR"
  if mv -f "$f" "$MOVE_DIR/"; then echo "Done."; else echo "ERROR: Failed to move $f"; fi
done

echo
echo "Finished."
