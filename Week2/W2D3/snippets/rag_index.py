"""Reference agentic-RAG retrieval pipeline for Day 3 AM.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified end to end against the real repo data:
chunk-by-heading -> embed (384-d, all-MiniLM-L6-v2) -> LanceDB (embedded,
no server) -> hybrid rerank with a cross-encoder.

Run it:
    uv run python W2D3/snippets/rag_index.py
"""

from __future__ import annotations

import re
from pathlib import Path

import lancedb
from sentence_transformers import CrossEncoder, SentenceTransformer


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


REPO_ROOT = discover_repo_root()
POLICIES_DIRS = [REPO_ROOT / "data" / "insurance" / "policies", REPO_ROOT / "data" / "logistics" / "policies"]
DB_PATH = REPO_ROOT / "W2D3" / "outputs" / "lancedb_policies"
TABLE_NAME = "policy_chunks"

_embedder: SentenceTransformer | None = None
_reranker: CrossEncoder | None = None


def embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


def chunk_markdown(path: Path) -> list[dict]:
    """Split a policy doc into chunks at each ## heading, preserving provenance."""
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading = section.splitlines()[0].lstrip("# ").strip()
        chunks.append({"text": section, "heading": heading, "source_file": path.name})
    return chunks


def build_index() -> "lancedb.table.Table":
    all_chunks = []
    for directory in POLICIES_DIRS:
        for md_file in sorted(directory.glob("*.md")):
            all_chunks.extend(chunk_markdown(md_file))
    vectors = embedder().encode([c["text"] for c in all_chunks]).tolist()
    rows = [{"vector": v, **c} for v, c in zip(vectors, all_chunks)]
    db = lancedb.connect(str(DB_PATH))
    table = db.create_table(TABLE_NAME, data=rows, mode="overwrite")
    return table


def search(query: str, k: int = 5) -> list[dict]:
    """Vector search, then cross-encoder rerank -- returns the top k, best first."""
    db = lancedb.connect(str(DB_PATH))
    table = db.open_table(TABLE_NAME)
    qvec = embedder().encode([query])[0].tolist()
    candidates = table.search(qvec).limit(k * 3).to_list()
    pairs = [(query, c["text"]) for c in candidates]
    scores = reranker().predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda pair: -pair[1])[:k]
    return [
        {"source_file": c["source_file"], "heading": c["heading"], "text": c["text"], "rerank_score": float(s)}
        for c, s in ranked
    ]


if __name__ == "__main__":
    table = build_index()
    print(f"Indexed {table.count_rows()} chunks from {len(POLICIES_DIRS)} policy directories.\n")
    for query in ["is a burst pipe covered", "what happens if my ocean shipment is delayed"]:
        print("Q:", query)
        for hit in search(query, k=3):
            print(f"   {hit['rerank_score']:6.2f}  {hit['source_file']} :: {hit['heading']}")
        print()
