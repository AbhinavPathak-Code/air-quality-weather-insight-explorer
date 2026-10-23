from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "raw" / "air_quality_weather_daily.csv"

st.set_page_config(page_title="Air Quality and Weather Explorer", page_icon="🌦️", layout="wide")
st.title("Air Quality and Weather Insight Explorer")
st.caption("Daily PM2.5 and nearby gridded weather data. Exploratory analysis, not a health advisory.")

if not DATA.exists():
    st.info("No data file yet. Add your OpenAQ key to .env and run: python src/download_data.py")
    st.stop()

data = pd.read_csv(DATA, parse_dates=["date"])
if data.empty:
    st.warning("The downloaded dataset is empty. Check station coverage and date range.")
    st.stop()

left, right = st.columns(2)
left.metric("Daily PM2.5 rows", f"{len(data):,}")
right.metric("Date range", f"{data['date'].min():%Y-%m-%d} to {data['date'].max():%Y-%m-%d}")
st.subheader("Daily PM2.5")
st.plotly_chart(px.line(data, x="date", y="pm25", title="PM2.5 by day"), width="stretch")

weather_fields = [c for c in ["temperature_2m", "relative_humidity_2m", "precipitation"] if c in data]
if weather_fields:
    field = st.selectbox("Compare PM2.5 with weather", weather_fields)
    st.plotly_chart(
        px.scatter(data, x=field, y="pm25", hover_data=["date"], title=f"PM2.5 vs {field}"),
        width="stretch",
    )
st.subheader("Data preview")
st.dataframe(data, width="stretch")

st.subheader("Machine-learning review of unusual days")
st.caption(
    "Isolation Forest flags days with unusual combinations of available measurements. "
    "These are prompts for further review, not health alerts or explanations of cause."
)

candidate_features = [
    column for column in ["pm25", "temperature_2m", "relative_humidity_2m", "precipitation"]
    if column in data.columns
]
numeric_features = data[candidate_features].apply(pd.to_numeric, errors="coerce")
usable_features = [column for column in candidate_features if numeric_features[column].notna().any()]
numeric_features = numeric_features[usable_features]
valid_rows = numeric_features.notna().any(axis=1) if usable_features else pd.Series(False, index=data.index)

if len(usable_features) == 0 or int(valid_rows.sum()) < 30:
    st.info("At least 30 usable daily records are needed before the model can flag unusual days.")
else:
    model_input = numeric_features.loc[valid_rows].copy()
    model_input = model_input.fillna(model_input.median()).dropna(axis=1, how="all")
    if model_input.empty or model_input.shape[1] == 0:
        st.info("There are not enough numeric measurements to run the anomaly review.")
    else:
        model = IsolationForest(contamination=0.05, random_state=42)
        labels = model.fit_predict(model_input)
        reviewed = data.loc[valid_rows].copy()
        reviewed["model_flag"] = ["Review" if label == -1 else "Typical" for label in labels]
        fig = px.scatter(
            reviewed,
            x="date",
            y="pm25",
            color="model_flag",
            color_discrete_map={"Typical": "#4C78A8", "Review": "#E45756"},
            hover_data=[column for column in ["temperature_2m", "relative_humidity_2m", "precipitation"] if column in reviewed],
            title="Model-flagged PM2.5 days for review",
        )
        st.plotly_chart(fig, width="stretch")
        unusual = reviewed.loc[reviewed["model_flag"] == "Review"].sort_values("date", ascending=False)
        st.write(f"The model flagged **{len(unusual)} of {len(reviewed)}** usable days for review.")
        st.dataframe(unusual, width="stretch")

st.caption("Sources: OpenAQ and Open-Meteo. Add verified, source-specific attribution before publishing.")
