from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

import verifiqa.retrieval.evidence_retriever as retriever_module
from verifiqa.corpus_builder import load_corpus
from verifiqa.dataset import load_financebench
from verifiqa.eval.retrieval_metrics import (
    _matches_oracle,
    _oracle_doc_pages,
    compute_retrieval_metrics,
)
from verifiqa.question_filter import is_numerical_example
from verifiqa.retrieval.evidence_retriever import EvidenceRetriever, _fact_query
from verifiqa.retrieval.planner import RetrievalPlanner
from verifiqa.types import RavResult


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/financebench_sample"))
    parser.add_argument("--corpus", type=Path, default=Path("data/corpus"))
    parser.add_argument("--audit", type=Path, default=Path("runs/retrieval_audit/retrieval_metrics.json"))
    parser.add_argument("--out", type=Path, default=Path("runs/retrieval_diagnostics"))
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--first-stage-k", type=int, default=100)
    parser.add_argument("--retriever-model", default="BAAI/bge-large-en-v1.5")
    parser.add_argument("--reranker-model", default="")
    args = parser.parse_args()

    examples, _ = load_financebench(args.data)
    examples = [example for example in examples if is_numerical_example(example)]
    chunks, corpus_stats = load_corpus(args.corpus)
    audit_metrics = json.loads(args.audit.read_text(encoding="utf-8"))
    audit_by_id = {row["financebench_id"]: row for row in audit_metrics["per_question"]}

    variants = [
        {
            "name": "baseline_current",
            "top_k": args.top_k,
            "metric_k": args.top_k,
            "question_limit_mode": "current",
            "lexical_weight": 1.0,
            "fact_page_diversity": False,
        },
        {
            "name": "question_rerank_topk",
            "top_k": args.top_k,
            "metric_k": args.top_k,
            "question_limit_mode": "top_k",
            "lexical_weight": 1.0,
            "fact_page_diversity": False,
        },
        {
            "name": "lexical_weight_0_5",
            "top_k": args.top_k,
            "metric_k": args.top_k,
            "question_limit_mode": "current",
            "lexical_weight": 0.5,
            "fact_page_diversity": False,
        },
        {
            "name": "lexical_weight_0_25",
            "top_k": args.top_k,
            "metric_k": args.top_k,
            "question_limit_mode": "current",
            "lexical_weight": 0.25,
            "fact_page_diversity": False,
        },
        {
            "name": "fact_page_diversity",
            "top_k": args.top_k,
            "metric_k": args.top_k,
            "question_limit_mode": "current",
            "lexical_weight": 1.0,
            "fact_page_diversity": True,
        },
        {
            "name": "top_k_15_metric_10",
            "top_k": 15,
            "metric_k": args.top_k,
            "question_limit_mode": "current",
            "lexical_weight": 1.0,
            "fact_page_diversity": False,
        },
        {
            "name": "top_k_15_metric_15",
            "top_k": 15,
            "metric_k": 15,
            "question_limit_mode": "current",
            "lexical_weight": 1.0,
            "fact_page_diversity": False,
        },
    ]

    args.out.mkdir(parents=True, exist_ok=True)
    variant_outputs = {}
    baseline_debug = None
    baseline_plans = None
    baseline_selections = None
    for variant in variants:
        run = run_variant(
            examples=examples,
            chunks=chunks,
            corpus_dir=args.corpus,
            retriever_model=args.retriever_model,
            reranker_model=args.reranker_model,
            first_stage_k=args.first_stage_k,
            top_k=variant["top_k"],
            metric_k=variant["metric_k"],
            question_limit_mode=variant["question_limit_mode"],
            lexical_weight=variant["lexical_weight"],
            fact_page_diversity=variant["fact_page_diversity"],
        )
        variant_outputs[variant["name"]] = {
            "config": variant,
            "metrics": summarize_metrics(run["metrics"]),
            "failure_mode_counts": run["metrics"].get("failure_mode_counts", {}),
        }
        if variant["name"] == "baseline_current":
            baseline_debug = run["debug_by_id"]
            baseline_plans = run["plans_by_id"]
            baseline_selections = run["selection_by_id"]
            (args.out / "baseline_metrics.json").write_text(
                json.dumps(run["metrics"], indent=2, sort_keys=True),
                encoding="utf-8",
            )
            write_jsonl(args.out / "baseline_retrieval_results.jsonl", run["retrieval_rows"])

    assert baseline_debug is not None and baseline_plans is not None and baseline_selections is not None
    failure_cases = diagnose_target_failures(
        audit_by_id=audit_by_id,
        debug_by_id=baseline_debug,
        selection_by_id=baseline_selections,
    )
    multi_page = diagnose_multi_page(
        audit_by_id=audit_by_id,
        debug_by_id=baseline_debug,
        plans_by_id=baseline_plans,
        selection_by_id=baseline_selections,
    )
    reranker_usage = summarize_reranker_usage(baseline_debug)

    summary = {
        "corpus_stats": corpus_stats,
        "audit_baseline_metrics": summarize_metrics(audit_metrics),
        "variant_metrics": variant_outputs,
        "reranker_usage": reranker_usage,
        "target_failure_summary": {
            "counts": dict(Counter(case["cause"] for case in failure_cases)),
            "cases": failure_cases,
        },
        "multi_page_summary": multi_page,
        "caveat": (
            "This audit uses RetrievalPlanner(None), i.e. the deterministic keyword fallback. "
            "The full pipeline can use Qwen/vLLM retrieval planning, so planner-dependent "
            "conclusions should be rechecked with logged Qwen plans."
        ),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "target_failure_counts": summary["target_failure_summary"]["counts"],
        "multi_page_counts": summary["multi_page_summary"]["counts"],
        "variant_metrics": variant_outputs,
        "reranker_usage": reranker_usage,
    }, indent=2, sort_keys=True))


