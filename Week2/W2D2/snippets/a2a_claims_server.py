"""Reference A2A server for the Day 2 PM A2A topic (python-a2a 0.5.10).

Fallback/reference only — the session guide asks you to have Claude Code
build this with you. Exposes one skill, check_claim_status, discoverable
via the Agent Card at GET /.well-known/agent.json, and callable via the
task/message endpoints python-a2a's A2AServer wires up automatically.

Run it:
    uv run python W2D2/snippets/a2a_claims_server.py
Card:  http://127.0.0.1:5055/.well-known/agent.json
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from python_a2a import A2AServer, AgentCard, AgentSkill, Message, MessageRole, TextContent, run_server


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


CLAIMS_DB = discover_repo_root() / "data" / "insurance" / "claims.db"

CARD = AgentCard(
    name="claims-status-agent",
    description="Reports claim status for the insurance ticket-resolution thread",
    url="http://127.0.0.1:5055",
    version="1.0.0",
    skills=[
        AgentSkill(
            name="check_claim_status",
            description="Look up a claim's status and route queue by claim_id",
            examples=["What is the status of CLM-424063?"],
        )
    ],
)


def lookup_status(claim_id: str) -> str:
    connection = sqlite3.connect(CLAIMS_DB)
    try:
        row = connection.execute(
            "SELECT status, route_queue FROM claims WHERE claim_id = ?",
            (claim_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return f"No claim found with id {claim_id}."
    status, route_queue = row
    return f"{claim_id}: status={status}, route_queue={route_queue}"


class ClaimsStatusServer(A2AServer):
    def handle_message(self, message: Message) -> Message:
        text = message.content.text if hasattr(message.content, "text") else ""
        claim_id = next((tok for tok in text.replace("?", " ").split() if tok.startswith("CLM-")), None)
        reply = lookup_status(claim_id) if claim_id else "Ask about a specific claim_id, e.g. CLM-424063."
        return Message(
            content=TextContent(text=reply),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )


if __name__ == "__main__":
    run_server(ClaimsStatusServer(agent_card=CARD), host="127.0.0.1", port=5055)
