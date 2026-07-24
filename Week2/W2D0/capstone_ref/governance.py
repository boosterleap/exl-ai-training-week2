"""Phase 5 reference: no reply that implies an escalation, denial framing,
or fraud-review disposition auto-sends -- it sits in a human-approval queue
first, and every decision is written to an append-only, tamper-evident
audit chain.

AuditChain is W2D5/snippets/audit_chain.py, unmodified (it's already
minimal and generic). ApprovalQueue is new: a SQLite-backed pending queue
gating anything CLAUDE.md's ground rules call "sensitive or irreversible" --
here, an escalation disposition (all 3 gold_loan cases) or a fraud-review
disposition (LN-012 specifically).

Run it (after running agent_loop.py at least once):
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" W2D0/capstone_ref/governance.py
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path(__file__).parent / "outputs"
DB_PATH = OUT_DIR / "approval_queue.db"


class AuditChain:
    """Append-only, tamper-evident: each entry hashes in the previous
    entry's hash, so editing any past entry breaks verification for
    everything after it."""

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


class ApprovalQueue:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(exist_ok=True)
        # check_same_thread=False: Streamlit's rerun model can hand this
        # cached connection to a different thread on each rerun.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS pending_approvals "
            "(email_id TEXT PRIMARY KEY, loan_id TEXT, disposition TEXT, "
            "status TEXT, decided_by TEXT, decided_at TEXT)"
        )
        self._conn.commit()

    def enqueue(self, email_id: str, loan_id: str, disposition: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO pending_approvals "
            "(email_id, loan_id, disposition, status, decided_by, decided_at) "
            "VALUES (?, ?, ?, 'pending', NULL, NULL)",
            (email_id, loan_id, disposition),
        )
        self._conn.commit()

    def decide(self, email_id: str, approved: bool, decided_by: str) -> None:
        self._conn.execute(
            "UPDATE pending_approvals SET status = ?, decided_by = ?, decided_at = ? "
            "WHERE email_id = ?",
            ("approved" if approved else "rejected", decided_by,
             datetime.now(timezone.utc).isoformat(), email_id),
        )
        self._conn.commit()

    def all(self) -> list[dict]:
        cols = ["email_id", "loan_id", "disposition", "status", "decided_by", "decided_at"]
        rows = self._conn.execute(f"SELECT {', '.join(cols)} FROM pending_approvals").fetchall()
        return [dict(zip(cols, row)) for row in rows]


def main():
    replies = json.loads((OUT_DIR / "draft_replies.json").read_text(encoding="utf-8"))
    queue = ApprovalQueue()
    audit = AuditChain()

    for reply in replies:
        email_id = reply["email_id"]
        loan_id = reply["loan_id"]
        if reply.get("escalated"):
            disposition = "fraud_review" if email_id == "LN-012" else "escalation"
            queue.enqueue(email_id, loan_id, disposition)
            audit.append({"action": "queued_for_review", "email_id": email_id,
                           "loan_id": loan_id, "disposition": disposition})
            if disposition == "fraud_review":
                # Simulated human decision: the fraud-flagged case does NOT get
                # the standard escalation reply auto-sent -- a human explicitly
                # routes it to the fraud team instead. This is the reject path.
                queue.decide(email_id, approved=False, decided_by="simulated_underwriter_jane")
                audit.append({"action": "rejected", "email_id": email_id, "loan_id": loan_id,
                               "approver": "simulated_underwriter_jane",
                               "reason": "fraud-flagged case routed to fraud team, not auto-sent"})
            else:
                queue.decide(email_id, approved=True, decided_by="simulated_underwriter_jane")
                audit.append({"action": "approved", "email_id": email_id, "loan_id": loan_id,
                               "approver": "simulated_underwriter_jane"})
        else:
            # Routine, grounded status/policy reply -- not a sensitive or
            # irreversible action per CLAUDE.md's ground rules, so it does
            # not need to sit in a human queue. Still logged to the audit
            # chain so there's a record of every reply that went out.
            audit.append({"action": "auto_approved_routine_reply", "email_id": email_id, "loan_id": loan_id})

    print("Approval queue contents:")
    for row in queue.all():
        print(f"  {row['email_id']:8s} {row['disposition']:12s} -> {row['status']:9s} (by {row['decided_by']})")

    print(f"\nAudit chain: {len(audit.entries)} entries, valid={audit.verify()}")

    # Tamper demo: mutate a past entry and confirm verification catches it.
    audit.entries[0]["event"]["loan_id"] = "TAMPERED"
    print(f"Audit chain after tampering entry 0: valid={audit.verify()}")


if __name__ == "__main__":
    main()
