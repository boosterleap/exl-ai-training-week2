"""Reference model training script for the W2D0 capstone, Stage 2.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified: trains a baseline (LinearRegression) and a
tuned model (RandomForestRegressor) on the Stage 1 data, compares them,
and saves the better one with joblib for the Streamlit app to load.

Run it (after data_prep.py has produced outputs/housing.parquet):
    uv run python W2D0/capstone/train_model.py
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
FEATURE_COLUMNS = [
    "MedInc", "HouseAge", "AveRooms", "AveBedrms", "Population", "AveOccup", "Latitude", "Longitude",
]
TARGET_COLUMN = "MedHouseVal"


def load_data() -> pd.DataFrame:
    path = OUTPUT_DIR / "housing.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"Run data_prep.py first -- missing {path}")
    return pd.read_parquet(path)


def train_and_compare(df: pd.DataFrame) -> dict:
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    candidates = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1),
    }

    results = {}
    fitted = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        results[name] = {
            "mae": round(mean_absolute_error(y_test, predictions), 4),
            "r2": round(r2_score(y_test, predictions), 4),
        }
        fitted[name] = model

    best_name = min(results, key=lambda n: results[n]["mae"])
    return {"results": results, "best_name": best_name, "best_model": fitted[best_name]}


if __name__ == "__main__":
    df = load_data()
    outcome = train_and_compare(df)

    print("Model comparison:")
    for name, metrics in outcome["results"].items():
        marker = " <- best (lowest MAE)" if name == outcome["best_name"] else ""
        print(f"  {name:20s} MAE={metrics['mae']:.4f}  R2={metrics['r2']:.4f}{marker}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = OUTPUT_DIR / "model.joblib"
    joblib.dump(outcome["best_model"], model_path)

    metrics_path = OUTPUT_DIR / "metrics.json"
    metrics_path.write_text(
        json.dumps({"best_model": outcome["best_name"], **outcome["results"]}, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved best model ({outcome['best_name']}) to {model_path}")
    print(f"Saved metrics to {metrics_path}")
