"""Reference EDA script for the W2D0 capstone, Stage 1.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified: loads the California Housing dataset
(bundled with scikit-learn, no download auth needed), reports summary
stats, and saves a correlation heatmap + a geographic scatter plot.

Run it:
    uv run python W2D0/capstone/data_prep.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless-safe for the VM
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.datasets import fetch_california_housing

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def load_housing_df() -> pd.DataFrame:
    bundle = fetch_california_housing(as_frame=True)
    df = bundle.frame.copy()
    df.columns = [c.strip() for c in df.columns]
    return df


def summarize(df: pd.DataFrame) -> None:
    print("Shape:", df.shape)
    print("\nSummary stats:")
    print(df.describe().round(2))
    print("\nMissing values per column:")
    print(df.isna().sum())


def plot_correlation_heatmap(df: pd.DataFrame, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(df.corr(numeric_only=True), annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("California Housing — feature correlations")
    path = out_dir / "correlation_heatmap.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def plot_geographic_price(df: pd.DataFrame, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    scatter = ax.scatter(
        df["Longitude"], df["Latitude"], c=df["MedHouseVal"], cmap="viridis", s=8, alpha=0.6
    )
    fig.colorbar(scatter, ax=ax, label="Median house value ($100k)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("California Housing — price by location")
    path = out_dir / "geographic_price.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


if __name__ == "__main__":
    df = load_housing_df()
    summarize(df)
    heatmap_path = plot_correlation_heatmap(df, OUTPUT_DIR)
    geo_path = plot_geographic_price(df, OUTPUT_DIR)
    df.to_parquet(OUTPUT_DIR / "housing.parquet")
    print(f"\nSaved: {heatmap_path}")
    print(f"Saved: {geo_path}")
    print(f"Saved: {OUTPUT_DIR / 'housing.parquet'}")
