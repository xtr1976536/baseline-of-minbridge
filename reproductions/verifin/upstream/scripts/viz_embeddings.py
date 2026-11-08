"""
Visualize corpus chunk embeddings with t-SNE (or UMAP if installed).

Usage:
    python3 scripts/viz_embeddings.py \
        --corpus data/corpus \
        --out plots/embeddings.png \
        --sample 100          # chunks per company
"""
from __future__ import annotations

import argparse
import random
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sentence_transformers import SentenceTransformer


def load_chunks(corpus_dir: Path):
    import json
    chunks = []
    with (corpus_dir / "corpus_chunks.jsonl").open() as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def sample_chunks(chunks, n_per_doc: int, seed: int = 42):
    by_doc = defaultdict(list)
    for c in chunks:
        by_doc[c["doc_name"]].append(c)
    rng = random.Random(seed)
    sampled = []
    for doc, doc_chunks in sorted(by_doc.items()):
        sampled.extend(rng.sample(doc_chunks, min(n_per_doc, len(doc_chunks))))
    return sampled


def company_from_doc(doc_name: str) -> str:
    return doc_name.split("_")[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("data/corpus"))
    parser.add_argument("--out", type=Path, default=Path("plots/embeddings.png"))
    parser.add_argument("--sample", type=int, default=100, help="chunks per doc")
    parser.add_argument("--model", default="BAAI/bge-large-en-v1.5")
    parser.add_argument("--method", choices=["tsne", "umap"], default="tsne")
    args = parser.parse_args()

    print("Loading corpus...")
    all_chunks = load_chunks(args.corpus)
    print(f"  {len(all_chunks)} total chunks")

    sampled = sample_chunks(all_chunks, args.sample)
    print(f"  {len(sampled)} sampled chunks across {len({c['doc_name'] for c in sampled})} docs")

    texts = [c["text"] for c in sampled]
    prefix = "Represent this sentence for searching relevant passages: "
    queries = [prefix + t for t in texts]

    print(f"Encoding with {args.model}...")
    model = SentenceTransformer(args.model)
    embeddings = model.encode(queries, batch_size=64, show_progress_bar=True, normalize_embeddings=True)

    print(f"Reducing with {args.method}...")
    if args.method == "umap":
        import umap
        reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
    else:
        from sklearn.manifold import TSNE
        reducer = TSNE(n_components=2, random_state=42, perplexity=40, n_iter=1000)
    coords = reducer.fit_transform(embeddings)

    companies = [company_from_doc(c["doc_name"]) for c in sampled]
    unique_companies = sorted(set(companies))
    cmap = plt.get_cmap("tab20")
    color_map = {co: cmap(i / max(len(unique_companies) - 1, 1)) for i, co in enumerate(unique_companies)}
    colors = [color_map[co] for co in companies]

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.scatter(coords[:, 0], coords[:, 1], c=colors, s=8, alpha=0.6, linewidths=0)

    # Legend (one entry per company)
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=color_map[co],
                   markersize=7, label=co)
        for co in unique_companies
    ]
    ax.legend(handles=handles, bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=7, frameon=False, ncol=1)

    ax.set_title(f"Corpus embeddings ({args.method.upper()}, {len(sampled)} chunks, {len(unique_companies)} companies)")
    ax.set_xlabel("dim 1")
    ax.set_ylabel("dim 2")
    ax.axis("off")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    print(f"Saved → {args.out}")


if __name__ == "__main__":
    main()
