"""Logistics tools: shipment lookup and permission-gated hold release."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from .. import config


class ShipmentInput(BaseModel):
    container_id: str = Field(min_length=3)


class ReleaseInput(BaseModel):
    container_id: str = Field(min_length=3)
    idempotency_key: str = Field(min_length=4)


def shipment_lookup(container_id: str) -> dict:
    with config.SHIPMENTS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            if event.get("container_id") == container_id:
                return event
    return {"found": False, "container_id": container_id}


def release_hold(container_id: str, idempotency_key: str) -> dict:
    """Study-only write shape. Callers must pass approval and idempotency checks first."""
    return {
        "status": "released",
        "container_id": container_id,
        "idempotency_key": idempotency_key,
    }
