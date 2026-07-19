"""
Create the insurance claims SQLite database used by Day 1 tools.

Run once from the Week2 repo root:
    uv run python data/insurance/seed_claims_db.py

See also: data/_README.html
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "claims.db"

CLAIM_ROWS = [
    ("CLM-424063", "POL-787532354", "open", "property", "high", 5834.0, "fnol_intake"),
    ("CLM-748422", "POL-930881789", "open", "property", "medium", 9415.0, "fnol_intake"),
    ("CLM-255335", "POL-441002118", "investigation", "commercial", "medium", 423312.0, "fnol_intake"),
    ("CLM-988147", "POL-552901774", "open", "property", "medium", 4200.0, "fnol_intake"),
    ("CLM-597471", "POL-661204889", "open", "property", "high", 52774.0, "fnol_intake"),
    ("CLM-699674", "POL-778301002", "open", "liability", "medium", 12000.0, "liability_review"),
    ("CLM-860535", "POL-635143991", "open", "property", "high", 19400.0, "fnol_intake"),
    ("CLM-531517", "POL-882901445", "open", "auto_property", "medium", 7800.0, "fnol_intake"),
]

POLICY_ROWS = [
    ("POL-787532354", "Jennifer Garcia", "active", "homeowners"),
    ("POL-930881789", "Michael Miller", "active", "commercial_property"),
    ("POL-441002118", "David Taylor", "active", "commercial_package"),
    ("POL-552901774", "Jennifer Johnson", "active", "homeowners"),
    ("POL-661204889", "Robert Chen", "active", "homeowners"),
    ("POL-778301002", "Sarah Lopez", "active", "landlord_liability"),
    ("POL-635143991", "Maria Santos", "active", "homeowners"),
    ("POL-882901445", "James Wu", "active", "homeowners"),
    ("POL-990112334", "Alex Kim", "active", "auto"),
]


def seed_database(db_path: Path = DB_PATH) -> Path:
  """Create claims.db with policies and claims tables."""
  db_path.parent.mkdir(parents=True, exist_ok=True)
  connection = sqlite3.connect(db_path)
  try:
    cursor = connection.cursor()
    cursor.executescript(
      """
      DROP TABLE IF EXISTS claims;
      DROP TABLE IF EXISTS policies;
      CREATE TABLE policies (
        policy_id TEXT PRIMARY KEY,
        named_insured TEXT NOT NULL,
        status TEXT NOT NULL,
        product TEXT NOT NULL
      );
      CREATE TABLE claims (
        claim_id TEXT PRIMARY KEY,
        policy_id TEXT NOT NULL,
        status TEXT NOT NULL,
        loss_type TEXT NOT NULL,
        urgency TEXT NOT NULL,
        reserve_usd REAL NOT NULL,
        route_queue TEXT NOT NULL,
        FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
      );
      """
    )
    cursor.executemany(
      "INSERT INTO policies VALUES (?, ?, ?, ?)",
      POLICY_ROWS,
    )
    cursor.executemany(
      "INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?)",
      CLAIM_ROWS,
    )
    connection.commit()
  finally:
    connection.close()
  return db_path


def main() -> None:
  """Entry point for seeding claims.db."""
  path = seed_database()
  print(f"Seeded {path}")


if __name__ == "__main__":
  main()
