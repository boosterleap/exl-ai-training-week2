"""Canonical data shapes for the progressive insurance app.

The Day 1 and Day 2 W2D snippets each define their own ClaimAndPolicy with a
different field set. This app uses one canonical version everywhere so a
Day 3+ module never has to guess which shape it received.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ClaimAndPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    claim_status: str
    loss_type: str
    urgency: str
    reserve_usd: float
    route_queue: str
    policy_id: str
    named_insured: str
    policy_status: str
    product: str
    grounding_available: bool
    policy_doc_files: list[str] = Field(default_factory=list)
