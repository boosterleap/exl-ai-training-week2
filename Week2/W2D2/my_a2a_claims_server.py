"""Day 2 -- standalone A2A server (python_a2a) named claims-status-agent.

Exposes one skill, check_claim_status, that looks up a claim_id's status
and route_queue in data/insurance/claims.db. Read-only, no invented facts:
an unknown claim_id gets an explicit "not found" error, never a guess.

Run it (separate terminal):
    uv run python W2D2/my_a2a_claims_server.py
Endpoint: http://127.0.0.1:5055/a2a
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from python_a2a import (
    A2AServer,
    AgentCard,
    AgentSkill,
    ErrorContent,
    FunctionResponseContent,
    Message,
    MessageRole,
    TextContent,
    run_server,
)


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


REPO_ROOT = discover_repo_root()
CLAIMS_DB = REPO_ROOT / "data" / "insurance" / "claims.db"
HOST = "127.0.0.1"
PORT = 5055


def lookup_claim_status(claim_id: str) -> dict[str, object] | None:
    """Read-only lookup of a claim's status/route_queue. None if not found."""
    if not CLAIMS_DB.is_file():
        raise FileNotFoundError(f"claims.db not found at {CLAIMS_DB}")
    connection = sqlite3.connect(CLAIMS_DB)
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT claim_id, status, route_queue FROM claims WHERE claim_id = ?",
            (claim_id,),
        )
        row = cursor.fetchone()
    finally:
        connection.close()

    if row is None:
        return None
    claim_id_out, status, route_queue = row
    return {"claim_id": claim_id_out, "status": status, "route_queue": route_queue}


AGENT_CARD = AgentCard(
    name="claims-status-agent",
    description=(
        "Read-only lookup of claim status and routing queue, grounded in "
        "data/insurance/claims.db. Never invents a status for an unknown claim_id."
    ),
    url=f"http://{HOST}:{PORT}",
    version="1.0.0",
    skills=[
        AgentSkill(
            id="check_claim_status",
            name="check_claim_status",
            description="Look up a claim's status and route_queue by claim_id.",
            examples=["CLM-424063"],
        )
    ],
)


class ClaimsStatusAgent(A2AServer):
    """Answers check_claim_status requests from data/insurance/claims.db."""

    def handle_message(self, message: Message) -> Message:
        if message.content.type == "function_call" and message.content.name == "check_claim_status":
            params = {p.name: p.value for p in message.content.parameters}
            claim_id = str(params.get("claim_id", "")).strip().upper()
            record = lookup_claim_status(claim_id) if claim_id else None
            if record is None:
                response: dict[str, object] = {
                    "error": f"claim_id {claim_id!r} was not found in claims.db."
                }
            else:
                response = record
            return Message(
                content=FunctionResponseContent(name="check_claim_status", response=response),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id,
            )

        if message.content.type == "text":
            claim_id = message.content.text.strip().upper()
            record = lookup_claim_status(claim_id)
            if record is None:
                text = f"claim_id {claim_id!r} was not found in claims.db."
            else:
                text = (
                    f"{record['claim_id']}: status={record['status']}, "
                    f"route_queue={record['route_queue']}"
                )
            return Message(
                content=TextContent(text=text),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id,
            )

        return Message(
            content=ErrorContent(
                message=(
                    "Unsupported input. Send plain text containing a claim_id, or a "
                    "check_claim_status function_call with a claim_id parameter."
                )
            ),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )


def self_check() -> dict[str, object]:
    known = lookup_claim_status("CLM-424063")
    unknown = lookup_claim_status("CLM-000000")
    return {
        "ok": True,
        "server": "claims-status-agent",
        "endpoint": f"http://{HOST}:{PORT}/a2a",
        "claims_db": str(CLAIMS_DB),
        "known_lookup": known,
        "unknown_lookup": unknown,
        "skills": [skill.id for skill in AGENT_CARD.skills],
    }


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        import json

        print(json.dumps(self_check(), indent=2))
    else:
        agent = ClaimsStatusAgent(agent_card=AGENT_CARD)
        run_server(agent, host=HOST, port=PORT)
