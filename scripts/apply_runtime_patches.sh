#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
apply_patch() {
  local checkout="$1" patch="$2"
  if git -C "$checkout" apply --reverse --check "$patch" 2>/dev/null; then
    echo "已应用：$patch"
  else
    git -C "$checkout" apply --check "$patch"
    git -C "$checkout" apply "$patch"
  fi
}
apply_patch "$ROOT/upstream/ReAct" "$ROOT/patches/react-wikipedia.patch"
apply_patch "$ROOT/upstream/Logic-LLM" "$ROOT/patches/logic-runtime.patch"
