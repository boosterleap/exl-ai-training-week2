"""
Generate the banking loans_5k.parquet slice for Week 2 Day 1 demos.

Run once from the Week2 repo root:
    uv run python data/banking/generate_loans_parquet.py

See also: data/_README.html
"""

from __future__ import annotations

import random
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

OUTPUT_PATH = Path(__file__).resolve().parent / "loans_5k.parquet"
STATUSES = ["current", "delinquent_30", "delinquent_60", "paid_off", "forbearance"]
PRODUCTS = ["mortgage", "auto", "personal", "smb_term"]


def generate_loans(row_count: int = 5000, seed: int = 42) -> pa.Table:
  """Build a synthetic loan servicing table."""
  random.seed(seed)
  loan_ids = [f"LN-{10000 + index}" for index in range(row_count)]
  customer_ids = [f"CUST-{88000 + (index % 1200)}" for index in range(row_count)]
  statuses = [random.choice(STATUSES) for _ in range(row_count)]
  products = [random.choice(PRODUCTS) for _ in range(row_count)]
  balances = [round(random.uniform(1200, 420000), 2) for _ in range(row_count)]
  payoff_amounts = [
    round(balance * random.uniform(0.98, 1.02), 2) for balance in balances
  ]
  return pa.table(
    {
      "loan_id": loan_ids,
      "customer_id": customer_ids,
      "status": statuses,
      "product": products,
      "balance_usd": balances,
      "payoff_usd": payoff_amounts,
    }
  )


def main() -> None:
  """Write loans_5k.parquet to the banking data folder."""
  table = generate_loans()
  OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
  pq.write_table(table, OUTPUT_PATH)
  print(f"Wrote {OUTPUT_PATH} ({table.num_rows} rows)")


if __name__ == "__main__":
  main()