def run_variant(
    *,
    examples,
    chunks,
    corpus_dir: Path,
    retriever_model: str,
    reranker_model: str,
    first_stage_k: int,
    top_k: int,
    metric_k: int,
    question_limit_mode: str,
    lexical_weight: float,
    fact_page_diversity: bool,
) -> dict:
    planner = RetrievalPlanner(None)
    debug_by_id = {}
    plans_by_id = {}
    selection_by_id = {}
    retrieval_rows = []
    results = []
    with lexical_weight_context(lexical_weight):
        retriever_kwargs = {
            "model_name": retriever_model,
            "rerank": True,
            "first_stage_k": first_stage_k,
            "embedding_cache_dir": corpus_dir,
        }
        if reranker_model:
            retriever_kwargs["reranker_model"] = reranker_model
        retriever = EvidenceRetriever(chunks, **retriever_kwargs)
        for example in examples:
            debug_records = []
            retriever.set_debug_callback(debug_records.append)
            plan = planner.plan(example.question)
            retrieved, selection = retrieve_with_plan_variant(
                retriever,
                example,
                plan,
                top_k=top_k,
                question_limit_mode=question_limit_mode,
                fact_page_diversity=fact_page_diversity,
            )
            retriever.set_debug_callback(None)
            chunk_ids = [chunk.chunk_id for chunk in retrieved]
            results.append(RavResult(
                financebench_id=example.financebench_id,
                question=example.question,
                answer="",
                final_status="RETRIEVED" if chunk_ids else "NO_EVIDENCE",
                first_pass_solver_status="RETRIEVAL_ONLY",
                gold_answer=example.answer,
                retrieved_chunk_ids=chunk_ids,
                retrieval_plan=plan,
                metric=plan.metric,
            ))
            debug_by_id[example.financebench_id] = debug_records
            plans_by_id[example.financebench_id] = plan
            selection_by_id[example.financebench_id] = selection
            retrieval_rows.append({
                "financebench_id": example.financebench_id,
                "question": example.question,
                "doc_name": example.doc_name,
                "oracle_pages": [{"doc_name": doc, "page": page} for doc, page in _oracle_doc_pages(example)],
                "retrieved_chunk_ids": chunk_ids,
                "retrieved_pages": [chunk_page(chunk) for chunk in retrieved],
                "retrieval_plan": {
                    "metric": plan.metric,
                    "facts": [
                        {
                            "name": fact.name,
                            "aliases": fact.aliases,
                            "period": fact.period,
                            "statement": fact.statement,
                        }
                        for fact in plan.facts
                    ],
                    "reason": plan.reason,
                },
            })
    return {
        "metrics": compute_retrieval_metrics(results, examples, k=metric_k),
        "debug_by_id": debug_by_id,
        "plans_by_id": plans_by_id,
        "selection_by_id": selection_by_id,
        "retrieval_rows": retrieval_rows,
    }


