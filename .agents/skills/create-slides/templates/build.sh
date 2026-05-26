#!/usr/bin/env bash
# create-slides build helper
#
# Usage:
#   bash .agents/skills/create-slides/templates/build.sh <target>
#
# Where <target> is a path like `workshops/foundry-models-e2e`
# (relative to repo root) or `models/<slug>`. The script builds
# index.html, index.pdf, and index.pptx in <target>/slides/.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <target>" >&2
  echo "  e.g. $0 workshops/foundry-models-e2e" >&2
  exit 2
fi

TARGET="$1"
SRC="$TARGET/slides/index.md"

if [[ ! -f "$SRC" ]]; then
  echo "error: $SRC not found" >&2
  echo "  scaffold one from .agents/skills/create-slides/templates/index.md first" >&2
  exit 1
fi

if ! command -v marp >/dev/null 2>&1; then
  echo "error: marp CLI not found. install with: npm i -g @marp-team/marp-cli" >&2
  exit 1
fi

export CHROME_PATH="${CHROME_PATH:-/usr/bin/chromium}"

echo "→ building HTML"
marp "$SRC" -o "$TARGET/slides/index.html"

echo "→ building PDF"
marp "$SRC" --pdf  -o "$TARGET/slides/index.pdf"

echo "→ building PPTX"
marp "$SRC" --pptx -o "$TARGET/slides/index.pptx"

echo
echo "outputs:"
ls -la "$TARGET/slides/"index.{html,pdf,pptx}
