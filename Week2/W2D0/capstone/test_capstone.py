"""Reference automated test suite for the W2D0 capstone, Stage 4.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified: all tests pass against the real Stage 1-3
outputs. Uses streamlit.testing.v1.AppTest for a headless UI smoke test --
no browser needed, same "quality floor" discipline as Week 2 Day 4.

Run it (after data_prep.py and train_model.py have produced outputs/):
    uv run pytest W2D0/capstone/test_capstone.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

CAPSTONE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CAPSTONE_DIR / "outputs"

# Quality floor: block "deployment" if the model regresses below this bar.
MAX_ACCEPTABLE_MAE = 0.60
MIN_ACCEPTABLE_R2 = 0.55


def test_data_was_prepared():
    """Stage 1 output exists and has no missing values."""
    data_path = OUTPUT_DIR / "housing.parquet"
    assert data_path.is_file(), "Run data_prep.py (Stage 1) first"
    df = pd.read_parquet(data_path)
    assert len(df) > 0
    assert df.isna().sum().sum() == 0, "Unexpected missing values in prepared data"


def test_data_values_are_in_expected_ranges():
    """Sanity-check the data isn't corrupted -- e.g. no negative populations."""
    df = pd.read_parquet(OUTPUT_DIR / "housing.parquet")
    assert (df["Population"] > 0).all()
    assert (df["MedHouseVal"] > 0).all()
    assert df["Latitude"].between(32, 42).all(), "Latitude out of California's real range"


def test_model_meets_quality_floor():
    """Stage 2's model must not regress below the declared floor."""
    metrics_path = OUTPUT_DIR / "metrics.json"
    assert metrics_path.is_file(), "Run train_model.py (Stage 2) first"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    best = metrics[metrics["best_model"]]
    assert best["mae"] <= MAX_ACCEPTABLE_MAE, f"MAE {best['mae']} exceeds floor {MAX_ACCEPTABLE_MAE}"
    assert best["r2"] >= MIN_ACCEPTABLE_R2, f"R2 {best['r2']} below floor {MIN_ACCEPTABLE_R2}"


def test_model_file_exists():
    assert (OUTPUT_DIR / "model.joblib").is_file(), "Run train_model.py (Stage 2) first"


def test_streamlit_app_loads_without_error():
    """Headless UI smoke test -- no browser needed."""
    at = AppTest.from_file(str(CAPSTONE_DIR / "app.py"))
    at.run(timeout=30)
    assert not at.exception, f"App raised an exception on load: {at.exception}"
    assert len(at.slider) == 8, f"Expected 8 input sliders, found {len(at.slider)}"
    assert len(at.button) == 1


def test_streamlit_predict_button_produces_a_prediction():
    """Full interaction smoke test: click predict, expect a real metric back."""
    at = AppTest.from_file(str(CAPSTONE_DIR / "app.py"))
    at.run(timeout=30)
    at.button[0].click().run(timeout=30)
    assert not at.exception, f"App raised an exception after clicking predict: {at.exception}"
    assert len(at.metric) == 1
    assert "$" in at.metric[0].value


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
