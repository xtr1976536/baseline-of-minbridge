import argparse
import asyncio
import json
from pathlib import Path

from .assets import prepare_assets
from .common import load_config


def main():
    parser = argparse.ArgumentParser(description="FinanceReasoning Table 5 best GPT-4o method only")
    parser.add_argument("command", choices=["prepare", "index", "check", "run"])
    parser.add_argument("--config", default=str(Path(__file__).parent.parent / "configs/main.json"))
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--retry-errors", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    try:
        if args.command == "prepare":
            result = prepare_assets(config["data_dir"], offline=args.offline)
        elif args.command == "index":
            from .assets import verify_assets
            from .retrieval import build_index
            _, _, functions = verify_assets(config["data_dir"])
            result = build_index(config["data_dir"], functions, config["retriever"])
        elif args.command == "check":
            from .runner import preflight
            problems, _, functions = preflight(config)
            result = {"ready": True, "questions": len(problems), "functions": len(functions), "real_api_calls": 0}
        else:
            from .runner import run
            result = asyncio.run(run(config, limit=args.limit, retry_errors=args.retry_errors))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command == "run" and not result["complete"]:
            return 2
        return 0
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"Stopped: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
