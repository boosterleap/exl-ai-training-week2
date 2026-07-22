"""Reference idempotent delay webhook for Day 3 PM Topic 03.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified: a re-delivered event (same event_id) is
correctly ignored as a duplicate rather than processed twice.

Run it:
    uv run uvicorn W2D3.snippets.delay_webhook:app --port 8010
Then, in a second terminal:
    curl -X POST http://127.0.0.1:8010/webhook/delay \
      -H "Content-Type: application/json" \
      -d '{"event_id":"DEL-001","container_id":"MSKU123","delay_hours":18}'
Run the same curl command twice -- the second response should say
"duplicate_ignored", not process it again.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


DB_PATH = discover_repo_root() / "W2D3" / "outputs" / "delay_events.sqlite"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

connection = sqlite3.connect(DB_PATH, check_same_thread=False)
connection.execute(
    """
    CREATE TABLE IF NOT EXISTS processed_delay_events (
        event_id TEXT PRIMARY KEY,
        container_id TEXT NOT NULL,
        delay_hours INTEGER NOT NULL
    )
    """
)
connection.commit()

app = FastAPI(title="delay-webhook")


class DelayEvent(BaseModel):
    event_id: str
    container_id: str
    delay_hours: int


@app.post("/webhook/delay")
def receive_delay(event: DelayEvent) -> dict:
    """Idempotent: a repeated event_id is a safe no-op, not a duplicate action."""
    already_seen = connection.execute(
        "SELECT 1 FROM processed_delay_events WHERE event_id = ?", (event.event_id,)
    ).fetchone()
    if already_seen:
        return {"status": "duplicate_ignored", "event_id": event.event_id}
    connection.execute(
        "INSERT INTO processed_delay_events VALUES (?, ?, ?)",
        (event.event_id, event.container_id, event.delay_hours),
    )
    connection.commit()
    return {"status": "processed", "event_id": event.event_id}
