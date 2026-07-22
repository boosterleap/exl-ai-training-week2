"""Reference append-only, tamper-evident audit chain for Day 5 PM Topic 01.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified: each entry hashes in the previous entry's
hash, so editing any past entry breaks verification for everything after
it -- append-only by construction, not just by convention.

Run it:
    uv run python W2D5/snippets/audit_chain.py
"""

from __future__ import annotations

import hashlib
import json


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


if __name__ == "__main__":
    chain = AuditChain()
    chain.append({"action": "approve_claim_payment", "claim_id": "CLM-424063", "approver": "jane.ops"})
    chain.append({"action": "release_hold", "claim_id": "CLM-748422", "approver": "jane.ops"})
    print("chain valid before tamper:", chain.verify())

    chain.entries[0]["event"]["approver"] = "attacker"
    print("chain valid after tamper:  ", chain.verify())
