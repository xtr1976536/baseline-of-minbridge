"""Recover benchmark identities and knowledge-graph evidence without a paid API."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gbfr.data import write_json
from gbfr.reconciliation import reconcile_datasets
from gbfr.graph_recovery import inventory_graph
from gbfr.paper_consistency import audit_main_table, audit_directed_degree_claims
from gbfr.source_recovery import source_audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--datasets-only", action="store_true")
    args = parser.parse_args()
    result = reconcile_datasets(ROOT / "research/upstream", ROOT / "data/raw/official",
                                ROOT / "research/history", ROOT / "data/reconciled", offline=args.offline)
    write_json(ROOT / "research/reconciliation/dataset_recovery.json", result)
    write_json(ROOT / "research/reconciliation/table_consistency.json", audit_main_table())
    write_json(ROOT / "research/reconciliation/graph_statistics_consistency.json",
               audit_directed_degree_claims(7521, 20152, "1.6", "2.3"))
    sources = source_audit(ROOT / "research/upstream", ROOT / "data/raw", ROOT / "research/reconciliation", offline=args.offline)
    print("FinanceReasoning official rows verified:", sources["FinanceReasoning"]["original_count"], flush=True)
    print("CFBenchmark label disagreements:", len(sources["CFBenchmark"]["gold_label_edits_in_gbfr_release"]), flush=True)
    for name, item in result["datasets"].items():
        print(name, item["actual"], "scalar_label_exceptions=", len(item["unresolved_labels"]))
    if not args.datasets_only:
        graph = inventory_graph(ROOT / "research/upstream/knowledge_base/term_en_final.json",
                                ROOT / "data/reconciliation/fmkg",
                                ROOT / "research/reconciliation/graph_recovery.json")
        print("Graph formula recovery:", graph["formula_status"], flush=True)
        print("Formula field completeness variations:", graph["formula_presence_variations"], flush=True)
        print("Formula/code review:", graph["formula_code_review_categories"], flush=True)
    print("Recovered selections are not asserted to solve all paper inconsistencies.")


if __name__ == "__main__":
    main()