def retrieve_with_plan_variant(
    retriever: EvidenceRetriever,
    example,
    plan,
    *,
    top_k: int,
    question_limit_mode: str,
    fact_page_diversity: bool,
):
    if plan is None or not plan.facts:
        chunks = retriever.retrieve(
            example.question,
            company=example.company,
            doc_name=example.doc_name,
            top_k=top_k,
        )
        return chunks, {"events": [], "mode": "no_plan"}

    candidates, candidate_embeddings = retriever._filter("", example.company, example.doc_name)
    if not candidates:
        return [], {"events": [], "mode": "no_candidates"}

    fact_rankings = []
    for fact in plan.facts:
        ranked = retriever._rank_candidates(
            _fact_query(example.question, fact),
            candidates,
            candidate_embeddings,
            limit=max(retriever.first_stage_k, top_k),
            oracle_mode=False,
            aliases=fact.aliases,
            period=fact.period,
            statement=fact.statement,
            use_reranker=False,
        )
        fact_rankings.append(ranked)

    question_limit = top_k if question_limit_mode == "top_k" else max(retriever.first_stage_k, top_k)
    question_ranked = retriever._rank_candidates(
        example.question,
        candidates,
        candidate_embeddings,
        limit=question_limit,
        oracle_mode=False,
        use_reranker=True,
    )

    selected = []
    seen_chunks: set[str] = set()
    seen_pages: set[tuple[str, int | None]] = set()
    events = []

    def add_index(index: int, *, phase: str, fact_index: int | None = None, fact_name: str = "", rank: int | None = None) -> bool:
        chunk = candidates[index]
        if chunk.chunk_id in seen_chunks:
            return False
        selected.append(index)
        seen_chunks.add(chunk.chunk_id)
        page = page_tuple(chunk)
        seen_pages.add(page)
        events.append({
            "phase": phase,
            "fact_index": fact_index,
            "fact_name": fact_name,
            "candidate_rank": rank,
            "chunk_id": chunk.chunk_id,
            "doc_name": chunk.doc_name,
            "page": chunk.page,
            "source_type": chunk.source_type,
            "page_key": list(page),
        })
        return True

    for fact_index, ranked in enumerate(fact_rankings):
        fact = plan.facts[fact_index]
        candidates_to_try = list(enumerate(ranked, start=1))
        if fact_page_diversity:
            diverse = [(rank, index) for rank, index in candidates_to_try if page_tuple(candidates[index]) not in seen_pages]
            candidates_to_try = diverse or candidates_to_try
        for rank, index in candidates_to_try:
            if add_index(index, phase="fact_coverage", fact_index=fact_index, fact_name=fact.name, rank=rank):
                break
        if len(selected) >= top_k:
            return expand_selected(retriever, candidates, selected[:top_k], plan), {"events": events, "mode": "planned"}

    for rank, index in enumerate(question_ranked[:1], start=1):
        add_index(index, phase="question_top1", rank=rank)
        if len(selected) >= top_k:
            return expand_selected(retriever, candidates, selected[:top_k], plan), {"events": events, "mode": "planned"}

    cursor = 1
    while len(selected) < top_k:
        added = False
        for fact_index, ranked in enumerate(fact_rankings):
            if cursor < len(ranked):
                fact = plan.facts[fact_index]
                added = add_index(
                    ranked[cursor],
                    phase="round_robin",
                    fact_index=fact_index,
                    fact_name=fact.name,
                    rank=cursor + 1,
                ) or added
                if len(selected) >= top_k:
                    break
        if not added:
            break
        cursor += 1

    for rank, index in enumerate(question_ranked, start=1):
        add_index(index, phase="question_fill", rank=rank)
        if len(selected) >= top_k:
            break

    return expand_selected(retriever, candidates, selected[:top_k], plan), {"events": events, "mode": "planned"}


