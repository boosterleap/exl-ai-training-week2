"""Day 3 -- adds grounded coverage retrieval + a fraud signal on top of Day 2.

For any claim where grounding_available is true:
  1. Build (or reuse) a chunk -> embed -> LanceDB index over
     data/insurance/policies/*.md only (not logistics).
  2. Search it for a coverage question about the claim's own loss_type,
     restricted -- via a LanceDB metadata pre-filter, before the vector
     search runs -- to ONLY that claim's own resolved policy_doc_files.
     A different product's document is never even a candidate.
  3. An exact-then-semantic cache sits in front of that search, hard-
     partitioned by the claim's product (a namespace argument on
     get/set) so a cache hit can never cross from one product to another,
     regardless of how similar two questions from different products
     happen to embed.
  4. A same-address fraud signal: load the Day 3 AM claims knowledge graph
     and check whether this claim's address is shared by any other claim
     (the same 2-hop traversal as W2D3/snippets/graphrag_traversal.py).

Run it:
    uv run python -m app.my_day3_resolve CLN-001
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import lancedb
import numpy as np

from app.my_day2_resolve import resolve_email as day2_resolve_email

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "W2D3" / "snippets"))
from graphrag_traversal import claimant_of, load_graph, same_address_claims  # noqa: E402
from rag_index import chunk_markdown, embedder, reranker  # noqa: E402  (reuse embed/rerank models)

INSURANCE_POLICIES_DIR = REPO_ROOT / "data" / "insurance" / "policies"
DB_PATH = REPO_ROOT / "app" / "outputs" / "lancedb_insurance_policies"
TABLE_NAME = "insurance_policy_chunks"

CACHE_DIR = REPO_ROOT / "app" / "outputs" / "coverage_cache"
SIMILARITY_THRESHOLD = 0.85


def build_or_reuse_index() -> "lancedb.table.Table":
    """Chunk -> embed -> LanceDB, over data/insurance/policies/*.md only -- built once, reused after."""
    db = lancedb.connect(str(DB_PATH))
    if TABLE_NAME in db.table_names():
        return db.open_table(TABLE_NAME)

    all_chunks = []
    for md_file in sorted(INSURANCE_POLICIES_DIR.glob("*.md")):
        all_chunks.extend(chunk_markdown(md_file))
    vectors = embedder().encode([c["text"] for c in all_chunks]).tolist()
    rows = [{"vector": v, **c} for v, c in zip(vectors, all_chunks)]
    return db.create_table(TABLE_NAME, data=rows, mode="overwrite")


def search_within_docs(query: str, allowed_source_files: list[str], k: int = 3) -> list[dict]:
    """Vector search + rerank, pre-filtered (before the vector search runs) to
    ONLY allowed_source_files -- never a document from a different product."""
    table = build_or_reuse_index()
    qvec = embedder().encode([query])[0].tolist()
    clause = " OR ".join(f"source_file = '{name}'" for name in allowed_source_files)
    candidates = table.search(qvec).where(clause, prefilter=True).limit(k * 3).to_list()
    if not candidates:
        return []
    pairs = [(query, c["text"]) for c in candidates]
    scores = reranker().predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda pair: -pair[1])[:k]
    return [
        {"source_file": c["source_file"], "heading": c["heading"], "text": c["text"], "rerank_score": float(s)}
        for c, s in ranked
    ]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class NamespacedCoverageCache:
    """Exact-then-semantic cache, hard-partitioned by namespace (product) --
    a hit in one product's namespace can never answer a query in another's,
    no matter how similar the two questions embed."""

    def __init__(self, cache_dir: Path = CACHE_DIR) -> None:
        import diskcache

        self._exact = diskcache.Cache(str(cache_dir / "exact"))
        self._semantic_entries: list[tuple[str, str, np.ndarray, dict]] = []  # (namespace, query, vector, response)

    def get(self, query: str, namespace: str) -> tuple[dict | None, str]:
        exact_key = (namespace, query)
        if exact_key in self._exact:
            return self._exact[exact_key], "exact"
        query_vec = embedder().encode([query])[0]
        best_sim, best_response = 0.0, None
        for entry_ns, _cached_query, cached_vec, response in self._semantic_entries:
            if entry_ns != namespace:
                continue
            sim = _cosine(query_vec, cached_vec)
            if sim > best_sim:
                best_sim, best_response = sim, response
        if best_sim >= SIMILARITY_THRESHOLD:
            return best_response, "semantic"
        return None, "miss"

    def set(self, query: str, response: dict, namespace: str) -> None:
        exact_key = (namespace, query)
        self._exact.set(exact_key, response, expire=3600)
        self._semantic_entries.append((namespace, query, embedder().encode([query])[0], response))


_cache = NamespacedCoverageCache()


def answer_coverage_question(loss_type: str, product: str, policy_doc_files: list[str]) -> dict:
    question = f"Is {loss_type} damage covered under this policy?"
    cached, layer = _cache.get(question, namespace=product)
    if cached is not None:
        return {
            "coverage_question": question,
            "coverage_answer_source": f"{cached['source_file']} :: {cached['heading']} (cache={layer})",
            "coverage_excerpt": cached["text"],
        }

    hits = search_within_docs(question, allowed_source_files=policy_doc_files, k=3)
    if not hits:
        return {
            "coverage_question": question,
            "coverage_answer_source": None,
            "coverage_excerpt": None,
        }

    top = hits[0]
    _cache.set(question, top, namespace=product)
    return {
        "coverage_question": question,
        "coverage_answer_source": f"{top['source_file']} :: {top['heading']} (cache=miss)",
        "coverage_excerpt": top["text"],
    }


def build_fraud_signal(claim_id: str) -> str:
    graph = load_graph()
    matches = same_address_claims(graph, claim_id)
    if not matches:
        return f"No other claims found at the same address as {claim_id}."
    this_claimant = claimant_of(graph, claim_id)
    return " ".join(
        f"MULTI-HOP SIGNAL: {other_id} (claimant: {claimant_of(graph, other_id)}) "
        f"shares an address with {claim_id} (claimant: {this_claimant}) -- "
        "flag for special_investigations review."
        for other_id in matches
    )


def resolve_email(email_id: str) -> dict[str, object]:
    result = day2_resolve_email(email_id)
    claim_id = result.get("claim_id")
    if not claim_id:
        return result

    network_check = result.get("network_grounding_check")
    if not network_check or not network_check.get("grounding_available"):
        return result

    coverage = answer_coverage_question(
        loss_type=network_check["loss_type"],
        product=network_check["product"],
        policy_doc_files=network_check["policy_doc_files"],
    )
    result.update(coverage)
    result["fraud_signal"] = build_fraud_signal(claim_id)
    return result


def main() -> None:
    email_id = sys.argv[1] if len(sys.argv) > 1 else "CLN-001"
    print(json.dumps(resolve_email(email_id), indent=2))


if __name__ == "__main__":
    main()
