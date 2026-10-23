from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

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
st.caption("Sources: OpenAQ and Open-Meteo. Add verified, source-specific attribution before publishing.")
