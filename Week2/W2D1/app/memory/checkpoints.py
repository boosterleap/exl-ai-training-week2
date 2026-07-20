"""Session and checkpoint identifiers for Day 1 memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class WorkingMemory:
    thread_id: str
    session_id: str
    summary: str = ""
    tool_trace: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def new_thread(prefix: str = "d1") -> WorkingMemory:
    stamp = uuid4().hex[:8]
    return WorkingMemory(
        thread_id=f"{prefix}-thread-{stamp}",
        session_id=f"{prefix}-session-{stamp}",
    )


def append_tool(memory: WorkingMemory, tool_name: str) -> WorkingMemory:
    memory.tool_trace.append(tool_name)
    memory.updated_at = datetime.now(UTC).isoformat()
    return memory
