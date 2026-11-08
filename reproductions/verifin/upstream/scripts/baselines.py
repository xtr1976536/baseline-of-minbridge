"""Accept/reject baselines for the VeriFin soundness comparison.

The paper's claim is about a *verifier*: given an LLM answer, decide accept
(VERIFIED) or reject (VIOLATED) and keep false-accepts at zero. These baselines
are the obvious *alternative* ways to make that accept/reject decision, so the
comparison isolates the decision mechanism, not the answer generator.

All baselines share the same dataset and oracle evidence. The canonical paper
runs use ``--answers-from`` to reuse one exact ``raw_answer`` pool from VeriFin;
without that option the script can instead generate new candidates. Output rows
use the schema scored by ``scripts/model_comparison.py``.

When a reused source row has a null ``claimed_value``, the loader reparses its
unchanged answer text. In the frozen one-pool artifacts this recovered 7
XBRLFiling and 6 FinanceBench values. Three FinanceBench answers remain
unparsed, including one that states the answer as the word ``zero``. The
grounded judge falls back to its evidence-only prompt when either the formula
or operand facts are missing (7 XBRLFiling and 9 FinanceBench rows). PoT
executes the complete generated program; only the saved ``pot_program`` audit
preview is truncated to 300 characters.

Baselines
---------
none            Raw LLM, no verification: accept every answer. Establishes the
                error rate the guardrail must catch (precision == accuracy, and
                false-accepts == number of wrong answers).
judge           LLM-as-judge: show a strong model the evidence + candidate answer
                and ask "is this correct?". accept->VERIFIED, reject->VIOLATED.
selfcons        Self-consistency @k: sample k answers (temp>0), take the majority
                value; accept it when agreement >= threshold, else abstain.
pot             Program-of-Thought self-check: the model writes a Python program that
                reads operands from the evidence and computes the value; the program is
                *executed by a deterministic interpreter* (not trusted from the LLM's
                text), and the candidate is accepted iff it matches within tolerance.
                Arithmetic is therefore exact -- any false-accept comes purely from the
                model choosing a wrong operand/formula, so this is the strongest
                self-check baseline and still not sound.

Usage
-----
    PYTHONPATH=src python scripts/baselines.py \
        --data data/multicompany_provable/data/provable_calcrequired.jsonl \
        --baseline judge \
        --answers-from results/mc_calc_detsmt_v2_haiku/results.jsonl \
        --out results/onepool/xbrl_judge \
        --llm-mode claude --model claude-haiku-4-5-20251001 --resume

    # then score it alongside VeriFin with the same tool:
    python scripts/model_comparison.py \
        "VeriFin=results/mc_calc_detsmt_v2_haiku" \
        "LLM-judge=results/onepool/xbrl_judge" \
        "raw-LLM=results/onepool/xbrl_none"

Controlled comparison (verification method is the ONLY variable)
----------------------------------------------------------------
Use --answers-from to judge the exact same raw-answer text a VeriFin run
produced, so answer generation is held fixed:

    PYTHONPATH=src python scripts/baselines.py --data $D --baseline judge \
        --answers-from results/mc_calc_detsmt_v2_haiku/results.jsonl \
        --out results/onepool/xbrl_judge \
        --llm-mode claude --model claude-haiku-4-5-20251001 --resume
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Auto-load .env from project root (same as verifiqa.agent.cli), so --llm-mode claude
# picks up ANTHROPIC_API_KEY without exporting it in the shell.
_env_file = ROOT / ".env"
if not os.environ.get("ANTHROPIC_API_KEY") and _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

from verifiqa.agent.agent import _parse_number
from verifiqa.dataset import chunks_from_examples, load_financebench_jsonl
from verifiqa.generation.answer_generator import AnswerGenerator
from verifiqa.generation.llm_client import ChatMessage, make_llm_client


# --------------------------------------------------------------------------- #
# LLM plumbing
# --------------------------------------------------------------------------- #
def build_llm(args):
    cfg = {"model": args.model, "max_tokens": 1024}
    if args.llm_mode == "vllm":
        cfg["base_url"] = args.vllm_url
        cfg["api_key"] = os.environ.get("VLLM_API_KEY") or os.environ.get("HF_TOKEN") or "EMPTY"
    return make_llm_client(mode=args.llm_mode, config=cfg)


def _evidence_text(example) -> tuple[str, list]:
    chunks = chunks_from_examples([example])
    text = "\n\n".join(c.text for c in chunks if c.text)
    return text, chunks


def _ask(llm, prompt: str, temperature: float, stage: str) -> str:
    return llm.chat(
        [ChatMessage(role="user", content=prompt)],
        temperature=temperature,
        stage=stage,
    ).strip()


# --------------------------------------------------------------------------- #
# Candidate answer (shared by none / judge / pot)
# --------------------------------------------------------------------------- #
def candidate_answer(gen: AnswerGenerator, example, chunks) -> str:
    try:
        return gen.generate(example.question, chunks).strip()
    except Exception:
        return ""


def load_answers(path: Path) -> dict[str, dict]:
    """id -> {answer, value, formula, facts} from a prior results file.

    Lets a baseline judge the exact same raw answers another run produced (e.g.
    VeriFin's), so the only variable is the accept/reject method, not generation.
    `formula` and `facts` are also captured so --with-formula can hand the judge the
    same grounded inputs VeriFin's verifier used (formula + authoritative operands).
    """
    answers: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rid = r.get("id")
        raw = str(r.get("raw_answer") or "").strip()
        value = r.get("claimed_value")
        if value is None:
            value = _parse_number(raw)
        facts = []
        for name, fv in (r.get("facts") or {}).items():
            if isinstance(fv, dict) and fv.get("value") is not None:
                facts.append((name, fv.get("value"), fv.get("unit", "")))
        if rid and raw:
            answers[rid] = {"answer": raw, "value": value,
                            "formula": r.get("formula") or "", "facts": facts}
    return answers


# --------------------------------------------------------------------------- #
# Baselines
# --------------------------------------------------------------------------- #
_JUDGE_PROMPT = """You are a careful financial-statement auditor. Decide whether the CANDIDATE ANSWER to the question is correct, using only the EVIDENCE. Check the arithmetic and the figures against the evidence.

QUESTION:
{question}

EVIDENCE (10-K excerpt):
{evidence}

CANDIDATE ANSWER: {answer}

Answer with exactly one word and nothing else: CORRECT or INCORRECT.
"""

# Grounded judge: handed the *same* inputs VerifiQA's verifier uses -- the formula and
# the authoritative operand values -- so the only remaining difference vs VerifiQA is the
# checking mechanism (LLM vs Z3). If it still false-accepts here, "it just needed the
# formula" is refuted.
# Grounded judge: handed the *same* inputs VeriFin's verifier uses -- the formula and
# the authoritative operand values -- so the only remaining difference vs VeriFin is the
# checking mechanism (LLM vs Z3). If it still false-accepts here, "it just needed the
# formula" is refuted.
_JUDGE_GROUNDED_PROMPT = """You are a careful financial-statement auditor. Verify whether the CANDIDATE ANSWER is correct.

QUESTION:
{question}

The filing reports these values:
{operands}

The correct value is computed as:
{formula}

CANDIDATE ANSWER: {answer}

Compute the formula from the reported values and compare it to the candidate answer.
Answer with exactly one word and nothing else: CORRECT or INCORRECT.
"""

# Chain-of-thought grounded judge: same inputs as the grounded judge, but the model
# is allowed to reason step by step (substitute, compute, compare) before committing
# a verdict on a final line. This tests whether the single-word constraint, rather than
# the judge's ability, was responsible for its false accepts.
_JUDGE_GROUNDED_COT_PROMPT = """You are a careful financial-statement auditor. Verify whether the CANDIDATE ANSWER is correct.

QUESTION:
{question}

The filing reports these values:
{operands}

The correct value is computed as:
{formula}

CANDIDATE ANSWER: {answer}

Work step by step: substitute the reported values into the formula, compute the result, and compare it with the candidate answer. Then, on the final line, write exactly one of:
VERDICT: CORRECT
VERDICT: INCORRECT
"""

_POT_PROMPT = """Compute the answer to the question from the EVIDENCE only by writing a short Python program. Read the operand values out of the evidence as numeric literals, then compute and assign the final answer to a variable named `result`. Do not use any imports or function calls other than arithmetic.

QUESTION:
{question}

EVIDENCE (10-K excerpt):
{evidence}

Reply with a single JSON object and nothing else:
{{"program": "<python that assigns a numeric `result`, e.g. 'revenue = 215938\\ncost = 62475\\nresult = revenue - cost'>"}}
"""


# Deterministic interpreter for the model's program: this is what makes PoT PoT.
# Arithmetic is executed exactly, so a false-accept can only come from the model
# choosing a wrong operand or formula -- never from a mental-math slip.
_POT_SAFE_BUILTINS = {"abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow}


def _run_program(source: str):
    """Execute a model-written arithmetic program and return its `result`, or None.

    Runs with no builtins and no imports; anything but plain arithmetic raises and
    yields None (-> the baseline abstains rather than trusting a broken program).
    """
    if not source or "result" not in source:
        return None
    if any(tok in source for tok in ("import", "__", "open(", "exec(", "eval(", "os.", "sys.")):
        return None
    ns: dict = {}
    try:
        exec(source, {"__builtins__": _POT_SAFE_BUILTINS}, ns)  # noqa: S102 - sandboxed, our own prompt
    except Exception:
        return None
    val = ns.get("result")
    try:
        return float(val)
    except Exception:
        return None

_DIRECT_PROMPT = """Answer the question using only the EVIDENCE. Give just the final numeric value.

QUESTION:
{question}

EVIDENCE (10-K excerpt):
{evidence}

Reply with a single JSON object and nothing else:
{{"value": <final numeric value, no units or commas>}}
"""


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


def _within_tol(a: float, b: float) -> bool:
    return abs(a - b) <= max(1.0, abs(b) * 0.01)


def decide_none(cand_value):
    # accept everything: raw-LLM floor
    return ("VERIFIED", cand_value, {})


def _parse_verdict(text: str) -> str:
    """Map a free-form judge reply to CORRECT / INCORRECT / "" (unparsed).

    INCORRECT is checked first: it contains the substring "correct", and negatives
    ("wrong"/"no") must win when both a positive and negative token appear.
    """
    t = (text or "").upper()
    if re.search(r"\bINCORRECT\b|\bWRONG\b|\bNOT\s+CORRECT\b|\bNO\b", t):
        return "INCORRECT"
    if re.search(r"\bCORRECT\b|\bYES\b", t):
        return "CORRECT"
    return ""


def _parse_cot_verdict(text: str) -> str:
    """Verdict from a chain-of-thought reply: read the final VERDICT: line so the
    reasoning's own uses of 'correct' do not leak into the decision."""
    hits = re.findall(r"VERDICT:\s*(INCORRECT|CORRECT)", (text or "").upper())
    if hits:
        return "INCORRECT" if hits[-1] == "INCORRECT" else "CORRECT"
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return _parse_verdict(lines[-1]) if lines else ""


def _format_operands(facts) -> str:
    if not facts:
        return "(no operand values available)"
    return "\n".join(f"  {name} = {value} {unit}".rstrip() for name, value, unit in facts)


def decide_judge(llm, example, evidence, cand_answer, cand_value, grounded=None, cot=False):
    # The judge is a verifier: it must decide CORRECT or INCORRECT. We force a
    # single-word reply and reprompt once if the model still wraps it in prose;
    # only a genuinely empty/garbage reply falls through to ABSTAIN (near-zero).
    if cand_value is None:
        return ("ABSTAIN", None, {"judge": "no_candidate"})
    # grounded mode: give the judge VerifiQA's own formula + authoritative operands.
    grounded_inputs = bool(grounded and grounded.get("formula") and grounded.get("facts"))
    if grounded_inputs and cot:
        prompt = _JUDGE_GROUNDED_COT_PROMPT.format(
            question=example.question,
            operands=_format_operands(grounded["facts"]),
            formula=grounded["formula"],
            answer=cand_answer,
        )
    elif grounded_inputs:
        prompt = _JUDGE_GROUNDED_PROMPT.format(
            question=example.question,
            operands=_format_operands(grounded["facts"]),
            formula=grounded["formula"],
            answer=cand_answer,
        )
    else:
        prompt = _JUDGE_PROMPT.format(question=example.question, evidence=evidence, answer=cand_answer)
    parse = _parse_cot_verdict if (grounded_inputs and cot) else _parse_verdict
    raw = _ask(llm, prompt, 0.0, "judge")
    verdict = parse(raw)
    if not verdict:
        raw = _ask(llm, prompt + "\n\nEnd with a line 'VERDICT: CORRECT' or 'VERDICT: INCORRECT'.",
                   0.0, "judge")
        verdict = parse(raw)
    if verdict == "CORRECT":
        return ("VERIFIED", cand_value, {"judge": verdict})
    if verdict == "INCORRECT":
        return ("VIOLATED", cand_value, {"judge": verdict})
    return ("ABSTAIN", cand_value, {"judge": "unparsed", "judge_raw": raw[:200]})


def decide_selfcons(llm, example, evidence, k, threshold):
    values = []
    for _ in range(k):
        raw = _ask(llm, _DIRECT_PROMPT.format(question=example.question, evidence=evidence),
                   0.7, "selfcons")
        v = _parse_number(str(_extract_json(raw).get("value", "")))
        if v is not None:
            values.append(round(float(v), 3))
    if not values:
        return ("ABSTAIN", None, {"selfcons": "no_values"})
    value, count = Counter(values).most_common(1)[0]
    agreement = count / k
    meta = {"selfcons_agreement": agreement, "selfcons_k": k, "selfcons_values": values}
    if agreement >= threshold:
        return ("VERIFIED", value, meta)          # confident -> accept the majority value
    return ("ABSTAIN", value, meta)               # not confident enough -> abstain


def decide_pot(llm, example, evidence, cand_value):
    if cand_value is None:
        return ("ABSTAIN", None, {"pot": "no_candidate"})
    raw = _ask(llm, _POT_PROMPT.format(question=example.question, evidence=evidence), 0.0, "pot")
    program = str(_extract_json(raw).get("program", ""))
    recomputed = _run_program(program)   # executed deterministically, not trusted from the LLM
    meta = {"pot_recomputed": recomputed, "pot_program": program[:300]}
    if recomputed is None:
        return ("ABSTAIN", cand_value, meta)
    if _within_tol(cand_value, recomputed):
        return ("VERIFIED", cand_value, meta)     # self-check agrees -> accept
    return ("VIOLATED", cand_value, meta)         # self-check disagrees -> reject


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def run(args) -> None:
    args.out.mkdir(parents=True, exist_ok=True)
    results_path = args.out / "results.jsonl"

    examples = load_financebench_jsonl(args.data)
    if args.limit:
        examples = examples[: args.limit]

    llm = build_llm(args)
    gen = AnswerGenerator(llm)

    if args.with_formula and (args.baseline != "judge" or not args.answers_from):
        raise SystemExit("--with-formula requires --baseline judge and --answers-from "
                         "(the formula + operands are read from the reused results file)")

    fixed_answers: dict[str, dict] = {}
    if args.answers_from:
        if args.baseline == "selfcons":
            raise SystemExit("--answers-from is incompatible with --baseline selfcons "
                             "(self-consistency samples its own answers)")
        fixed_answers = load_answers(args.answers_from)
        print(f"answers-from: reusing {len(fixed_answers)} candidate answers from {args.answers_from}")

    done: set[str] = set()
    if args.resume and results_path.exists():
        for line in results_path.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line).get("id"))
        print(f"resume: {len(done)} rows present, skipping them")

    counts: dict[str, int] = {}
    mode = "a" if args.resume else "w"
    t0 = time.time()
    with results_path.open(mode, encoding="utf-8") as fh:
        for i, ex in enumerate(examples):
            if args.ids and ex.financebench_id not in args.ids:
                continue
            if ex.financebench_id in done:
                continue
            evidence, chunks = _evidence_text(ex)
            if not evidence:
                continue

            t = time.time()
            # candidate answer (shared by none/judge/pot; selfcons samples its own)
            if args.baseline == "selfcons":
                cand_answer, cand_value = "", None
            elif args.answers_from:
                if ex.financebench_id not in fixed_answers:
                    continue  # only judge answers present in the reused set
                src = fixed_answers[ex.financebench_id]
                cand_answer, cand_value = src["answer"], src["value"]
            else:
                cand_answer = candidate_answer(gen, ex, chunks)
                cand_value = _parse_number(cand_answer)

            if args.baseline == "none":
                status, claimed, meta = decide_none(cand_value)
            elif args.baseline == "judge":
                grounded = fixed_answers.get(ex.financebench_id) if args.with_formula else None
                status, claimed, meta = decide_judge(llm, ex, evidence, cand_answer, cand_value, grounded, args.cot)
            elif args.baseline == "selfcons":
                status, claimed, meta = decide_selfcons(llm, ex, evidence, args.k, args.threshold)
            elif args.baseline == "pot":
                status, claimed, meta = decide_pot(llm, ex, evidence, cand_value)
            else:
                raise ValueError(args.baseline)

            row = {
                "id": ex.financebench_id,
                "question": ex.question,
                "baseline": args.baseline,
                "status": status,
                "claimed_value": claimed,
                "raw_answer": cand_answer,
                "gold_answer": ex.answer,
                "answer": ex.answer,
                "elapsed_s": round(time.time() - t, 2),
                **meta,
            }
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            counts[status] = counts.get(status, 0) + 1
            if args.verbose:
                print(f"[{i+1}/{len(examples)}] {ex.financebench_id} {status}"
                      f" claimed={claimed} gold={ex.answer!r}")

    print(f"\n{args.baseline}: {dict(counts)}  ({time.time()-t0:.0f}s)  -> {results_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--baseline", required=True, choices=["none", "judge", "selfcons", "pot"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--llm-mode", default="claude", choices=["claude", "vllm"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--vllm-url", default="http://localhost:11434/v1")
    ap.add_argument("--answers-from", type=Path, default=None,
                    help="reuse candidate answers from a prior results.jsonl (matched by id) "
                         "instead of generating them -- makes the verification method the only "
                         "variable vs a VerifiQA run. Not valid with --baseline selfcons.")
    ap.add_argument("--with-formula", action="store_true",
                    help="judge only: hand the judge VerifiQA's formula + authoritative operands "
                         "(from --answers-from), isolating LLM-vs-Z3 as the only difference.")
    ap.add_argument("--cot", action="store_true",
                    help="grounded judge only: allow chain-of-thought reasoning before the verdict "
                         "(tests whether the single-word constraint caused the false accepts).")
    ap.add_argument("--k", type=int, default=5, help="samples for self-consistency")
    ap.add_argument("--threshold", type=float, default=0.5, help="agreement to accept (self-consistency)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
