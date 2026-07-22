"""Day 3 -- stdio MCP server exposing the rag_index.py policy search.

Wraps snippets/rag_index.py's search() (vector search -> cross-encoder
rerank over the LanceDB policy_chunks table) as a single MCP tool. The
index itself is built separately -- run snippets/rag_index.py once first
to create W2D3/outputs/lancedb_policies before using this tool.

Run a syntax/self-check directly:
    python W2D3/my_policy_search_server.py --self-check
"""

from __future__ import annotations

import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict

sys.path.insert(0, str(Path(__file__).resolve().parent / "snippets"))
from rag_index import DB_PATH, search  # noqa: E402

# product -> policy document prefix under data/{insurance,logistics}/policies/.
PRODUCT_PREFIXES: dict[str, str] = {
    "auto": "POL-AUTO-001",
    "homeowners": "POL-HOME-010",
    "commercial_property": "POL-COMM-030",
    "landlord_liability": "POL-LL-040",
    "health": "POL-HEALTH-020",
    "ocean_freight": "OCEAN-SLA-001",
    "rail_freight": "RAIL-SLA-002",
    "cargo_claims": "CARGO-CLAIM-010",
}

# Default-deny: a role not listed here gets zero products, not "all".
ROLE_ALLOWED_PRODUCTS: dict[str, list[str]] = {
    "claims_adjuster": list(PRODUCT_PREFIXES),
    "auto_specialist": ["auto", "homeowners"],
}

mcp = FastMCP(
    "policy-search",
    instructions=(
        "Semantic search over insurance and logistics policy documents. "
        "Returns the top-k grounding chunks (source file, heading, text) "
        "for a natural-language query -- never invents policy language "
        "that isn't in a returned chunk."
    ),
)


class PolicyChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_file: str
    heading: str
    text: str
    rerank_score: float


@mcp.tool()
def search_policies(query: str, role: str, k: int = 5) -> list[PolicyChunk]:
    """Search indexed policy documents and return the top k grounding chunks, best first.

    role is required and checked against a default-deny permission matrix
    (ROLE_ALLOWED_PRODUCTS): any role not explicitly listed there gets zero
    products, not "all". The allowed products' document prefixes are applied
    as a LanceDB metadata pre-filter (prefilter=True) BEFORE the vector search
    runs, so disallowed documents are never even candidates -- not filtered
    out of results after the fact.

    Requires the LanceDB index to already exist (run snippets/rag_index.py
    once to build it). Each result cites its source_file and heading --
    use those for citation, don't paraphrase coverage claims beyond what
    the returned text says.
    """
    query = query.strip()
    if not query:
        raise ValueError("query must be a non-empty search string.")
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"LanceDB index not found at {DB_PATH}. Run "
            "W2D3/snippets/rag_index.py once to build it."
        )
    allowed_products = ROLE_ALLOWED_PRODUCTS.get(role, [])
    if not allowed_products:
        raise PermissionError(
            f"role {role!r} is not permitted to search any policy products "
            "(default-deny: role not in ROLE_ALLOWED_PRODUCTS)."
        )
    prefixes = [PRODUCT_PREFIXES[product] for product in allowed_products]
    return [PolicyChunk(**hit) for hit in search(query, k=k, source_prefixes=prefixes)]


def self_check() -> dict[str, object]:
    sample = search_policies("is a burst pipe covered", role="claims_adjuster", k=3)
    return {
        "ok": True,
        "server": "policy-search",
        "transport": "stdio",
        "db_path": str(DB_PATH),
        "sample_search": [hit.model_dump() for hit in sample],
    }


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        import json

        print(json.dumps(self_check(), indent=2))
    else:
        mcp.run()
