"""Day 3 -- chunk -> embed -> LanceDB -> cross-encoder rerank over the
insurance policy corpus.

Adapted from W2D3/snippets/rag_index.py for the progressive app: scoped to
data/insurance/policies only (the original also indexed the logistics
corpus, out of scope for this insurance-only app), sharing one embedder
singleton with semantic_cache.py instead of each maintaining its own.

Run it:
    uv run python -m app.rag_index
"""

from __future__ import annotations

import re
from pathlib import Path

import lancedb
from sentence_transformers import CrossEncoder, SentenceTransformer

from app.paths import APP_OUTPUTS_DIR, POLICIES_DIR

DB_PATH = APP_OUTPUTS_DIR / "lancedb_policies"
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
    for md_file in sorted(POLICIES_DIR.glob("*.md")):
        all_chunks.extend(chunk_markdown(md_file))
    vectors = embedder().encode([c["text"] for c in all_chunks]).tolist()
    rows = [{"vector": v, **c} for v, c in zip(vectors, all_chunks)]
    db = lancedb.connect(str(DB_PATH))
    table = db.create_table(TABLE_NAME, data=rows, mode="overwrite")
    return table


def search(query: str, k: int = 5, allowed_files: set[str] | None = None) -> list[dict]:
    """Vector search, then cross-encoder rerank -- returns the top k, best first.

    allowed_files, when given, restricts results to those source files --
    e.g. the specific claim's own policy_doc_files, so a coverage answer
    can never be grounded in a different product's policy by mistake.
    """
    db = lancedb.connect(str(DB_PATH))
    table = db.open_table(TABLE_NAME)
    qvec = embedder().encode([query])[0].tolist()
    candidates = table.search(qvec).limit(k * 10 if allowed_files else k * 3).to_list()
    if allowed_files is not None:
        candidates = [c for c in candidates if c["source_file"] in allowed_files]
    if not candidates:
        return []
    pairs = [(query, c["text"]) for c in candidates]
    scores = reranker().predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda pair: -pair[1])[:k]
    return [
        {"source_file": c["source_file"], "heading": c["heading"], "text": c["text"], "rerank_score": float(s)}
        for c, s in ranked
    ]


if __name__ == "__main__":
    table = build_index()
    print(f"Indexed {table.count_rows()} chunks from {POLICIES_DIR}.\n")
    for query in ["is a burst pipe covered", "what is excluded under the auto policy"]:
        print("Q:", query)
        for hit in search(query, k=3):
            print(f"   {hit['rerank_score']:6.2f}  {hit['source_file']} :: {hit['heading']}")
        print()
