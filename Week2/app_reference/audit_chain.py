"""Day 5 -- append-only, tamper-evident audit chain, adapted from
W2D5/snippets/audit_chain.py.

Adds JSONL persist/load helpers on top of the original in-memory-only
AuditChain, so the app's audit trail survives past a single process run
(each day5_resolve.py call appends to the same file rather than starting
a fresh, empty chain every time).

Run it:
    uv run python -m app.audit_chain
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.paths import APP_OUTPUTS_DIR

AUDIT_LOG_PATH = APP_OUTPUTS_DIR / "audit_log.jsonl"


class AuditChain:
    def __init__(self) -> None:
        self.entries: list[dict] = []
        self.last_hash = "0" * 64

    def append(self, event: dict) -> dict:
        payload = json.dumps(event, sort_keys=True)
        this_hash = hashlib.sha256((self.last_hash + payload).encode()).hexdigest()
        record = {"event": event, "prev_hash": self.last_hash, "hash": this_hash}
        self.entries.append(record)
        self.last_hash = this_hash
        return record

    def verify(self) -> bool:
        prev = "0" * 64
        for record in self.entries:
            payload = json.dumps(record["event"], sort_keys=True)
            expected = hashlib.sha256((prev + payload).encode()).hexdigest()
            if record["hash"] != expected or record["prev_hash"] != prev:
                return False
            prev = record["hash"]
        return True

    def persist_to(self, path: Path = AUDIT_LOG_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for record in self.entries:
                f.write(json.dumps(record) + "\n")

    @classmethod
    def load_from(cls, path: Path = AUDIT_LOG_PATH) -> "AuditChain":
        chain = cls()
        if not path.is_file():
            return chain
        with path.open(encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        chain.entries = lines
        chain.last_hash = lines[-1]["hash"] if lines else "0" * 64
        return chain


if __name__ == "__main__":
    chain = AuditChain()
    chain.append({"action": "approve_claim_payment", "claim_id": "CLM-424063", "approver": "jane.ops"})
    chain.append({"action": "release_hold", "claim_id": "CLM-748422", "approver": "jane.ops"})
    print("chain valid before tamper:", chain.verify())

    chain.entries[0]["event"]["approver"] = "attacker"
    print("chain valid after tamper:  ", chain.verify())
