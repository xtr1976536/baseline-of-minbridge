# VeriFin experiment guide


Every run writes to `results/<dir>/` containing:
- `results.jsonl` — one row per question (status, claimed_value, gold, diagnostics)
- `summary.json` — run summary
- `smt/` — one `.smt2` per question (for inspection / re-running)

The primary safety metric is **FA (false accepts)**: an incorrect answer that
the verifier accepts. Report it together with coverage and false rejections;
do not infer guarantees beyond the evaluated runs.

---

## 0. Setup (once)

```bash
cd /path/to/verifiqa

# --- open models: Ollama (Mac-friendly, GPU via Metal) ---
# Serve WITH parallelism so --workers actually helps. Leave this in its own terminal:
OLLAMA_NUM_PARALLEL=4 OLLAMA_KEEP_ALIVE=-1 ollama serve
ollama pull qwen2.5:7b        # + any other models you want (llama3.1:8b, etc.)

# --- closed models: Claude ---
# ANTHROPIC_API_KEY is auto-loaded from the project .env; no export needed.

# --- shared paths (set once per shell) ---
export D=data/multicompany_provable/data/provable_calcrequired.jsonl   # dataset
export X=data/multicompany_provable/xbrl_artifacts                     # XBRL artifacts
export O=http://localhost:11434/v1                                     # Ollama endpoint
```

Everything runs with `PYTHONPATH=src`.

---

## 1. Main VeriFin runs (the method)

```bash
# one open model
PYTHONPATH=src python3 -m verifiqa.agent.cli run \
  --data $D --out results/mc_calc_qwen2.5-7b --xbrl-artifacts $X \
  --llm-mode vllm --model qwen2.5:7b --vllm-url $O \
  --workers 4 --verbose

# Claude (frontier reference)
PYTHONPATH=src python3 -m verifiqa.agent.cli run \
  --data $D --out results/mc_calc_claude --xbrl-artifacts $X \
  --llm-mode claude --model claude-haiku-4-5-20251001 \
  --workers 4 --verbose
```

Sweep several models at once (writes `results/<tag>_<model>/`):

```bash
python3 scripts/run_model_sweep.py --data $D --xbrl-artifacts $X \
  --tag mc_calc --models qwen2.5-7b llama3.1-8b claude --workers 4 --verbose
```

Model tags live in `scripts/run_model_sweep.py` (edit `MODELS` to add more).

---

## 2. Deterministic-SMT ablation

Renders the SMT directly from the IR (no autoformalizer LLM). Always well-formed,
so it removes `solver_INVALID` abstentions while keeping FA = 0.

```bash
PYTHONPATH=src python3 -m verifiqa.agent.cli run \
  --data $D --out results/mc_calc_detsmt_qwen2.5-7b --xbrl-artifacts $X \
  --llm-mode vllm --model qwen2.5:7b --vllm-url $O \
  --deterministic-smt --workers 4 --verbose
```

Compare against the LLM-SMT run:

```bash
python3 scripts/model_comparison.py \
  "LLM-SMT=results/mc_calc_qwen2.5-7b" \
  "deterministic-SMT=results/mc_calc_detsmt_qwen2.5-7b"
```

---

## 3. Baselines (accept/reject comparison)

The canonical paper baselines use a **single raw-answer pool**. The
`--answers-from` option reuses the exact `raw_answer` text produced by the
Claude Haiku 4.5 VeriFin run, so answer generation is held fixed while the
accept/reject method changes.

```bash
ANS=results/mc_calc_detsmt_v2_haiku/results.jsonl  # fixed XBRLFiling answers

# raw LLM floor: accept everything (establishes how many wrong answers exist)
PYTHONPATH=src python3 scripts/baselines.py --data $D --baseline none \
  --answers-from $ANS --out results/onepool/xbrl_none \
  --llm-mode claude --model claude-haiku-4-5-20251001 --resume

# LLM-as-judge, evidence only
PYTHONPATH=src python3 scripts/baselines.py --data $D --baseline judge \
  --answers-from $ANS --out results/onepool/xbrl_judge \
  --llm-mode claude --model claude-haiku-4-5-20251001 --resume

# LLM-as-judge GIVEN the formula + authoritative operands (the "everything" baseline)
PYTHONPATH=src python3 scripts/baselines.py --data $D --baseline judge --with-formula \
  --answers-from $ANS --out results/onepool/xbrl_judge_formula \
  --llm-mode claude --model claude-haiku-4-5-20251001 --resume

# Program-of-Thought: model writes Python, it is EXECUTED, compared to the candidate
PYTHONPATH=src python3 scripts/baselines.py --data $D --baseline pot \
  --answers-from $ANS --out results/onepool/xbrl_pot \
  --llm-mode claude --model claude-haiku-4-5-20251001 --resume

```

