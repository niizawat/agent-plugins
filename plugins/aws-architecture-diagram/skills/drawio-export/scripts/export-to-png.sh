#!/usr/bin/env bash
# export-to-png.sh — Convert a .drawio file to PNG using the drawio CLI
#
# Usage:
#   export-to-png.sh <input.drawio> [output.png]
#
# If output path is omitted, the PNG is written next to the input file.
# Requires: drawio CLI (brew install drawio on macOS)

set -euo pipefail

INPUT="${1:?Error: input .drawio file required. Usage: export-to-png.sh <input.drawio> [output.png]}"

if [[ ! -f "$INPUT" ]]; then
  echo "Error: file not found: $INPUT" >&2
  exit 1
fi

OUTPUT="${2:-${INPUT%.drawio}.png}"

# Locate drawio executable
DRAWIO_CMD=""
for candidate in drawio /opt/homebrew/bin/drawio /usr/local/bin/drawio; do
  if command -v "$candidate" &>/dev/null; then
    DRAWIO_CMD="$candidate"
    break
  fi
done

if [[ -z "$DRAWIO_CMD" ]]; then
  echo "Error: drawio CLI not found. Install with: brew install drawio" >&2
  echo "SKIP_PNG_REVIEW=true"
  exit 2
fi

"$DRAWIO_CMD" \
  --export \
  --format png \
  --scale 2 \
  --border 20 \
  --output "$OUTPUT" \
  "$INPUT"

echo "Exported: $OUTPUT"
