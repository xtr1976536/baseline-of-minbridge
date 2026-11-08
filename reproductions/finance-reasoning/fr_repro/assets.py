"""Immutable official inputs; serving objects deliberately omit labels and solutions."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import math
from pathlib import Path
import re

import httpx

from .common import read_json, sha256, write_json

REPO = "BUPT-Reasoning-Lab/FinanceReasoning"
COMMIT = "b0fe6455396f831955e4eb988472b4a563403bc5"
SOURCES = {
    "hard.json": ("data/FinanceReasoning/hard.json", "ca8c055ef104176131da2e0f533897350cde3b93c4754575b09c7c7fbd046d9f"),
    "functions-article-all.json": ("data/functions/functions-article-all.json", "1c1d11ef6173208da0014b6bbb71cc8e2aa2683da9ba1ada4bf9e593fb4c7293"),
}
MODEL = "facebook/contriever-msmarco"
REVISION = "abe8c1493371369031bcb1e02acb754cf4e162fa"
WEIGHTS_SHA256 = "08b88f3a3697877345669405c51a23f53ed90aa2bab441cd7b7b08659925eef8"
MODEL_FILES = ["config.json", "pytorch_model.bin", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "vocab.txt"]


def download_model(model_dir):
    """Pinned public HTTP downloads; avoids optional Xet service hangs on Windows."""
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    base = f"https://huggingface.co/{MODEL}/resolve/{REVISION}/"
    with httpx.Client(timeout=90, follow_redirects=True) as client:
        for name in MODEL_FILES:
            if name == "pytorch_model.bin" or (model_dir / name).exists():
                continue
            response = client.get(base + name)
            response.raise_for_status()
            (model_dir / name).write_bytes(response.content)
    weights = model_dir / "pytorch_model.bin"
    if weights.exists() and sha256(weights) == WEIGHTS_SHA256:
        return
    # Fixed upstream LFS size; each range has a distinct URL to avoid proxy
    # caches returning the wrong partial range. Hash the joined file afterward.
    size, chunk_size = 438007537, 4 * 1024 * 1024
    parts = model_dir / ".download_parts"
    parts.mkdir(exist_ok=True)
    def part(start):
        end = min(start+chunk_size, size)-1
        path = parts / str(start)
        if path.exists() and path.stat().st_size == end-start+1:
            return path
        for attempt in range(3):
            try:
                r = httpx.get(base + f"pytorch_model.bin?range_start={start}", headers={"Range": f"bytes={start}-{end}"},
                              timeout=90, follow_redirects=True)
                r.raise_for_status()
                if r.status_code != 206 or r.headers.get("content-range") != f"bytes {start}-{end}/{size}" or len(r.content) != end-start+1:
                    raise ValueError("Model download returned an incorrect byte range")
                path.write_bytes(r.content)
                return path
            except (httpx.HTTPError, ValueError):
                if attempt == 2:
                    raise
    with ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(part, range(0, size, chunk_size)))
    tmp = weights.with_suffix(".download")
    with tmp.open("wb") as output:
        for path in paths:
            output.write(path.read_bytes())
    if sha256(tmp) != WEIGHTS_SHA256:
        raise ValueError("Downloaded model failed upstream SHA256 verification")
    tmp.replace(weights)
    # Only these individually known staging files, never recursive cleanup.
    for path in paths:
        path.unlink()
    parts.rmdir()


@dataclass(frozen=True)
class Problem:
    question_id: str
    question: str
    context: str


def function_description(code):
    # Some released reference functions have invalid parameter identifiers.
    # Read the literal docstring span without requiring the code to compile;
    # retain original code bytes for retrieval/judging and never execute them.
    match = re.search(r'''(?s)("""|\x27\x27\x27)(.*?)\1''', code)
    description = match.group(2) if match else None
    if not description or not description.split("Args:")[0].strip():
        raise ValueError("Library entry lacks a usable description")
    # Same description span as the author server; no execution of library code.
    return description.split("Args:")[0]


def load_inputs(data_dir):
    root = Path(data_dir)
    for name, (_, expected) in SOURCES.items():
        if sha256(root / "raw" / name) != expected:
            raise ValueError(f"Official source hash mismatch: {name}")
    rows = read_json(root / "raw/hard.json")
    functions = read_json(root / "raw/functions-article-all.json")
    if len(rows) != 238 or len(functions) != 3133:
        raise ValueError("Expected 238 Hard questions and 3133 functions")
    ids = [r["question_id"] for r in rows]
    fids = [f["function_id"] for f in functions]
    if len(set(ids)) != len(ids) or len(set(fids)) != len(fids):
        raise ValueError("Duplicate question/function identities")
    for row in rows:
        if row["level"] != "hard" or not row["question"].strip():
            raise ValueError("Invalid Hard question")
        if type(row["ground_truth"]) not in (bool, int, float) or not math.isfinite(row["ground_truth"]):
            raise ValueError("Invalid scalar ground truth")
    for function in functions:
        function_description(function["function"])
    problems = [Problem(r["question_id"], r["question"], r.get("context", "")) for r in rows]
    labels = {r["question_id"]: r["ground_truth"] for r in rows}
    return problems, labels, functions


def prepare_assets(data_dir, *, offline=False):
    root = Path(data_dir)
    for name, (relative, expected) in SOURCES.items():
        dest = root / "raw" / name
        if not dest.exists():
            if offline:
                raise FileNotFoundError(dest)
            response = httpx.get(f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{relative}", timeout=90, follow_redirects=True)
            response.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(response.content)
        if sha256(dest) != expected:
            raise ValueError(f"Source mismatch: {dest}")
    model_dir = root / "models/contriever-msmarco"
    if not all((model_dir / f).exists() for f in MODEL_FILES):
        if offline:
            raise FileNotFoundError("Pinned Contriever model is not downloaded")
        download_model(model_dir)
    if sha256(model_dir / "pytorch_model.bin") != WEIGHTS_SHA256:
        raise ValueError("Contriever weights differ from pinned upstream LFS SHA256")
    problems, labels, functions = load_inputs(root)
    lock = {
        "repository": REPO, "commit": COMMIT, "retriever": {"model": MODEL, "revision": REVISION},
        "questions": len(problems), "functions": len(functions), "question_ids": [p.question_id for p in problems],
        "boolean_labels": sum(type(v) is bool for v in labels.values()),
        "empty_contexts_preserved": sum(not p.context.strip() for p in problems),
        "adjustments": [],
        "files": {str(p.relative_to(root)).replace("\\", "/"): sha256(p) for p in
                  [root / "raw" / name for name in SOURCES] + [model_dir / f for f in MODEL_FILES]},
    }
    write_json(root / "assets.lock.json", lock)
    return lock


def verify_assets(data_dir):
    root = Path(data_dir)
    lock = read_json(root / "assets.lock.json")
    if lock["commit"] != COMMIT or lock["retriever"] != {"model": MODEL, "revision": REVISION}:
        raise ValueError("Asset provenance differs from the fixed experiment")
    expected_paths = {"raw/" + name for name in SOURCES} | {"models/contriever-msmarco/" + f for f in MODEL_FILES}
    if set(lock["files"]) != expected_paths:
        raise ValueError("Incomplete asset lock")
    for relative, expected in lock["files"].items():
        if sha256(root / relative) != expected:
            raise ValueError(f"Asset changed: {relative}")
    if lock["files"]["models/contriever-msmarco/pytorch_model.bin"] != WEIGHTS_SHA256:
        raise ValueError("Unrecognized model weights")
    problems, labels, functions = load_inputs(root)
    if lock["question_ids"] != [p.question_id for p in problems] or lock["questions"] != 238 or lock["functions"] != 3133:
        raise ValueError("Asset identities changed")
    return problems, labels, functions