What each baseline is:

| baseline | what it does | given the formula? |
|---|---|---|
| `none` | accept every answer (raw-LLM floor) | — |
| `judge` | LLM sees evidence + answer, says CORRECT/INCORRECT | no |
| `judge --with-formula` | same, but handed the formula + operands | **yes** |
| `pot` | LLM writes code, code is executed, compare | no (reads operands itself) |

The frozen canonical artifacts and outcome counts (`TA/FA/TR/FR/AB`) are:

| Dataset | Direct LLM | LLM judge | Judge + formula | Program of Thought |
|---|---|---|---|---|
| XBRLFiling | `onepool/xbrl_none`: 508/92/0/0/0 | `onepool/xbrl_judge`: 195/26/66/313/0 | `onepool/xbrl_judge_formula`: 480/75/17/28/0 | `onepool/xbrl_pot`: 444/6/79/49/22 |
| FinanceBench | `onepool/fb_none`: 46/18/0/0/3 | `onepool/fb_judge`: 22/7/11/24/3 | `onepool/fb_judge_formula`: 34/13/5/12/3 | `onepool/fb_pot`: 40/4/14/6/3 |

All paths in the table are relative to `results/`. FinanceBench uses
`results/fb_detsmt_v2_haiku/results.jsonl` as its answer source and
`data/numerical_questions.jsonl` as its 67-question dataset.

The raw-answer text matches its source run for all 600/67 questions. The
baseline loader reparses text only when the source `claimed_value` is null,
recovering 7 XBRLFiling and 6 FinanceBench numerical values without changing
the answer text. Three FinanceBench candidates remain unparsed; one says that
the ratio is textual `zero`, while two are narrative answers. Under the
canonical scoring policy all three are abstentions.

Judge + formula is grounded only when both a formula and operand facts are
available in the answer-source artifact. It falls back to the evidence-only
judge for 7 XBRLFiling and 9 FinanceBench questions with incomplete grounded
inputs. Program-of-Thought execution uses the complete generated program; the
`pot_program` field retained in `results.jsonl` is a 300-character audit
preview and may therefore appear truncated.

---

## 4. Score everything

```bash
# per-model VeriFin table
python3 scripts/model_comparison.py \
  "claude=results/mc_calc_claude" \
  "qwen2.5-7b=results/mc_calc_qwen2.5-7b" \
  "detSMT=results/mc_calc_detsmt_qwen2.5-7b" \
  --csv results/mc_calc_comparison.csv

# baselines vs VeriFin (same raw-answer pool) — the headline comparison
python3 scripts/model_comparison.py \
  "VeriFin=results/mc_calc_detsmt_v2_haiku" \
  "raw-LLM=results/onepool/xbrl_none" \
  "judge-evidence=results/onepool/xbrl_judge" \
  "judge+formula=results/onepool/xbrl_judge_formula" \
  "PoT=results/onepool/xbrl_pot"
```

Columns: `prec` precision · `catch` catch-rate on wrong answers · `acc` decision
accuracy · `abst` abstention · `TA/TC/FR/FA/ABST` confusion buckets · `errs` #wrong
answers. Treat every nonzero FA as a safety failure and report a zero count only
for runs whose per-question outcomes have been audited.

Notebook version of these tables (renders inline, output baked in):
`notebooks/agent_financebench_result_metrics.ipynb`.

---

## Flag reference

| flag | meaning |
|---|---|
| `--llm-mode vllm --vllm-url $O` | any OpenAI-compatible endpoint (Ollama on Mac) |
| `--llm-mode claude --model claude-…` | Claude API (key from `.env`) |
| `--resume` | skip rows already done; safe to re-run after an interruption |
| `--deterministic-smt` | render SMT from the IR (no autoformalizer LLM) |
| `--workers N` | parallel questions; match `OLLAMA_NUM_PARALLEL` |
| `--ids ID1 ID2 …` | run only specific questions (debugging) |
| `--answers-from FILE` | baselines only: judge a fixed answer set |
| `--with-formula` | judge baseline only: hand it the formula + operands |
| `--limit N` | first N questions only (smoke test) |

---

## Notes

- **Match `--workers` to `OLLAMA_NUM_PARALLEL`.** With the default (1), extra workers
  just queue and give no speedup.
- **Interrupted runs:** just re-run the same command with `--resume`.
