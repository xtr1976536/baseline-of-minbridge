from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from verifiqa.corpus_builder import load_corpus
from verifiqa.dataset import load_financebench
from verifiqa.eval.retrieval_metrics import _matches_oracle, _oracle_doc_pages
from verifiqa.question_filter import is_numerical_example
from verifiqa.retrieval.evidence_retriever import EvidenceRetriever, _fact_query
from verifiqa.retrieval.planner import RetrievalPlanner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/financebench_sample"))
    parser.add_argument("--corpus", type=Path, default=Path("data/corpus"))
    parser.add_argument("--audit", type=Path, default=Path("runs/retrieval_audit/retrieval_metrics.json"))
    parser.add_argument("--out", type=Path, default=Path("runs/retrieval_diagnostics_light"))
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--first-stage-k", type=int, default=100)
    parser.add_argument("--retriever-model", default="BAAI/bge-large-en-v1.5")
    args = parser.parse_args()

    examples, _ = load_financebench(args.data)
    examples = [example for example in examples if is_numerical_example(example)]
    example_by_id = {example.financebench_id: example for example in examples}
    chunks, corpus_stats = load_corpus(args.corpus)
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    audit_by_id = {row["financebench_id"]: row for row in audit["per_question"]}

    retriever = EvidenceRetriever(
        chunks,
        model_name=args.retriever_model,
        rerank=False,
        first_stage_k=args.first_stage_k,
        embedding_cache_dir=args.corpus,
    )
    planner = RetrievalPlanner(None)

    debug_by_id = {}
    plans_by_id = {}
    selection_by_id = {}
    for example in examples:
        records = []
        retriever.set_debug_callback(records.append)
        plan = planner.plan(example.question)
        selection = simulate_current_planned_selection(
            retriever,
            example,
            plan,
            top_k=args.top_k,
        )
        retriever.set_debug_callback(None)
        debug_by_id[example.financebench_id] = records
        plans_by_id[example.financebench_id] = plan
        selection_by_id[example.financebench_id] = selection

    target_cases = []
    for financebench_id, row in audit_by_id.items():
        if row["failure_mode"] not in {"wrong_page_same_document", "partial_multi_page_coverage"}:
            continue
        plan = plans_by_id[financebench_id]
        missing_exact = missing_exact_pages(row)
        survival = page_survival(missing_exact or oracle_pages(row), debug_by_id[financebench_id])
        cause = classify_target_case(plan, survival)
        target_cases.append({
            "financebench_id": financebench_id,
            "failure_mode": row["failure_mode"],
            "n_plan_facts": len(plan.facts),
            "cause": cause,
            "oracle_pages": row["oracle_pages"],
            "retrieved_pages": row["retrieved_pages"],
            "missing_exact_pages": [{"doc_name": doc, "page": page} for doc, page in missing_exact],
            "survival": survival,
            "fact_coverage_events": [
                event for event in selection_by_id[financebench_id]["events"]
                if event["phase"] == "fact_coverage"
            ],
        })

    multi_page_cases = []
    for financebench_id, row in audit_by_id.items():
        if row["n_distinct_oracle_pages"] <= 1 or row["recall_at_k"] >= 1.0:
            continue
        plan = plans_by_id[financebench_id]
        selection = selection_by_id[financebench_id]
        fact_events = [event for event in selection["events"] if event["phase"] == "fact_coverage"]
        missing_pages = missing_pages_with_tolerance(row)
        survival = page_survival(missing_pages, debug_by_id[financebench_id])
        fact_pages = [tuple(event["page_key"]) for event in fact_events]
        if len(fact_events) < min(len(plan.facts), args.top_k):
            category = "fact_coverage_loop_did_not_place_one_per_fact"
        elif len(set(fact_pages)) < len(fact_pages):
            category = "fact_coverage_selected_same_page_for_multiple_facts"
        elif not any(item["survived_first_stage"] for item in survival):
            category = "missing_page_never_survived_first_stage"
        else:
            category = "missing_page_survived_but_not_selected"
        multi_page_cases.append({
            "financebench_id": financebench_id,
            "failure_mode": row["failure_mode"],
            "recall_at_k": row["recall_at_k"],
            "n_plan_facts": len(plan.facts),
            "category": category,
            "oracle_pages": row["oracle_pages"],
            "retrieved_pages": row["retrieved_pages"],
            "missing_pages_with_tolerance": [{"doc_name": doc, "page": page} for doc, page in missing_pages],
            "fact_coverage_events": fact_events,
            "missing_page_survival": survival,
        })

    reranker_applicability = summarize_reranker_applicability(debug_by_id, plans_by_id)
    summary = {
        "corpus_stats": corpus_stats,
        "audit_metrics": {
            "hit_rate_at_k": audit["hit_rate_at_k"],
            "exact_hit_rate_at_k": audit["exact_hit_rate_at_k"],
            "mrr_at_k": audit["mrr_at_k"],
            "mean_recall_at_k": audit["mean_recall_at_k"],
            "multi_page_full_coverage_rate": audit["multi_page_full_coverage_rate"],
            "failure_mode_counts": audit["failure_mode_counts"],
        },
        "target_failure_counts": dict(Counter(case["cause"] for case in target_cases)),
        "target_failure_cases": target_cases,
        "multi_page_counts": dict(Counter(case["category"] for case in multi_page_cases)),
        "multi_page_cases": multi_page_cases,
        "reranker_applicability": reranker_applicability,
        "caveat": (
            "This diagnosis uses the deterministic fallback planner. The full pipeline may use Qwen/vLLM "
            "retrieval plans, so planner-dependent conclusions should be rechecked on logged Qwen plans."
        ),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "target_failure_counts": summary["target_failure_counts"],
        "multi_page_counts": summary["multi_page_counts"],
        "reranker_applicability": summary["reranker_applicability"],
    }, indent=2, sort_keys=True))


