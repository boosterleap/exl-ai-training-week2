"""Phase 3 reference: expose tools.py's two functions as a real network MCP
server (Streamable HTTP), mirroring W2D2/my_claims_network_server.py's
pattern exactly -- a standalone service Claude Code (or any MCP client)
connects to over a port, not an in-process import.

Run it (separate terminal):
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" W2D0/capstone_ref/mcp_loan_server.py
Endpoint: http://127.0.0.1:8770/mcp

Self-check (verifies the underlying logic without needing a live MCP client):
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" W2D0/capstone_ref/mcp_loan_server.py --self-check
"""
from __future__ import annotations

import sys
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP

from tools import get_loan_record, search_policy

mcp = FastMCP(
    "loan-lookup",
    instructions=(
        "Read-only lookup for bank loan applications and their grounding "
        "underwriting policy documents. Never invents a loan record or a "
        "policy term that does not exist in the underlying data."
    ),
    host="127.0.0.1",
    port=8770,
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


@mcp.tool()
def get_loan_record_tool(loan_id: str) -> dict:
    """Look up a loan application and report which policy doc (if any) grounds it.

    If grounding_available is false, no policy document exists for this
    product -- do not answer an eligibility/coverage question from general
    knowledge; escalate instead.
    """
    normalized = loan_id.strip().upper()
    if not normalized:
        raise ValueError("loan_id must be a non-empty Loan_ID, e.g. LP002305.")
    return asdict(get_loan_record(normalized))


@mcp.tool()
def search_policy_tool(query: str, product: str | None = None, k: int = 3) -> list[dict]:
    """Semantic search over underwriting policy docs, scoped to one product."""
    return search_policy(query, k=k, product=product)


def self_check() -> dict[str, object]:
    grounded = asdict(get_loan_record("LP002305"))
    ungrounded = asdict(get_loan_record("LP002448"))  # gold_loan -- deliberate gap
    hits = search_policy("is there a surcharge for rural properties", product="home_loan")
    return {
        "ok": True,
        "server": "loan-lookup",
        "transport": "streamable-http",
        "endpoint": "http://127.0.0.1:8770/mcp",
        "grounded_lookup": grounded,
        "deliberate_gap_lookup": ungrounded,
        "sample_search_top_heading": hits[0]["heading"] if hits else None,
    }


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        import json

        print(json.dumps(self_check(), indent=2))
    else:
        mcp.run(transport="streamable-http")
