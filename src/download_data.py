from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OPENAQ = "https://api.openaq.org/v3"
OPEN_METEO = "https://archive-api.open-meteo.com/v1/archive"
LOCATION_ID = 8118  # OpenAQ quick-start example for New Delhi. Verify coverage/licence.


def get_json(url: str, *, headers: dict | None = None, params: dict | None = None) -> dict:
    response = requests.get(url, headers=headers, params=params, timeout=45)
    if response.status_code == 401:
        raise RuntimeError("OpenAQ rejected the key. Check OPENAQ_API_KEY in your local .env file.")
    response.raise_for_status()
    return response.json()


def collect_air_quality(api_key: str, start: date, end: date) -> tuple[pd.DataFrame, dict]:
    headers = {"X-API-Key": api_key}
    location = get_json(f"{OPENAQ}/locations/{LOCATION_ID}", headers=headers)["results"][0]
    sensors = get_json(f"{OPENAQ}/locations/{LOCATION_ID}/sensors", headers=headers).get("results", [])
    pm_sensors = []
    for sensor in sensors:
        parameter = sensor.get("parameter", {})
        label = str(parameter.get("name", "")).lower().replace(".", "").replace("_", "")
        display = str(parameter.get("displayName", "")).lower().replace(".", "").replace("_", "")
        if label in {"pm25", "pm2 5"} or display in {"pm25", "pm2 5"}:
            pm_sensors.append(sensor)
    if not pm_sensors:
        available = sorted({str(s.get("parameter", {}).get("name", "unknown")) for s in sensors})
        raise RuntimeError(f"No PM2.5 sensor found at location {LOCATION_ID}. Available parameters: {available}.")

    rows = []
    for sensor in pm_sensors:
        query = {
            "date_from": f"{start.isoformat()}T00:00:00Z",
            "date_to": f"{end.isoformat()}T23:59:59Z",
            "limit": 100,
            "page": 1,
        }
        while True:
            payload = get_json(
                f"{OPENAQ}/sensors/{sensor['id']}/days", headers=headers, params=query
            )
            results = payload.get("results", [])
            for item in results:
                start_time = item.get("period", {}).get("datetimeFrom", {})
                rows.append({
                    "date": start_time.get("local") or start_time.get("utc"),
                    "pm25": item.get("value"),
                    "unit": sensor.get("parameter", {}).get("units"),
                    "sensor_id": sensor.get("id"),
                    "sensor_name": sensor.get("name"),
                    "location_id": LOCATION_ID,
                    "location_name": location.get("name"),
                    "provider": location.get("provider", {}).get("name"),
                })
            found = payload.get("meta", {}).get("found", 0)
            try:
                found = int(found or 0)
            except (TypeError, ValueError):
                found = 0
            if not results or len(results) < query["limit"] or (found and query["page"] * query["limit"] >= found):
                break
            query["page"] += 1
    air = pd.DataFrame(rows)
    if not air.empty:
        air["date"] = pd.to_datetime(air["date"], errors="coerce").dt.date
        air = air.dropna(subset=["date", "pm25"]).drop_duplicates(["date", "sensor_id"])
    return air, location


def collect_weather(latitude: float, longitude: float, timezone: str, start: date, end: date) -> pd.DataFrame:
    payload = get_json(OPEN_METEO, params={
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "hourly": "temperature_2m,relative_humidity_2m,precipitation",
        "timezone": timezone or "Asia/Kolkata",
    })
    hourly = pd.DataFrame(payload.get("hourly", {}))
    if hourly.empty:
        raise RuntimeError("Open-Meteo returned no hourly data for the selected coordinates and dates.")
    hourly["date"] = pd.to_datetime(hourly["time"], errors="coerce").dt.date
    return hourly.groupby("date", as_index=False).agg(
        temperature_2m=("temperature_2m", "mean"),
        relative_humidity_2m=("relative_humidity_2m", "mean"),
        precipitation=("precipitation", "sum"),
    )


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("OPENAQ_API_KEY")
    if not api_key or api_key == "put_your_key_here":
        print("Add your OpenAQ API key to .env first. See README.md.")
        return 1

    end = date.today() - timedelta(days=5)  # Historical API has a short reporting delay.
    start = end - timedelta(days=180)
    RAW.mkdir(parents=True, exist_ok=True)
    try:
        air, location = collect_air_quality(api_key, start, end)
        if air.empty:
            raise RuntimeError("No daily PM2.5 rows were returned for this date range.")
        coordinates = location.get("coordinates", {})
        latitude, longitude = coordinates.get("latitude"), coordinates.get("longitude")
        if latitude is None or longitude is None:
            raise RuntimeError("The station does not include coordinates needed for weather data.")
        weather = collect_weather(
            float(latitude), float(longitude), location.get("timezone") or "Asia/Kolkata", start, end
        )
        air.to_csv(RAW / "openaq_pm25_daily.csv", index=False)
        weather.to_csv(RAW / "openmeteo_weather_daily.csv", index=False)
        merged = air.merge(weather, on="date", how="left")
        merged.to_csv(RAW / "air_quality_weather_daily.csv", index=False)
        print(f"Saved {len(air)} air-quality rows and {len(weather)} weather rows to {RAW}")
        print(f"Station: {location.get('name')} | Date range: {start} to {end}")
        print("Review missing dates, units, station license, and provider attribution before analysis.")
        return 0
    except (requests.RequestException, RuntimeError, KeyError, ValueError) as exc:
        print(f"Download failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
