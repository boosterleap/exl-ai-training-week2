"""
Generate banking accounts with ACL metadata for permission-aware retrieval demos.

Run from Week2 root:
    uv run python data/banking/generate_accounts_acl.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

OUTPUT_PATH = Path(__file__).resolve().parent / "accounts_acl.parquet"


def main() -> None:
  """Write a small accounts table with row-level visibility roles."""
  rows = [
    {
      "account_id": "AC-1001",
      "customer_id": "CU-101",
      "balance_usd": 4200.50,
      "region": "US",
      "product": "checking",
      "acl_roles": json.dumps(["teller", "manager"]),
    },
    {
      "account_id": "AC-1002",
      "customer_id": "CU-102",
      "balance_usd": 98000.00,
      "region": "US",
      "product": "private_banking",
      "acl_roles": json.dumps(["manager", "private_banker"]),
    },
    {
      "account_id": "AC-2001",
      "customer_id": "CU-201",
      "balance_usd": 1500.00,
      "region": "EU",
      "product": "checking",
      "acl_roles": json.dumps(["teller"]),
    },
    {
      "account_id": "AC-3001",
      "customer_id": "CU-301",
      "balance_usd": 250000.00,
      "region": "EU",
      "product": "private_banking",
      "acl_roles": json.dumps(["private_banker"]),
    },
  ]
  table = pa.Table.from_pylist(rows)
  pq.write_table(table, OUTPUT_PATH)
  print(f"Wrote {OUTPUT_PATH} ({table.num_rows} rows)")


if __name__ == "__main__":
  main()
