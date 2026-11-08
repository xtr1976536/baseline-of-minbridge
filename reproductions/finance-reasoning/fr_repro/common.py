from __future__ import annotations

import hashlib
import json
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_config(path):
    path = Path(path).resolve()
    config = read_json(path)
    root = path.parent.parent
    for key in ["data_dir", "output_dir", "cache_dir"]:
        config[key] = str((root / config[key]).resolve())
    r = config["retriever"]
    if config.get("judge_protocol", "labels-v1") not in {"labels-v1", "candidate-ids-v2"}:
        raise ValueError("Unrecognized function selection protocol")
    if (config["method"] != "table5-gpt4o-instructed-function-judge-pot-v1"
        or r["top_k"] != 30 or r["selected_k"] != 3
        or r["pooling"] != "masked_mean" or r["similarity"] != "inner_product"):
        raise ValueError("This runner implements only the frozen Table 5 best-method protocol")
    return config
