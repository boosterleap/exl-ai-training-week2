"""Shared repo/data paths for the progressive insurance app.

Every W2Dn/snippets/ reference script duplicates its own discover_repo_root().
This app is one continuous package built up over five days, so that helper
lives here once and every day{N}_resolve.py imports it instead of redefining it.
"""

from __future__ import annotations

from pathlib import Path


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


REPO_ROOT = discover_repo_root()
DATA_DIR = REPO_ROOT / "data" / "insurance"
CLAIMS_DB = DATA_DIR / "claims.db"
POLICIES_DIR = DATA_DIR / "policies"
FNOL_EMAILS_CSV = DATA_DIR / "fnol_emails.csv"
CLAIMS_KG = DATA_DIR / "claims_kg.json"
GOVERNANCE_TIERS = REPO_ROOT / "data" / "governance" / "use_case_risk_tiers.json"
APP_OUTPUTS_DIR = REPO_ROOT / "app" / "outputs"

# product -> policy document prefix under data/insurance/policies/.
# "commercial_package" has NO entry on purpose -- see data/_DATA_README.md.
PRODUCT_TO_POLICY_PREFIX: dict[str, str] = {
    "homeowners": "POL-HOME-010",
    "auto": "POL-AUTO-001",
    "commercial_property": "POL-COMM-030",
    "landlord_liability": "POL-LL-040",
    "health": "POL-HEALTH-020",
}
