"""
Shared offline retrieval helpers for Day 3 AM/PM labs.

Run scripts from the Week2 repo root so paths resolve correctly.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

WEEK2_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = WEEK2_ROOT / "data" / "insurance" / "policy_chunks.json"
GOLDENS_PATH = WEEK2_ROOT / "data" / "insurance" / "rag_goldens.json"


def tokenize(text: str) -> list[str]:
  """Lowercase alphanumeric tokens for keyword scoring."""
  return re.findall(r"[a-z0-9]+", text.lower())


def load_policy_chunks() -> list[dict]:
  """Load chunked policy records built by build_policy_index.py."""
  if not CHUNKS_PATH.exists():
    raise FileNotFoundError(
      f"Missing {CHUNKS_PATH}. Run: uv run python data/rag/build_policy_index.py"
    )
  payload = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
  return payload["chunks"]


def keyword_score(query: str, text: str) -> float:
  """Simple BM25-like overlap score without extra dependencies."""
  query_tokens = tokenize(query)
  doc_tokens = tokenize(text)
  if not query_tokens or not doc_tokens:
    return 0.0
  doc_counts = Counter(doc_tokens)
  score = 0.0
  for token in set(query_tokens):
    tf = doc_counts.get(token, 0)
    if tf:
      score += 1.0 + math.log(1.0 + tf)
  return score


def top_k_chunks(query: str, chunks: list[dict], k: int = 3) -> list[dict]:
  """Return top-k chunks by keyword score."""
  ranked = sorted(
    chunks,
    key=lambda chunk: keyword_score(query, chunk["text"]),
    reverse=True,
  )
  return [{**chunk, "score": keyword_score(query, chunk["text"])} for chunk in ranked[:k]]


def dedupe_chunks(chunks: list[dict]) -> list[dict]:
  """Keep first occurrence of each chunk_id."""
  seen: set[str] = set()
  unique: list[dict] = []
  for chunk in chunks:
    chunk_id = chunk["chunk_id"]
    if chunk_id in seen:
      continue
    seen.add(chunk_id)
    unique.append(chunk)
  return unique


def grade_evidence(question_id: str | None, chunk_ids: list[str]) -> dict:
  """Check whether retrieved chunk_ids satisfy a golden question."""
  if not question_id:
    return {"sufficient": True, "missing": []}
  goldens = json.loads(GOLDENS_PATH.read_text(encoding="utf-8"))["goldens"]
  golden = next((row for row in goldens if row["question_id"] == question_id), None)
  if golden is None:
    return {"sufficient": True, "missing": []}
  required = set(golden["required_chunk_ids"])
  have = set(chunk_ids)
  missing = sorted(required - have)
  return {"sufficient": not missing, "missing": missing, "question_id": question_id}


def refine_query(base_query: str, hits: list[dict]) -> str:
  """Add missing heading terms for the next retrieval round."""
  terms = []
  for hit in hits:
    terms.extend(tokenize(hit.get("heading", "")))
  extra = " ".join(sorted(set(terms))[:4])
  return f"{base_query} {extra}".strip()


def single_pass_retrieve(query: str, chunks: list[dict], k: int = 3) -> dict:
  """One-shot retrieval baseline."""
  hits = top_k_chunks(query, chunks, k=k)
  return {
    "mode": "single_pass",
    "query": query,
    "steps": [{"round": 0, "query": query, "hits": [hit["chunk_id"] for hit in hits]}],
    "chunks": hits,
  }


def agentic_retrieve(
  query: str,
  chunks: list[dict],
  question_id: str | None = None,
  max_rounds: int = 3,
  k: int = 2,
) -> dict:
  """Planner loop: retrieve, grade evidence, refine query, retrieve again."""
  steps: list[dict] = []
  collected: list[dict] = []
  current_query = query
  grade = {"sufficient": False, "missing": []}
  for round_index in range(max_rounds):
    hits = top_k_chunks(current_query, chunks, k=k)
    collected.extend(hits)
    collected = dedupe_chunks(collected)
    chunk_ids = [chunk["chunk_id"] for chunk in collected]
    grade = grade_evidence(question_id, chunk_ids)
    steps.append(
      {
        "round": round_index,
        "query": current_query,
        "hits": [hit["chunk_id"] for hit in hits],
        "sufficient": grade["sufficient"],
        "missing": grade.get("missing", []),
      }
    )
    if grade["sufficient"]:
      break
    current_query = refine_query(query, hits)
  return {
    "mode": "agentic_rag",
    "query": query,
    "steps": steps,
    "chunks": collected,
    "grade": grade,
  }
