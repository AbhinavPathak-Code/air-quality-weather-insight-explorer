# Air Quality and Weather Insight Explorer

A data analytics portfolio project studying how daily PM2.5 readings vary over time alongside temperature, humidity, and rainfall in New Delhi. It collects and joins public air-quality and weather data, presents the results in a Streamlit dashboard, and uses Isolation Forest to flag unusual days for further review.

## Project question

How do daily PM2.5 readings vary over time, and what patterns appear alongside weather? This is exploratory analysis: association does not establish that weather caused air-quality changes.

## Data sources

- Air quality: OpenAQ API v3. The starter uses location ID `8118`, cited in OpenAQ's New Delhi quick start. Confirm current coverage, sensors, provider, and license metadata before relying on it. An API key is required.
- Weather: Open-Meteo Historical Weather API, queried at the station coordinates. Credit Open-Meteo and its data providers; the free API is for non-commercial use.

See [data source details](docs/DATA_SOURCES.md). Do not commit API keys or downloaded raw data.

## Current sample and results

The current local sample covers **2026-04-21 through 2026-10-18**. It contains **161 daily PM2.5 observations** and **181 daily weather records**. There are **20 calendar dates without a PM2.5 observation** in that span; these dates are gaps in station coverage, not zero readings. The joined sample has one PM2.5 sensor at the New Delhi location, with readings reported in **µg/m³**.

The dashboard's Isolation Forest flagged **8 of 161 usable days** for review. These are statistical review prompts, not confirmed errors, health alerts, or evidence that weather caused a pollution change. The result depends on the chosen model settings and this station's sample.

Before presenting or comparing results, confirm current station and sensor metadata, coverage, and source attribution. Weather is gridded reanalysis for the station coordinates, not a measurement taken by the air-quality sensor. The current sample is local and is excluded from GitHub; rerun the download script to reproduce it.

## Stack

Python, Pandas, Requests, OpenAQ API, Open-Meteo API, Plotly, Streamlit, and later scikit-learn.

## Start in VS Code on Windows

1. Install Python 3.11+ and VS Code. Install the Microsoft Python extension in VS Code.
2. Open this folder using **File > Open Folder**.
3. In **Terminal > New Terminal**, run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Create an OpenAQ API key at https://explore.openaq.org/register. Copy `.env.example` to `.env` and set `OPENAQ_API_KEY=your_key`. Never add the key to source code or GitHub.
5. Download a recent six-month sample:

   ```powershell
   python src/download_data.py
   ```

6. Review the saved CSV files in `data/raw`. Check date coverage, units, missing dates, and the station's attribution/license metadata.
7. Launch the starter dashboard:

   ```powershell
   streamlit run app.py
   ```

## GitHub checklist

- Create a public repository named `air-quality-weather-insight-explorer` (or choose another name).
- Keep `.env` and downloaded files out of Git. The supplied `.gitignore` excludes them.
- Add verified source links, license/attribution, date range, collection method, and limitations.
- Add dashboard screenshots after you have built and reviewed the dashboard.
- Never upload keys or data whose terms prohibit redistribution.

## Current status and next improvements

- [x] Download and join a sample of daily air-quality and weather data
- [x] Display the time series, data table, and Isolation Forest review flags in Streamlit
- [x] Document the current sample size, date gaps, and interpretation of model flags
- [ ] Confirm current OpenAQ sensor/provider metadata, source attribution, and data terms
- [ ] Add a screenshot of the dashboard and a short, evidence-based analysis of the observed trends
- [ ] Review the public GitHub repository to confirm `.env` and downloaded raw data are excluded

The project is educational and is not a health advisory. Stations vary in sensor, provider, units, and sampling coverage; do not compare them without checking these details. Open-Meteo values are gridded reanalysis, not necessarily measurements at the sensor itself.
