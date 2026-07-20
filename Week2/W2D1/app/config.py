"""Shared Day 1 settings and repository paths."""

from pathlib import Path

WEEK2_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = WEEK2_ROOT / "data"
OUTPUT_DIR = WEEK2_ROOT / "W2D1" / "outputs" / "day1"

FNOL_PATH = DATA_ROOT / "insurance" / "fnol_emails.csv"
CLAIMS_DB = DATA_ROOT / "insurance" / "claims.db"
SHIPMENTS_PATH = DATA_ROOT / "logistics" / "shipment_events.jsonl"

DEFAULT_MODEL = "claude-sonnet-4-6"
REASONING_MODEL = "claude-opus-4-8"
MAX_TURNS = 6
MAX_TOKENS = 8000
MAX_BUDGET_USD = 1.0
