from __future__ import annotations
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

UPSTREAM_COMMIT = "5c49943e8aa43f3dc03c1b2058a73469b22c5c5e"
PAPER_SHA256 = "07dea58bcf91be05d310116040d062139d1f5196dd4bbc4619d7bec0e4214f16"
HF_REVISION = "1c1d5b8ff198942e7197c5b0beb9df959c3ecedc"
TAT_REVISION = "bc46208b22f0bfe47152c98fd0938d238ce868c2"
MODELS = ("Qwen2.5-7B", "Llama-3.1-8B", "Qwen3-30B", "Fin-o1-8B", "Claude-Haiku-4.5", "GPT-5.5")
DATASETS = {"XBRLFiling": 600, "FinanceBench": 67, "TAT-DQA": 403}

def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fingerprint(value):
    return hashlib.sha256(dumps(value).encode()).hexdigest()

def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s.strip()]

def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content=json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+"\n"
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False,suffix='.part') as f:
        f.write(content);temp=Path(f.name)
    for attempt in range(7):
        try:os.replace(temp,path);break
        except PermissionError:
            if attempt==6:raise
            time.sleep(.05*2**attempt)

def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(dumps(r)+"\n" for r in rows), encoding="utf-8")
