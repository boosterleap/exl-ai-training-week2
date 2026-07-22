"""Reference exact + semantic cache for Day 3 PM Topic 05.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified: a paraphrased query ("is my burst pipe
covered" vs. cached "is a burst pipe covered") scores ~0.95 cosine
similarity (hit); an unrelated query scores ~0.07 (miss).

Run it:
    uv run python W2D3/snippets/semantic_cache.py
"""

from __future__ import annotations

from pathlib import Path

import diskcache
import numpy as np
from sentence_transformers import SentenceTransformer

SIMILARITY_THRESHOLD = 0.85


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


CACHE_DIR = discover_repo_root() / "W2D3" / "outputs" / "response_cache"
_embedder: SentenceTransformer | None = None


def embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class ExactThenSemanticCache:
    """Checks an exact-match cache first, then a semantic-similarity cache."""

    def __init__(self, cache_dir: Path = CACHE_DIR) -> None:
        self._exact = diskcache.Cache(str(cache_dir / "exact"))
        self._semantic_entries: list[tuple[str, np.ndarray, str]] = []  # (query, vector, response)

    def get(self, query: str) -> tuple[str | None, str]:
        """Returns (response_or_None, layer) where layer is exact/semantic/miss."""
        if query in self._exact:
            return self._exact[query], "exact"
        query_vec = embedder().encode([query])[0]
        best_sim, best_response = 0.0, None
        for cached_query, cached_vec, response in self._semantic_entries:
            sim = _cosine(query_vec, cached_vec)
            if sim > best_sim:
                best_sim, best_response = sim, response
        if best_sim >= SIMILARITY_THRESHOLD:
            return best_response, "semantic"
        return None, "miss"

    def set(self, query: str, response: str) -> None:
        self._exact.set(query, response, expire=3600)
        self._semantic_entries.append((query, embedder().encode([query])[0], response))


if __name__ == "__main__":
    cache = ExactThenSemanticCache()
    cache.set("is a burst pipe covered", "Yes, up to USD 10,000 after the USD 1,000 deductible.")

    for query in [
        "is a burst pipe covered",           # exact match
        "is my burst pipe covered",           # paraphrase -> semantic hit
        "what is the weather today",          # unrelated -> miss
    ]:
        response, layer = cache.get(query)
        print(f"{layer:9s} | {query!r} -> {response}")
