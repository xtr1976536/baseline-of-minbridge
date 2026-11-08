"""Offline test doubles for optional heavyweight model dependencies."""

import re
import sys
import types
import zlib

import numpy as np


class OfflineSentenceTransformer:
    """Small deterministic bag-of-words encoder used in place of a checkpoint."""

    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, texts, **kwargs):
        vectors = np.zeros((len(texts), 2048), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in re.findall(r"[a-z0-9]+", text.lower()):
                column = zlib.crc32(token.encode("utf-8")) % vectors.shape[1]
                vectors[row, column] += 1.0
            norm = np.linalg.norm(vectors[row])
            if norm:
                vectors[row] /= norm
        return vectors


class OfflineCrossEncoder:
    def __init__(self, model_name):
        self.model_name = model_name

    def predict(self, pairs):
        return np.zeros(len(pairs), dtype=np.float32)


# Retrieval tests validate filtering, lexical ranking, BM25, and orchestration;
# loading remote neural checkpoints would make those unit tests non-hermetic.
sentence_transformers = types.ModuleType("sentence_transformers")
sentence_transformers.SentenceTransformer = OfflineSentenceTransformer
sentence_transformers.CrossEncoder = OfflineCrossEncoder
sys.modules["sentence_transformers"] = sentence_transformers
