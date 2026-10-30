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
uv venv "$ROOT/.local/webshop-venv" --python 3.11 --allow-existing
uv pip install --python "$ROOT/.local/webshop-venv/bin/python" --no-deps -r "$ROOT/configs/webshop-requirements.lock.txt"
"$ROOT/.local/webshop-venv/bin/python" "$ROOT/scripts/download_webshop_data.py"
if [[ -z "${JAVA_HOME:-}" && -d /opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home ]]; then
  export JAVA_HOME=/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home
fi
"$ROOT/.local/webshop-venv/bin/python" "$ROOT/scripts/build_webshop_index.py"
cd "$TARGET/search_engine"
"$ROOT/.local/webshop-venv/bin/python" -m pyserini.index.lucene \
  --collection JsonCollection --input resources --index indexes \
  --generator DefaultLuceneDocumentGenerator --threads 1 \
  --storePositions --storeDocvectors --storeRaw
printf '%s\n' '完整 WebShop 数据及索引已准备。使用 scripts/start_webshop.py 启动本机服务。'
