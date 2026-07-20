"""Stable Week 2 operator-facing decision contracts."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class TriageDecision(BaseModel):
    lane: Literal["insurance", "banking", "logistics"]
    case_id: str
    urgency: Literal["low", "medium", "high"]
    route_queue: str
    summary: str
    rationale: str
    tools_used: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    needs_human_approval: bool = False


class TriageOutcome(BaseModel):
    status: Literal["completed", "refused"]
    decision: TriageDecision | None = None
    refusal_reason: str | None = None

    @model_validator(mode="after")
    def require_status_fields(self) -> Self:
        if self.status == "completed" and self.decision is None:
            raise ValueError("completed outcomes require a TriageDecision")
        if self.status == "refused" and not self.refusal_reason:
            raise ValueError("refused outcomes require a refusal_reason")
        return self
