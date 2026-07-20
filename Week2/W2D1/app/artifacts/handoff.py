"""Day 2 handoff artifact preview."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from ..models import TriageDecision


class Day2Handoff(BaseModel):
    source_day: str = "W2D1"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    case_id: str
    lane: str
    summary: str
    route_queue: str
    tools_used: list[str]
    needs_human_approval: bool


def build_handoff(decision: TriageDecision) -> Day2Handoff:
    return Day2Handoff(
        case_id=decision.case_id,
        lane=decision.lane,
        summary=decision.summary,
        route_queue=decision.route_queue,
        tools_used=decision.tools_used,
        needs_human_approval=decision.needs_human_approval,
    )
