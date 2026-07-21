"""
Create the logistics shipments SQLite database used by the Day 1-5 logistics
exercise thread (parallels data/insurance/seed_claims_db.py).

Run once from the Week2-Claude repo root:
    uv run python data/logistics/seed_shipments_db.py

See also: data/logistics/shipment_events.jsonl and data/logistics/delay_events.jsonl
for the container-level event timeline, and data/logistics/policies/ for the
carrier SLA and exception-handling terms.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "shipments.db"

CUSTOMER_ROWS = [
    ("CUS-3001", "Aisha Rahman", "aisha.rahman@example.com"),
    ("CUS-3002", "Tom Becker", "tom.becker@example.com"),
    ("CUS-3003", "Priya Nair", "priya.nair@example.com"),
    ("CUS-3004", "Carlos Mendes", "carlos.mendes@example.com"),
    ("CUS-3005", "Grace Kim", "grace.kim@example.com"),
    ("CUS-3006", "Daniel Osei", "daniel.osei@example.com"),
    ("CUS-3007", "Fatima Ali", "fatima.ali@example.com"),
]

# mode: ocean | rail | air — used to look up the matching carrier SLA policy
# doc prefix (OCEAN-SLA-001 / RAIL-SLA-002). "air" intentionally has no
# matching SLA doc in data/logistics/policies/ — that gap is deliberate,
# it is the logistics-thread parallel to insurance's ungrounded
# commercial_package product (see data/insurance/policies/_README notes).
ORDER_ROWS = [
    ("ORD-3001", "CUS-3001", "MSKU123", "consumer electronics", "ocean", "Kuala Lumpur, MY"),
    ("ORD-3002", "CUS-3002", "MSKU456", "consumer electronics", "ocean", "Rotterdam, NL"),
    ("ORD-3003", "CUS-3003", "MSKU789", "auto parts", "rail", "Chicago, US"),
    ("ORD-3004", "CUS-3004", "MSKU321", "packaged foods", "ocean", "Santos, BR"),
    ("ORD-3005", "CUS-3005", "MSKU654", "apparel", "ocean", "Long Beach, US"),
    ("ORD-3006", "CUS-3006", "MSKU987", "auto parts", "rail", "Atlanta, US"),
    ("ORD-3007", "CUS-3007", "AWB-551", "medical devices", "air", "Doha, QA"),
]


def seed_database(db_path: Path = DB_PATH) -> Path:
  """Create shipments.db with customers and orders tables."""
  db_path.parent.mkdir(parents=True, exist_ok=True)
  connection = sqlite3.connect(db_path)
  try:
    cursor = connection.cursor()
    cursor.executescript(
      """
      DROP TABLE IF EXISTS orders;
      DROP TABLE IF EXISTS customers;
      CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL
      );
      CREATE TABLE orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        container_id TEXT NOT NULL,
        product TEXT NOT NULL,
        mode TEXT NOT NULL,
        destination TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
      );
      """
    )
    cursor.executemany(
      "INSERT INTO customers VALUES (?, ?, ?)",
      CUSTOMER_ROWS,
    )
    cursor.executemany(
      "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
      ORDER_ROWS,
    )
    connection.commit()
  finally:
    connection.close()
  return db_path


def main() -> None:
  """Entry point for seeding shipments.db."""
  path = seed_database()
  print(f"Seeded {path}")


if __name__ == "__main__":
  main()
