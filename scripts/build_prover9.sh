#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../upstream/Logic-LLM/models/symbolic_solvers/Prover9"
make -C ladr realclean
make -C mace4.src realclean
make -C provers.src realclean
make all CC='cc -std=gnu89 -Wno-error=implicit-int -Wno-error=implicit-function-declaration -Wno-error=incompatible-function-pointer-types'