def expand_selected(retriever, candidates, selected, plan):
    return retriever._with_structured_rows(
        retriever._with_page_context([candidates[index] for index in selected]),
        retrieval_plan=plan,
    )


def diagnose_target_failures(*, audit_by_id, debug_by_id, selection_by_id) -> list[dict]:
    cases = []
    target_modes = {"wrong_page_same_document", "partial_multi_page_coverage"}
    for financebench_id, row in audit_by_id.items():
        if row["failure_mode"] not in target_modes:
            continue
        oracle_pages = [(item["doc_name"], item["page"]) for item in row["oracle_pages"]]
        missing_exact = [
            page for page in oracle_pages
            if page not in [(item["doc_name"], item["page"]) for item in row["retrieved_pages"]]
        ]
        analysis = analyze_page_survival(missing_exact or oracle_pages, debug_by_id[financebench_id])
        selection = selection_by_id[financebench_id]
        cause = classify_survival_cause(analysis)
        cases.append({
            "financebench_id": financebench_id,
            "failure_mode": row["failure_mode"],
            "oracle_pages": row["oracle_pages"],
            "retrieved_pages": row["retrieved_pages"],
            "missing_exact_pages": [{"doc_name": doc, "page": page} for doc, page in missing_exact],
            "cause": cause,
            "page_survival": analysis,
            "fact_coverage_events": [event for event in selection["events"] if event["phase"] == "fact_coverage"],
        })
    return cases


def analyze_page_survival(pages: Iterable[tuple[str, int]], debug_records: list[dict]) -> list[dict]:
    output = []
    for doc, page in pages:
        hits = []
        for record_index, record in enumerate(debug_records):
            matching = [
                item for item in record["first_stage"]
                if item["doc_name"] == doc and item["page"] == page
            ]
            for item in matching:
                hits.append({
                    "record_index": record_index,
                    "query_kind": query_kind(record),
                    "first_stage_rank": item["rank"],
                    "returned_rank": item["returned_rank"],
                    "rerank_rank": item["rerank_rank"],
                    "rerank_score": item["rerank_score"],
                    "reranker_applied": record["reranker_applied"],
                    "use_reranker": record["use_reranker"],
                    "chunk_id": item["chunk_id"],
                    "source_type": item["source_type"],
                    "dense_score": item["dense_score"],
                    "lexical_score": item["lexical_score"],
                    "combined_score": item["combined_score"],
                })
        output.append({
            "doc_name": doc,
            "page": page,
            "survived_first_stage": bool(hits),
            "hits": hits,
        })
    return output


def classify_survival_cause(page_survival: list[dict]) -> str:
    if not any(page["survived_first_stage"] for page in page_survival):
        return "first_stage_miss"
    for page in page_survival:
        for hit in page["hits"]:
            if (
                hit["reranker_applied"]
                and hit["rerank_rank"] is not None
                and hit["returned_rank"] is None
            ):
                return "cross_encoder_demoted"
    return "survived_first_stage_not_selected"


