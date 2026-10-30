#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$ROOT/.local/WebShop"
COMMIT="64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"

if [[ ! -d "$TARGET/.git" ]]; then
  mkdir -p "$ROOT/.local"
  git clone https://github.com/princeton-nlp/WebShop.git "$TARGET"
fi
git -C "$TARGET" fetch --depth 1 origin "$COMMIT"
git -C "$TARGET" checkout --detach "$COMMIT"
printf 'WebShop source: %s\nCommit: %s\n' "$TARGET" "$COMMIT"
printf '%s\n' 'The official setup downloads product data and builds the local search index.'
printf '%s\n' 'Run: cd .local/WebShop && ./setup_arm.sh -d small (Apple Silicon) or ./setup.sh -d small.'
