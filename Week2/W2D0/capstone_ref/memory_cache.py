"""Phase 4 reference: durable per-Loan_ID session memory (so a follow-up
email resumes with context) and a semantic cache over policy search (so a
paraphrased question doesn't re-run retrieval).

Adapts W2D3/my_customer_notes.py's episodic-note idea (without the LangGraph
dependency -- a plain SQLite table is enough for one note per interaction)
and W2D3/snippets/semantic_cache.py's exact-then-semantic cache verbatim.

Run it:
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" W2D0/capstone_ref/memory_cache.py
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import anthropic
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from tools import search_policy

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DB_PATH = Path(__file__).parent / "outputs" / "session_memory.db"
SIMILARITY_THRESHOLD = 0.85
MODEL = "claude-opus-4-8"


class SessionMemory:
    """One row per interaction per Loan_ID -- durable across process restarts."""

    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS case_notes "
            "(loan_id TEXT, note TEXT, created_at TEXT)"
        )
        self._conn.commit()

    def add_note(self, loan_id: str, note: str) -> None:
        self._conn.execute(
            "INSERT INTO case_notes (loan_id, note, created_at) VALUES (?, ?, ?)",
            (loan_id, note, datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()

    def get_notes(self, loan_id: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT note FROM case_notes WHERE loan_id = ? ORDER BY created_at", (loan_id,)
        ).fetchall()
        return [r[0] for r in rows]


_embedder: SentenceTransformer | None = None


def _embed(text: str) -> np.ndarray:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return np.array(_embedder.encode([text])[0])


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


class SemanticPolicyCache:
    """Caches search_policy results; a paraphrased query hits the cache
    instead of re-running retrieval."""

    def __init__(self):
        self._entries: list[tuple[str, str, np.ndarray, list[dict]]] = []  # (product, query, vec, hits)
        self.hits = 0
        self.misses = 0

    def search(self, query: str, product: str) -> tuple[list[dict], str]:
        query_vec = _embed(query)
        best_sim, best_hits = 0.0, None
        for cached_product, _, cached_vec, hits in self._entries:
            if cached_product != product:
                continue
            sim = _cosine(query_vec, cached_vec)
            if sim > best_sim:
                best_sim, best_hits = sim, hits
        if best_sim >= SIMILARITY_THRESHOLD:
            self.hits += 1
            return best_hits, "semantic_hit"
        self.misses += 1
        hits = search_policy(query, product=product)
        self._entries.append((product, query, query_vec, hits))
        return hits, "miss"


def demo_memory(client: anthropic.Anthropic) -> None:
    memory = SessionMemory()
    loan_id = "LP002086"  # rejected education_loan, live case from Phase 1

    memory.add_note(
        loan_id,
        f"[{date.today().isoformat()}] Told customer their education_loan was "
        f"rejected; no documented appeal-window policy exists for education_loan "
        f"(only business_loan has one), so no re-review timeline was promised.",
    )

    prior_notes = memory.get_notes(loan_id)
    followup_body = (
        "Hi again, following up on my rejected loan LP002086 -- has anything "
        "changed, or is there really nothing I can do?"
    )
    system = (
        "You are a loan-servicing assistant. Prior interactions on this case:\n"
        + "\n".join(prior_notes)
        + "\n\nUse this context so you don't repeat information the customer "
        "wasn't told, and don't contradict what was already said."
    )
    response = client.messages.create(
        model=MODEL, max_tokens=400, system=system,
        messages=[{"role": "user", "content": followup_body}],
    )
    reply = next(b.text for b in response.content if b.type == "text")
    print("Prior note stored:")
    for n in prior_notes:
        print(f"  {n}")
    print("\nFollow-up reply (should be consistent with the prior note):")
    print(reply)


def demo_cache() -> None:
    cache = SemanticPolicyCache()
    queries = [
        ("is there a surcharge for rural properties", "home_loan"),
        ("do rural properties get charged extra", "home_loan"),  # paraphrase -> hit
        ("what documents are needed for a business loan", "business_loan"),  # unrelated -> miss
    ]
    print("\nSemantic policy cache:")
    for query, product in queries:
        hits, layer = cache.search(query, product)
        top = hits[0]["heading"] if hits else None
        print(f"  {layer:12s} | ({product}) {query!r} -> top heading: {top}")
    print(f"  cache hits={cache.hits} misses={cache.misses}")


if __name__ == "__main__":
    client = anthropic.Anthropic()
    demo_memory(client)
    demo_cache()
