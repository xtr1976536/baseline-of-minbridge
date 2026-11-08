#!/usr/bin/env bash
# RAG ablation: hold the agent, model, and verification path fixed; vary only
# how the evidence set E is retrieved. All three configs use BGE-large-en-v1.5
# so they share the cached corpus embeddings (no re-encoding).
#
#   r1_dense_norerank  dense first-stage, no reranking              (weakest)
#   r2_dense_rerank    dense first-stage + cross-encoder rerank
#   r3_hybrid_rerank   hybrid (BM25+dense RRF) + cross-encoder rerank  (strongest)
#
# Results land in results/rag_ablation/<config>/.
#
# Usage:  bash scripts/run_rag_ablation.sh [extra args passed to every run]
set -euo pipefail

PY=.venv-mac/bin/python
MODEL=claude-haiku-4-5-20251001

# BENCH=fb  -> FinanceBench, 67 questions (exact ID match with fb_detsmt_v2_haiku)
# BENCH=xbrl -> XBRLFiling, 600 questions (exact ID match with mc_calc_detsmt_v2_haiku)
BENCH=${BENCH:-xbrl}

if [ "$BENCH" = "fb" ]; then
  DATA=data/numerical_questions.jsonl
  CORPUS=data/corpus
  OUTDIR=results/rag_ablation_fb
  ARTIFACTS=()
else
  DATA=data/multicompany_provable/data/provable_calcrequired.jsonl
  CORPUS=data/corpus_filingcalc
  OUTDIR=results/rag_ablation_xbrl
  ARTIFACTS=(--xbrl-artifacts data/multicompany_provable/xbrl_artifacts)
fi

COMMON=(--data "$DATA" --corpus "$CORPUS" "${ARTIFACTS[@]}"
        --llm-mode claude --model "$MODEL"
        --deterministic-smt --workers 4 --top-k 10 --verbose)

EXTRA=("$@")

run () {
  local name=$1; shift
  echo "=== $name ==="
  PYTHONPATH=src "$PY" -m verifiqa.agent.cli run \
    "${COMMON[@]}" "$@" --out "$OUTDIR/$name" ${EXTRA[@]+"${EXTRA[@]}"}
}

mkdir -p "$OUTDIR"

run r1_dense_norerank  --retrieval-mode dense  --no-rerank
run r2_dense_rerank    --retrieval-mode dense
run r3_hybrid_rerank   --retrieval-mode hybrid

echo
echo "Done. Results in $OUTDIR/{r1_dense_norerank,r2_dense_rerank,r3_hybrid_rerank}/"
