"""Official Contriever mean pooling and exhaustive (exact) inner-product search."""
from pathlib import Path

import numpy as np

from .assets import MODEL, REVISION, function_description
from .common import digest, read_json, sha256, write_json


def mean_pool(hidden, mask):
    return hidden.masked_fill(~mask[..., None].bool(), 0.0).sum(dim=1) / mask.sum(dim=1)[..., None]


class Contriever:
    def __init__(self, data_dir, config):
        import torch
        from transformers import AutoModel, AutoTokenizer
        if config["model"] != MODEL or config["revision"] != REVISION:
            raise ValueError("Unexpected Contriever snapshot")
        self.torch = torch
        torch.set_num_threads(config.get("cpu_threads", 4))
        self.config = config
        model_dir = Path(data_dir) / "models/contriever-msmarco"
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        self.model = AutoModel.from_pretrained(model_dir, local_files_only=True, use_safetensors=False).eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def encode(self, texts):
        arrays = []
        batch_size = self.config.get("batch_size", 16)
        with self.torch.inference_mode():
            for start in range(0, len(texts), batch_size):
                batch = self.tokenizer(texts[start:start+batch_size], padding=True, truncation=True,
                                       max_length=self.config["max_length"], return_tensors="pt").to(self.device)
                hidden = self.model(**batch).last_hidden_state
                arrays.append(mean_pool(hidden, batch["attention_mask"]).cpu().numpy().astype("float32"))
        return np.concatenate(arrays)


def index_identity(data_dir, functions, config):
    return digest({"asset_lock": sha256(Path(data_dir) / "assets.lock.json"),
                   "descriptions": [function_description(f["function"]) for f in functions],
                   "ids": [f["function_id"] for f in functions],
                   "encoder": {k: config[k] for k in ["model", "revision", "pooling", "similarity", "max_length"]},
                   "implementation": sha256(Path(__file__))})


def build_index(data_dir, functions, config):
    root = Path(data_dir) / "index"
    root.mkdir(parents=True, exist_ok=True)
    identity = index_identity(data_dir, functions, config)
    if (root / "manifest.json").exists():
        verify_index(data_dir, functions, config)
        return read_json(root / "manifest.json")
    encoder = Contriever(data_dir, config)
    texts = [function_description(f["function"]) for f in functions]
    vectors = encoder.encode(texts)
    if vectors.shape != (len(functions), 768) or not np.isfinite(vectors).all():
        raise ValueError("Invalid Contriever vectors")
    np.save(root / "embeddings.npy", vectors, allow_pickle=False)
    token_lengths = [len(encoder.tokenizer.encode(t, add_special_tokens=True, truncation=False)) for t in texts]
    manifest = {"identity": identity, "count": len(functions), "dimensions": 768,
                "embedding_sha256": sha256(root / "embeddings.npy"), "device": str(encoder.device),
                "descriptions_truncated": sum(n > config["max_length"] for n in token_lengths),
                "max_description_tokens": max(token_lengths), "pooling": "masked_mean", "similarity": "inner_product"}
    write_json(root / "manifest.json", manifest)
    return manifest


def verify_index(data_dir, functions, config):
    root = Path(data_dir) / "index"
    meta = read_json(root / "manifest.json")
    if meta["identity"] != index_identity(data_dir, functions, config):
        raise ValueError("Retrieval configuration/assets/code changed; rebuild data/index")
    if sha256(root / "embeddings.npy") != meta["embedding_sha256"]:
        raise ValueError("Retrieval embeddings changed")
    vectors = np.load(root / "embeddings.npy", allow_pickle=False)
    if vectors.shape != (len(functions), 768) or not np.isfinite(vectors).all():
        raise ValueError("Corrupt index")
    return vectors


class FunctionRetriever:
    def __init__(self, data_dir, functions, config):
        self.functions = functions
        self.vectors = verify_index(data_dir, functions, config)
        self.encoder = Contriever(data_dir, config)

    def search(self, query, k=30):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Empty retrieval query")
        embedding = self.encoder.encode([query])[0]
        scores = self.vectors @ embedding
        # Stable source order for exact ties; no score or label based tuning.
        indices = np.argsort(-scores, kind="stable")[:k]
        return [{**self.functions[int(i)], "score": float(scores[i])} for i in indices]
