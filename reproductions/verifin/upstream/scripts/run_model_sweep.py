"""Run the verifier pipeline across several models, then print the comparison table.

Each model entry carries its own OpenAI-compatible endpoint. On a Mac use Ollama
(GPU via Metal); vLLM only serves on Linux + NVIDIA, so its entries are for a GPU box.

Serving efficiently (Mac / Ollama):
    # Concurrency is the main throughput lever. Ollama's default OLLAMA_NUM_PARALLEL is
    # often 1, so --workers > 1 alone does nothing — the requests just queue. Launch the
    # server with parallelism matching your workers, and keep the model resident:
    OLLAMA_NUM_PARALLEL=4 OLLAMA_KEEP_ALIVE=-1 ollama serve
    # then run the sweep with --workers 4. Per-question latency is dominated by the agent's
    # several sequential LLM calls, so parallelism must come from across questions (workers),
    # not within one. Bump num_ctx (Modelfile / request options) if evidence prompts exceed 4096.

Runs use --resume, so you can serve one model, sweep it, swap models, and re-run the
same command; each model's results land in results/<tag>_<name>/ and completed ones
are skipped.

Example:
    python scripts/run_model_sweep.py \
        --data data/multicompany_provable/data/provable_calcrequired.jsonl \
        --xbrl-artifacts data/multicompany_provable/xbrl_artifacts \
        --tag mc_calc --models qwen2.5-7b llama3.1-8b claude --workers 4 [--limit 15]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# name -> how to invoke it. "mode": "vllm" means any OpenAI-compatible endpoint
# (vLLM on a GPU box, OR Ollama/LM Studio locally — just set the right url + tag).
_OLLAMA = "http://localhost:11434/v1"   # `ollama serve` default
_VLLM = "http://localhost:8000/v1"      # `vllm serve ... --port 8000`
MODELS: dict[str, dict] = {
    # --- Ollama (Mac-friendly; `ollama pull <tag>` first) --------------------
    # small open foil — makes more errors, exercises the guardrail hard
    "qwen3-4b":     {"mode": "vllm", "model": "qwen3:4b",       "url": _OLLAMA},
    "qwen2.5-7b":   {"mode": "vllm", "model": "qwen2.5:7b",     "url": _OLLAMA},
    "llama3.1-8b":  {"mode": "vllm", "model": "llama3.1:8b",    "url": _OLLAMA},
    "gpt-oss-20b":  {"mode": "vllm", "model": "gpt-oss:20b",    "url": _OLLAMA},
    "qwen-32b":     {"mode": "vllm", "model": "qwen:32b",       "url": _OLLAMA},  # Qwen1.5-32B (installed)
    "qwen2.5-32b":  {"mode": "vllm", "model": "qwen2.5:32b",    "url": _OLLAMA},
    "llama3.3-70b": {"mode": "vllm", "model": "llama3.3:70b",   "url": _OLLAMA},
    "r1-32b":       {"mode": "vllm", "model": "deepseek-r1:32b", "url": _OLLAMA},
    # --- vLLM (GPU box; HF repo ids) -----------------------------------------
    "vllm-qwen3-4b": {"mode": "vllm", "model": "Qwen/Qwen3-4B-Instruct-2507", "url": _VLLM},
    # --- finance-tuned (LoRA adapter on Llama-3-8B) --------------------------
    # HF: FinGPT/fingpt-mt_llama3-8b_lora  (base: meta-llama/Meta-Llama-3-8B).
    # WARNING: this adapter is fine-tuned for financial SENTIMENT classification
    # (pos/neg/neutral), NOT numerical QA -- it is a poor answer model for the
    # calc-required task (task mismatch -> mostly unparseable answers). Kept here
    # only for reference; prefer a finance model trained for numerical/financial
    # reasoning if a "finance-tuned" answer-model point is wanted.
    # Not an Ollama model. Serve base + LoRA on a GPU box, e.g.:
    #   vllm serve meta-llama/Meta-Llama-3-8B --enable-lora \
    #        --lora-modules fingpt=FinGPT/fingpt-mt_llama3-8b_lora --port 8000
    "fingpt-llama3-8b": {"mode": "vllm", "model": "fingpt", "url": _VLLM},
    # --- frontier closed reference -------------------------------------------
    "claude":       {"mode": "claude", "model": "claude-haiku-4-5-20251001"},
}


def run_model(name: str, cfg: dict, args) -> Path:
    out = ROOT / "results" / f"{args.tag}_{name}"
    cmd = [
        sys.executable, "-m", "verifiqa.agent.cli", "run",
        "--data", str(args.data),
        "--out", str(out),
        "--xbrl-artifacts", str(args.xbrl_artifacts),
        "--llm-mode", cfg["mode"],
        "--model", cfg["model"],
        "--workers", str(args.workers),
        "--resume",
    ]
    if cfg["mode"] == "vllm":
        cmd += ["--vllm-url", cfg["url"]]
    if args.limit:
        cmd += ["--limit", str(args.limit)]
    if args.repair:
        cmd += ["--repair"]
    if args.verbose:
        cmd += ["--verbose"]
    env = {"PYTHONPATH": str(ROOT / "src")}
    print(f"\n{'='*70}\n[{name}] {cfg['model']}  ({cfg['mode']})\n{'='*70}")
    import os
    subprocess.run(cmd, env={**os.environ, **env}, check=False)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--xbrl-artifacts", type=Path, required=True)
    ap.add_argument("--tag", required=True, help="prefix for result dirs: results/<tag>_<model>")
    ap.add_argument("--models", nargs="+", required=True,
                    help=f"subset of: {', '.join(MODELS)}")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--repair", action="store_true",
                    help="On VIOLATED, re-ask the LLM once with diagnostic feedback and re-verify "
                         "(sound: adopts the retry only if it verifies). Passed through to the CLI.")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    unknown = [m for m in args.models if m not in MODELS]
    if unknown:
        ap.error(f"unknown models {unknown}; choose from {list(MODELS)}")

    out_dirs = []
    for name in args.models:
        out_dirs.append((name, run_model(name, MODELS[name], args)))

    # comparison table across whatever produced results
    print(f"\n{'='*70}\nCOMPARISON\n{'='*70}")
    from model_comparison import main as compare
    compare([f"{name}={d}" for name, d in out_dirs if (d / 'results.jsonl').exists()]
            + ["--csv", str(ROOT / 'results' / f'{args.tag}_comparison.csv')])


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