def simulate_current_planned_selection(retriever, example, plan, *, top_k: int) -> dict:
    candidates, candidate_embeddings = retriever._filter("", example.company, example.doc_name)
    events = []
    if not candidates:
        return {"events": events, "mode": "no_candidates"}
    if not plan.facts:
        retriever._rank_candidates(
            example.question,
            candidates,
            candidate_embeddings,
            limit=top_k,
            oracle_mode=False,
            use_reranker=False,
        )
        return {"events": events, "mode": "no_plan"}

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

    question_ranked = retriever._rank_candidates(
        example.question,
        candidates,
        candidate_embeddings,
        limit=max(retriever.first_stage_k, top_k),
        oracle_mode=False,
        use_reranker=True,
    )

    selected = []
    seen_chunks = set()

    def add_index(index: int, *, phase: str, fact_index=None, fact_name="", rank=None) -> bool:
        chunk = candidates[index]
        if chunk.chunk_id in seen_chunks:
            return False
        selected.append(index)
        seen_chunks.add(chunk.chunk_id)
        events.append({
            "phase": phase,
            "fact_index": fact_index,
            "fact_name": fact_name,
            "candidate_rank": rank,
            "chunk_id": chunk.chunk_id,
            "doc_name": chunk.doc_name,
            "page": chunk.page,
            "source_type": chunk.source_type,
            "page_key": [chunk.doc_name, chunk.page],
        })
        return True

    for fact_index, ranked in enumerate(fact_rankings):
        fact = plan.facts[fact_index]
        for rank, index in enumerate(ranked, start=1):
            if add_index(index, phase="fact_coverage", fact_index=fact_index, fact_name=fact.name, rank=rank):
                break
        if len(selected) >= top_k:
            return {"events": events, "mode": "planned"}

    for rank, index in enumerate(question_ranked[:1], start=1):
        add_index(index, phase="question_top1", rank=rank)
    return {"events": events, "mode": "planned"}


def page_survival(pages, debug_records) -> list[dict]:
    output = []
    for doc, page in pages:
        hits = []
        for record_index, record in enumerate(debug_records):
            for item in record["first_stage"]:
                if item["doc_name"] == doc and item["page"] == page:
                    hits.append({
                        "record_index": record_index,
                        "query_kind": "fact" if "required fact:" in record["query_text"] else "question",
                        "first_stage_rank": item["rank"],
                        "returned_rank_without_rerank": item["returned_rank"],
                        "chunk_id": item["chunk_id"],
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


def classify_target_case(plan, survival) -> str:
    if not any(item["survived_first_stage"] for item in survival):
        return "first_stage_miss"
    if not plan.facts:
        return "survived_first_stage_then_absent_after_cross_encoder_final"
    return "survived_first_stage_but_not_selected"


def summarize_reranker_applicability(debug_by_id, plans_by_id) -> dict:
    no_plan = sum(1 for plan in plans_by_id.values() if not plan.facts)
    planned = len(plans_by_id) - no_plan
    planned_question_records = 0
    planned_question_records_where_current_code_would_not_rerank = 0
    for financebench_id, records in debug_by_id.items():
        if not plans_by_id[financebench_id].facts:
            continue
        for record in records:
            if "required fact:" not in record["query_text"]:
                planned_question_records += 1
                if record["limit"] >= record["first_k"]:
                    planned_question_records_where_current_code_would_not_rerank += 1
    return {
        "no_plan_questions_where_retrieve_path_uses_cross_encoder": no_plan,
        "planned_questions": planned,
        "planned_question_records": planned_question_records,
        "planned_question_records_where_current_limit_prevents_cross_encoder": (
            planned_question_records_where_current_code_would_not_rerank
        ),
        "fact_records_use_cross_encoder": 0,
    }


def oracle_pages(row):
    return [(item["doc_name"], item["page"]) for item in row["oracle_pages"]]


def retrieved_pages(row):
    return [(item["doc_name"], item["page"]) for item in row["retrieved_pages"]]


def missing_exact_pages(row):
    retrieved = set(retrieved_pages(row))
    return [page for page in oracle_pages(row) if page not in retrieved]


def missing_pages_with_tolerance(row):
    retrieved = retrieved_pages(row)
    missing = []
    for page in oracle_pages(row):
        if not any(_matches_oracle(candidate, {page}) for candidate in retrieved):
            missing.append(page)
    return missing


if __name__ == "__main__":
    main()
