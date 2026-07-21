"""Day 3 -- GraphRAG fraud-connection signal, adapted from
W2D3/snippets/graphrag_traversal.py.

Run it:
    uv run python -m app.graph_signals CLM-424063
"""

from __future__ import annotations

import json
import sys

import networkx as nx

from app.paths import CLAIMS_KG


def load_graph() -> nx.DiGraph:
    payload = json.loads(CLAIMS_KG.read_text(encoding="utf-8"))
    graph = nx.DiGraph()
    for node in payload["nodes"]:
        graph.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
    for edge in payload["edges"]:
        graph.add_edge(edge["source"], edge["target"], relation=edge["relation"])
    return graph


def same_address_claims(graph: nx.DiGraph, claim_id: str) -> list[str]:
    """2-hop traversal: claim -> address -> other claims at that address.

    The knowledge-graph fixture only covers a demo subset of claims.db
    (it exists to teach the traversal, not to mirror every row) -- a
    claim_id absent from the graph has no fraud signal available, not an
    error, so this returns [] rather than raising.
    """
    if claim_id not in graph:
        return []
    addresses = [t for t in graph.successors(claim_id) if graph.nodes[t].get("type") == "address"]
    if not addresses:
        return []
    address = addresses[0]
    return [s for s in graph.predecessors(address) if s != claim_id]


def claimant_of(graph: nx.DiGraph, claim_id: str) -> str | None:
    if claim_id not in graph:
        return None
    for policy in graph.predecessors(claim_id):
        for claimant in graph.predecessors(policy):
            if graph.nodes[claimant].get("type") == "claimant":
                return claimant
    return None


def main() -> None:
    claim_id = sys.argv[1] if len(sys.argv) > 1 else "CLM-424063"
    graph = load_graph()
    matches = same_address_claims(graph, claim_id)
    print(f"Claimant of {claim_id}: {claimant_of(graph, claim_id)}")
    if not matches:
        print(f"No other claims found at the same address as {claim_id}.")
        return
    for other_id in matches:
        print(
            f"MULTI-HOP SIGNAL: {other_id} (claimant: {claimant_of(graph, other_id)}) "
            f"shares an address with {claim_id} (claimant: {claimant_of(graph, claim_id)}) "
            f"-- flag for special_investigations review."
        )


if __name__ == "__main__":
    main()
