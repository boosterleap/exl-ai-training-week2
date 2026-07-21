"""Day 3 -- exact + semantic cache in front of the RAG grounding lookup.

Adapted from W2D3/snippets/semantic_cache.py: reuses app.rag_index's
embedder() singleton instead of loading a second copy of the same model.

Run it:
    uv run python -m app.semantic_cache
"""

from __future__ import annotations

from pathlib import Path

import diskcache
import numpy as np

from app.paths import APP_OUTPUTS_DIR
from app.rag_index import embedder

SIMILARITY_THRESHOLD = 0.85
CACHE_DIR = APP_OUTPUTS_DIR / "response_cache"


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class ExactThenSemanticCache:
    """Checks an exact-match cache first, then a semantic-similarity cache.

    Every entry is hard-partitioned by `namespace` (this app passes the
    claim's product, e.g. "homeowners"). Semantic similarity is a soft,
    approximate match -- without a hard namespace boundary, a paraphrased
    question about one product could accidentally return a cached answer
    grounded in a *different* product's policy, which is exactly the kind
    of wrong-document grounding this course's data rules exist to prevent.
    """

    def __init__(self, cache_dir: Path = CACHE_DIR) -> None:
        self._exact = diskcache.Cache(str(cache_dir / "exact"))
        self._semantic_entries: list[tuple[str, str, np.ndarray, str]] = []  # (namespace, query, vector, response)

    def get(self, namespace: str, query: str) -> tuple[str | None, str]:
        """Returns (response_or_None, layer) where layer is exact/semantic/miss."""
        exact_key = f"{namespace}::{query}"
        if exact_key in self._exact:
            return self._exact[exact_key], "exact"
        query_vec = embedder().encode([query])[0]
        best_sim, best_response = 0.0, None
        for cached_namespace, cached_query, cached_vec, response in self._semantic_entries:
            if cached_namespace != namespace:
                continue
            sim = _cosine(query_vec, cached_vec)
            if sim > best_sim:
                best_sim, best_response = sim, response
        if best_sim >= SIMILARITY_THRESHOLD:
            return best_response, "semantic"
        return None, "miss"

    def set(self, namespace: str, query: str, response: str) -> None:
        self._exact.set(f"{namespace}::{query}", response, expire=3600)
        self._semantic_entries.append((namespace, query, embedder().encode([query])[0], response))


if __name__ == "__main__":
    cache = ExactThenSemanticCache()
    cache.set("homeowners", "is a burst pipe covered", "Yes, up to USD 10,000 after the USD 1,000 deductible.")

    for namespace, query in [
        ("homeowners", "is a burst pipe covered"),   # exact match
        ("homeowners", "is my burst pipe covered"),  # paraphrase, same product -> semantic hit
        ("auto", "is my burst pipe covered"),        # same wording, different product -> must miss
        ("homeowners", "what is the weather today"), # unrelated -> miss
    ]:
        response, layer = cache.get(namespace, query)
        print(f"{layer:9s} | ({namespace}) {query!r} -> {response}")
