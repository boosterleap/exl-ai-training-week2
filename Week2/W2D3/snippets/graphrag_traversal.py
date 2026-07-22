"""Reference GraphRAG traversal for Day 3 AM Topic 03.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified: a 2-hop traversal from CLM-424063 through
its address correctly surfaces CLM-100234 -- a different claimant, same
address -- a connection plain text/vector search over claim content would
not find (see data/insurance/claims_kg.json for why this fixture exists).

Run it:
    uv run python W2D3/snippets/graphrag_traversal.py CLM-424063
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


KG_PATH = discover_repo_root() / "data" / "insurance" / "claims_kg.json"


def load_graph() -> nx.DiGraph:
    payload = json.loads(KG_PATH.read_text(encoding="utf-8"))
    graph = nx.DiGraph()
    for node in payload["nodes"]:
        graph.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
    for edge in payload["edges"]:
        graph.add_edge(edge["source"], edge["target"], relation=edge["relation"])
    return graph


def same_address_claims(graph: nx.DiGraph, claim_id: str) -> list[str]:
    """2-hop traversal: claim -> address -> other claims at that address."""
    addresses = [t for t in graph.successors(claim_id) if graph.nodes[t].get("type") == "address"]
    if not addresses:
        return []
    address = addresses[0]
    return [s for s in graph.predecessors(address) if s != claim_id]


def claimant_of(graph: nx.DiGraph, claim_id: str) -> str | None:
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
