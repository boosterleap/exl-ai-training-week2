"""
Build a local Chroma index from insurance policy markdown files.

Run from Week2 root:
    uv run python data/rag/build_policy_index.py
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

WEEK2_ROOT = Path(__file__).resolve().parents[2]
POLICIES_DIR = WEEK2_ROOT / "data" / "insurance" / "policies"
CHUNKS_PATH = WEEK2_ROOT / "data" / "insurance" / "policy_chunks.json"
PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", WEEK2_ROOT / "data" / "chroma_persist"))


def split_markdown(path: Path) -> list[dict]:
  """Split a policy markdown file into section chunks."""
  text = path.read_text(encoding="utf-8")
  policy_id = path.stem.split("_")[0]
  chunks: list[dict] = []
  current_heading = "intro"
  buffer: list[str] = []
  for line in text.splitlines():
    if line.startswith("## "):
      if buffer:
        chunk_id = f"{path.stem}#{slug(current_heading)}"
        chunks.append(make_chunk(chunk_id, policy_id, path.name, current_heading, buffer))
        buffer = []
      current_heading = line[3:].strip()
    else:
      buffer.append(line)
  if buffer:
    chunk_id = f"{path.stem}#{slug(current_heading)}"
    chunks.append(make_chunk(chunk_id, policy_id, path.name, current_heading, buffer))
  return chunks


def slug(value: str) -> str:
  """Create a stable chunk slug from a heading."""
  cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
  return cleaned or "section"


def make_chunk(chunk_id: str, policy_id: str, source_file: str, heading: str, lines: list[str]) -> dict:
  """Build one chunk record with metadata for ACL and lineage."""
  body = "\n".join(lines).strip()
  return {
    "chunk_id": chunk_id,
    "policy_id": policy_id,
    "source_file": source_file,
    "heading": heading,
    "text": body,
    "lane": "insurance",
    "indexed_at": "2026-07-16",
    "version": "v1",
  }


def load_all_chunks() -> list[dict]:
  """Load and chunk all policy markdown files."""
  chunks: list[dict] = []
  for path in sorted(POLICIES_DIR.glob("*.md")):
    chunks.extend(split_markdown(path))
  return chunks


def write_chunks_json(chunks: list[dict]) -> None:
  """Persist chunk records for offline AM demos."""
  payload = {"chunks": chunks, "count": len(chunks)}
  CHUNKS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
  print(f"Wrote {CHUNKS_PATH} ({len(chunks)} chunks)")


def write_chroma_index(chunks: list[dict]) -> None:
  """Embed chunks into a persistent Chroma collection."""
  import chromadb
  from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

  PERSIST_DIR.mkdir(parents=True, exist_ok=True)
  client = chromadb.PersistentClient(path=str(PERSIST_DIR))
  collection_name = "policy_chunks"
  try:
    client.delete_collection(collection_name)
  except Exception:
    pass
  embed_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
  collection = client.get_or_create_collection(
    name=collection_name,
    embedding_function=embed_fn,
  )
  existing = collection.get()
  if existing.get("ids"):
    collection.delete(ids=existing["ids"])
  collection.add(
    ids=[chunk["chunk_id"] for chunk in chunks],
    documents=[chunk["text"] for chunk in chunks],
    metadatas=[
      {
        "policy_id": chunk["policy_id"],
        "source_file": chunk["source_file"],
        "heading": chunk["heading"],
        "lane": chunk["lane"],
        "indexed_at": chunk["indexed_at"],
        "version": chunk["version"],
      }
      for chunk in chunks
    ],
  )
  print(f"Wrote Chroma index at {PERSIST_DIR} ({len(chunks)} chunks)")


def main() -> None:
  """Build JSON chunks and optional Chroma persist directory."""
  chunks = load_all_chunks()
  if not chunks:
    raise SystemExit(f"No policy markdown files found in {POLICIES_DIR}")
  write_chunks_json(chunks)
  rebuild = os.getenv("REBUILD_INDEX", "true").lower() == "true"
  if rebuild:
    write_chroma_index(chunks)
  else:
    print("Skipped Chroma rebuild (REBUILD_INDEX=false)")


if __name__ == "__main__":
  main()
