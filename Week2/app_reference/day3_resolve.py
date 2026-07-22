"""Day 3 -- adds real policy grounding, a cache in front of it, and a
fraud-connection signal on top of Day 2.

Where Day 1 only checked *whether* a policy document exists, this stage
actually answers the coverage question: RAG-search the indexed policy
corpus for the claim's loss type, cache the answer (exact, then semantic),
and cross-check the claims knowledge graph for a same-address connection
to another claim -- a signal plain text search over one claim's content
would never surface.

Run it:
    uv run python -m app.day3_resolve CLN-001
"""

from __future__ import annotations

import json
import sys

from app.day2_resolve import resolve_email as day2_resolve_email
from app.graph_signals import claimant_of, load_graph, same_address_claims
from app.rag_index import DB_PATH, TABLE_NAME, build_index, search
from app.semantic_cache import ExactThenSemanticCache

_cache: ExactThenSemanticCache | None = None
_graph = None


def _get_cache() -> ExactThenSemanticCache:
    global _cache
    if _cache is None:
        _cache = ExactThenSemanticCache()
    return _cache


def _get_graph():
    global _graph
    if _graph is None:
        _graph = load_graph()
    return _graph


def _ensure_index_built() -> None:
    import lancedb

    db = lancedb.connect(str(DB_PATH))
    if TABLE_NAME not in db.list_tables():
        build_index()


def _coverage_question(claim: dict) -> str:
    return f"is {claim['loss_type']} damage covered"


def resolve_email(email_id: str) -> dict[str, object]:
    result = day2_resolve_email(email_id)
    claim_id = result.get("claim_id")
    if not claim_id or not result.get("found"):
        return result

    claim = result["claim"]
    if claim["grounding_available"]:
        _ensure_index_built()
        question = _coverage_question(claim)
        cache = _get_cache()
        cached, layer = cache.get(claim["product"], question)
        if cached is not None:
            answer = cached
            source = layer  # "exact" or "semantic"
        else:
            hits = search(question, k=3, allowed_files=set(claim["policy_doc_files"]))
            top = hits[0] if hits else None
            answer = top["text"] if top else None
            source = "rag_search"
            if answer:
                cache.set(claim["product"], question, answer)
        result["coverage_question"] = question
        result["coverage_answer_source"] = source
        result["coverage_excerpt"] = answer

    graph = _get_graph()
    same_address = same_address_claims(graph, claim_id)
    result["fraud_signal"] = {
        "claimant": claimant_of(graph, claim_id),
        "same_address_claim_ids": same_address,
        "flag": bool(same_address),
    }
    return result


def main() -> None:
    email_id = sys.argv[1] if len(sys.argv) > 1 else "CLN-001"
    print(json.dumps(resolve_email(email_id), indent=2))


if __name__ == "__main__":
    main()
