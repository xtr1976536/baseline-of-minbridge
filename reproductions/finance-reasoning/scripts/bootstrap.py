"""Acquire/verify pinned public assets and build the local Contriever index."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fr_repro.assets import prepare_assets, verify_assets
from fr_repro.common import load_config
from fr_repro.retrieval import build_index

parser = argparse.ArgumentParser()
parser.add_argument("--offline", action="store_true")
args = parser.parse_args()
config = load_config(Path(__file__).resolve().parents[1] / "configs/main.json")
prepare_assets(config["data_dir"], offline=args.offline)
_, _, functions = verify_assets(config["data_dir"])
print(build_index(config["data_dir"], functions, config["retriever"]), flush=True)
