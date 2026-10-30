#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/upstream/Logic-LLM/models/symbolic_solvers/Prover9"
BUILD="$ROOT/.local/Prover9"
mkdir -p "$ROOT/.local"
rm -rf "$BUILD"
cp -R "$SOURCE" "$BUILD"
cd "$BUILD"
make -C ladr realclean
make -C mace4.src realclean
make -C provers.src realclean
make all CC='cc -std=gnu89 -Wno-error=implicit-int -Wno-error=implicit-function-declaration -Wno-error=incompatible-function-pointer-types'
printf 'Prover9_BIN=%s/bin\n' "$BUILD" > "$ROOT/.local/prover9.env"
