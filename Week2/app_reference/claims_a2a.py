"""Day 2 -- standalone A2A server exposing check_claim_status.

Adapted from W2D2/snippets/a2a_claims_server.py. Discoverable via the
Agent Card at GET /.well-known/agent.json. Like claims_network.py, this
stays a real standalone process (the exercise is A2A discovery + the
message round trip) -- day2_resolve.py calls lookup_status() in-process
for its own pipeline rather than spawning this server itself.

Run it:
    uv run python -m app.claims_a2a
Card:  http://127.0.0.1:5055/.well-known/agent.json
"""

from __future__ import annotations

import sqlite3

from python_a2a import A2AServer, AgentCard, AgentSkill, Message, MessageRole, TextContent, run_server

from app.paths import CLAIMS_DB

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
    normalized = claim_id.strip().upper()
    connection = sqlite3.connect(CLAIMS_DB)
    try:
        row = connection.execute(
            "SELECT status, route_queue FROM claims WHERE claim_id = ?",
            (normalized,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return f"No claim found with id {normalized}."
    status, route_queue = row
    return f"{normalized}: status={status}, route_queue={route_queue}"


class ClaimsStatusServer(A2AServer):
    def handle_message(self, message: Message) -> Message:
        text = message.content.text if hasattr(message.content, "text") else ""
        claim_id = next((tok for tok in text.replace("?", " ").split() if tok.upper().startswith("CLM-")), None)
        reply = lookup_status(claim_id) if claim_id else "Ask about a specific claim_id, e.g. CLM-424063."
        return Message(
            content=TextContent(text=reply),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )


if __name__ == "__main__":
    run_server(ClaimsStatusServer(agent_card=CARD), host="127.0.0.1", port=5055)