def diagnose_multi_page(*, audit_by_id, debug_by_id, plans_by_id, selection_by_id) -> dict:
    cases = []
    for financebench_id, row in audit_by_id.items():
        if row["n_distinct_oracle_pages"] <= 1:
            continue
        if row["recall_at_k"] >= 1.0:
            continue
        plan = plans_by_id[financebench_id]
        selection = selection_by_id[financebench_id]
        fact_events = [event for event in selection["events"] if event["phase"] == "fact_coverage"]
        selected_fact_pages = [tuple(event["page_key"]) for event in fact_events]
        selected_unique_pages = set(selected_fact_pages)
        oracle_pages = [(item["doc_name"], item["page"]) for item in row["oracle_pages"]]
        retrieved_pages = [(item["doc_name"], item["page"]) for item in row["retrieved_pages"]]
        missing_oracle = [
            page for page in oracle_pages
            if not any(_matches_oracle(retrieved, {page}) for retrieved in retrieved_pages)
        ]
        survival = analyze_page_survival(missing_oracle, debug_by_id[financebench_id])
        if len(fact_events) < min(len(plan.facts), 10):
            category = "fact_coverage_loop_did_not_place_one_per_fact"
        elif len(selected_unique_pages) < len(selected_fact_pages):
            category = "fact_coverage_selected_same_page_for_multiple_facts"
        elif not any(page["survived_first_stage"] for page in survival):
            category = "missing_page_never_survived_first_stage"
        else:
            category = "missing_page_survived_but_lower_rank_or_selection"
        cases.append({
            "financebench_id": financebench_id,
            "failure_mode": row["failure_mode"],
            "recall_at_k": row["recall_at_k"],
            "n_plan_facts": len(plan.facts),
            "oracle_pages": row["oracle_pages"],
            "retrieved_pages": row["retrieved_pages"],
            "missing_oracle_pages_with_tolerance": [{"doc_name": doc, "page": page} for doc, page in missing_oracle],
            "category": category,
            "fact_coverage_events": fact_events,
            "missing_page_survival": survival,
        })
    return {
        "counts": dict(Counter(case["category"] for case in cases)),
        "cases": cases,
    }


def summarize_reranker_usage(debug_by_id) -> dict:
    total_records = 0
    applied = 0
    requested = 0
    by_kind = defaultdict(lambda: Counter({"records": 0, "requested": 0, "applied": 0}))
    for records in debug_by_id.values():
        for record in records:
            total_records += 1
            kind = query_kind(record)
            by_kind[kind]["records"] += 1
            if record["use_reranker"]:
                requested += 1
                by_kind[kind]["requested"] += 1
            if record["reranker_applied"]:
                applied += 1
                by_kind[kind]["applied"] += 1
    return {
        "records": total_records,
        "requested": requested,
        "applied": applied,
        "by_kind": {kind: dict(counter) for kind, counter in by_kind.items()},
    }


def summarize_metrics(metrics: dict) -> dict:
    return {
        "k": metrics.get("k"),
        "n": metrics.get("n"),
        "hit_rate_at_k": metrics.get("hit_rate_at_k"),
        "exact_hit_rate_at_k": metrics.get("exact_hit_rate_at_k"),
        "mean_recall_at_k": metrics.get("mean_recall_at_k"),
        "mrr_at_k": metrics.get("mrr_at_k"),
        "multi_page_questions": metrics.get("multi_page_questions"),
        "multi_page_full_coverage_rate": metrics.get("multi_page_full_coverage_rate"),
    }


def query_kind(record: dict) -> str:
    text = record["query_text"]
    if "required fact:" in text:
        return "fact"
    return "question"


def chunk_page(chunk) -> dict:
    return {
        "chunk_id": chunk.chunk_id,
        "doc_name": chunk.doc_name,
        "page": chunk.page,
        "source_type": chunk.source_type,
    }


def page_tuple(chunk) -> tuple[str, int | None]:
    return chunk.doc_name, chunk.page


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


@contextmanager
def lexical_weight_context(weight: float):
    original = retriever_module._lexical_score
    if weight == 1.0:
        yield
        return

    def weighted(*args, **kwargs):
        return original(*args, **kwargs) * weight

    retriever_module._lexical_score = weighted
    try:
        yield
    finally:
        retriever_module._lexical_score = original


if __name__ == "__main__":
    main()
