"""Phase 6 reference: a small Streamlit review queue for a loan officer.

Reads the approval queue Phase 5's governance.py populated, shows each
pending/decided case's drafted reply side by side with its disposition,
and lets a real human click Approve/Reject -- the actual human-in-the-loop
step Phase 5 simulated with a scripted decision.

Run it:
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" -m streamlit run W2D0/capstone_ref/app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from governance import ApprovalQueue  # noqa: E402

OUT_DIR = Path(__file__).parent / "outputs"


@st.cache_resource
def load_queue() -> ApprovalQueue:
    return ApprovalQueue()


@st.cache_data
def load_replies() -> dict[str, dict]:
    path = OUT_DIR / "draft_replies.json"
    if not path.is_file():
        return {}
    replies = json.loads(path.read_text(encoding="utf-8"))
    return {r["email_id"]: r for r in replies}


st.title("Loan officer review queue")
st.caption("Escalated and fraud-flagged cases only -- routine grounded replies auto-send.")

queue = load_queue()
replies = load_replies()

if not replies:
    st.error("No draft replies found. Run agent_loop.py first.")
    st.stop()

rows = queue.all()
if not rows:
    st.info("Queue is empty. Run governance.py first to populate it from draft_replies.json.")
    st.stop()

for row in rows:
    reply = replies.get(row["email_id"], {})
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"{row['email_id']} — {row['loan_id']}")
            st.caption(f"Disposition: {row['disposition']}")
            st.write(reply.get("reply", "(no draft on file)"))
        with col2:
            st.metric("Status", row["status"])
            if row["decided_by"]:
                st.caption(f"Decided by {row['decided_by']}")
            if st.button("Approve", key=f"approve_{row['email_id']}"):
                queue.decide(row["email_id"], approved=True, decided_by="reviewer_in_app")
                st.rerun()
            if st.button("Reject", key=f"reject_{row['email_id']}"):
                queue.decide(row["email_id"], approved=False, decided_by="reviewer_in_app")
                st.rerun()
