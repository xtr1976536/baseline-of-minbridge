import argparse
import asyncio
import json
from pathlib import Path

from .data import prepare
from .runner import lock_assets, preflight, report, resolve_paths, run, audit_datasets
from .types import AssetError


def main():
    parser = argparse.ArgumentParser(description="Paper-first GBFR; main experiment only")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="Normalize published data and audit discrepancies (no API)")
    prep.add_argument("--upstream", type=Path, default=Path("research/upstream"))
    prep.add_argument("--output", type=Path, default=Path("data/processed"))
    prep.add_argument("--official", type=Path, default=Path("data/raw/official"))
    prep.add_argument("--recovered", type=Path, default=Path("data/reconciled"))
    for name in ["check", "check-data", "run", "report", "lock-assets"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--config", type=Path, default=Path("configs/main.json"))
        if name == "lock-assets":
            cmd.add_argument("--provenance", required=True, help="Source and human review of the exact paper assets")
        if name == "run":
            cmd.add_argument("--retry-errors", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            recovered = args.recovered if (args.recovered / "selection_manifest.json").exists() else None
            result = prepare(args.upstream, args.output, args.official, recovered)
            print(json.dumps({"datasets": {n: v["actual"] for n, v in result["datasets"].items()},
                              "graph": result["raw_graph"], "paper_ready": result["paper_ready"]}, ensure_ascii=False, indent=2))
            return
        config = resolve_paths(args.config)
        if args.command == "check":
            graph, datasets = preflight(config)
            print(json.dumps({"graph": graph.stats(), "datasets": {k: len(v) for k, v in datasets.items()}}, indent=2))
        elif args.command == "check-data":
            print(json.dumps(audit_datasets(config), ensure_ascii=False, indent=2))
        elif args.command == "run":
            asyncio.run(run(config, retry_errors=args.retry_errors))
        elif args.command == "report":
            print(report(config))
        elif args.command == "lock-assets":
            print(lock_assets(config, args.provenance))
    except (AssetError, FileNotFoundError) as exc:
        parser.exit(2, "实验尚未就绪: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
