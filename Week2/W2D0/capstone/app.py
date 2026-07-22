"""Reference Streamlit UI for the W2D0 capstone, Stage 3.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified with streamlit.testing.v1.AppTest (headless,
no browser needed) -- see test_capstone.py Stage 4 for the automated check.

Run it for real:
    uv run streamlit run W2D0/capstone/app.py
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
FEATURE_COLUMNS = [
    "MedInc", "HouseAge", "AveRooms", "AveBedrms", "Population", "AveOccup", "Latitude", "Longitude",
]


@st.cache_resource
def load_model():
    model_path = OUTPUT_DIR / "model.joblib"
    if not model_path.is_file():
        return None
    return joblib.load(model_path)


def predict_price(model, inputs: dict) -> float:
    row = pd.DataFrame([[inputs[col] for col in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
    return float(model.predict(row)[0])


st.title("California Housing — median value predictor")
st.caption("W2D0 capstone — built stage by stage through Claude Code")

model = load_model()
if model is None:
    st.error("No trained model found. Run train_model.py first (Stage 2).")
    st.stop()

st.subheader("Enter block-group features")
col1, col2 = st.columns(2)
with col1:
    med_inc = st.slider("Median income ($10k)", 0.5, 15.0, 3.9, key="med_inc")
    house_age = st.slider("House age (years)", 1, 52, 28, key="house_age")
    ave_rooms = st.slider("Average rooms per household", 1.0, 15.0, 5.4, key="ave_rooms")
    ave_bedrms = st.slider("Average bedrooms per household", 0.5, 5.0, 1.1, key="ave_bedrms")
with col2:
    population = st.slider("Block group population", 3, 5000, 1400, key="population")
    ave_occup = st.slider("Average occupants per household", 0.5, 10.0, 3.0, key="ave_occup")
    latitude = st.slider("Latitude", 32.5, 42.0, 34.2, key="latitude")
    longitude = st.slider("Longitude", -124.5, -114.0, -118.4, key="longitude")

inputs = {
    "MedInc": med_inc,
    "HouseAge": house_age,
    "AveRooms": ave_rooms,
    "AveBedrms": ave_bedrms,
    "Population": population,
    "AveOccup": ave_occup,
    "Latitude": latitude,
    "Longitude": longitude,
}

if st.button("Predict median house value", key="predict_button"):
    prediction = predict_price(model, inputs)
    st.metric("Predicted median house value", f"${prediction * 100:.1f}k")
