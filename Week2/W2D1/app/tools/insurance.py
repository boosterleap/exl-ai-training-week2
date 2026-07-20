"""Insurance read tools used by Day 1 agents."""

from __future__ import annotations

import csv
import json
import sqlite3

from pydantic import BaseModel, Field

from .. import config


class FnolInput(BaseModel):
    email_id: str = Field(pattern=r"^CLN-\d{3}$")


class ClaimInput(BaseModel):
    claim_id: str = Field(pattern=r"^CLM-\d{6}$")


class PolicyInput(BaseModel):
    policy_id: str = Field(pattern=r"^POL-(?:[A-Z]+-)?\d{3,9}$")


def fnol_lookup(email_id: str) -> dict:
    with config.FNOL_PATH.open(encoding="utf-8", newline="") as handle:
        row = next(
            (item for item in csv.DictReader(handle) if item["email_id"] == email_id),
            None,
        )
    return row or {"found": False, "email_id": email_id}


def _query_db(sql: str, identifier: str) -> dict:
    with sqlite3.connect(config.CLAIMS_DB) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(sql, (identifier,)).fetchone()
    return dict(row) if row else {"found": False, "id": identifier}


def claim_lookup(claim_id: str) -> dict:
    return _query_db("SELECT * FROM claims WHERE claim_id = ?", claim_id)


def policy_lookup(policy_id: str) -> dict:
    return _query_db("SELECT * FROM policies WHERE policy_id = ?", policy_id)


def as_json(record: dict) -> str:
    return json.dumps(record)
