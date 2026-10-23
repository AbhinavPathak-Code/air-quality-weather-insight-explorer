# Air Quality and Weather Insight Explorer

A data analytics portfolio project studying how daily PM2.5 readings vary over time alongside temperature, humidity, and rainfall in New Delhi. The first version focuses on source validation, data collection, cleaning, exploratory analysis, and a clean dashboard. A later version adds carefully scoped anomaly detection.

## Project question

How do daily PM2.5 readings vary over time, and what patterns appear alongside weather? This is exploratory analysis: association does not establish that weather caused air-quality changes.

## Data sources

- Air quality: OpenAQ API v3. The starter uses location ID `8118`, cited in OpenAQ's New Delhi quick start. Confirm current coverage, sensors, provider, and license metadata before relying on it. An API key is required.
- Weather: Open-Meteo Historical Weather API, queried at the station coordinates. Credit Open-Meteo and its data providers; the free API is for non-commercial use.

See [data source details](docs/DATA_SOURCES.md). Do not commit API keys or downloaded raw data.

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

## Roadmap

- [ ] Confirm a usable OpenAQ station, sensor, coverage, and license
- [ ] Download a reproducible sample and document data quality
- [ ] Clean and join daily pollution and weather data
- [ ] Analyze time trends, seasonality, missingness, and weather comparisons
- [ ] Improve the Streamlit dashboard and explain findings
- [ ] Add Isolation Forest anomaly flags, described as review signals rather than health alerts
- [ ] Add source attribution, limitations, screenshots, and setup guidance

The project is educational and is not a health advisory. Stations vary in sensor, provider, units, and sampling coverage; do not compare them without checking these details. Open-Meteo values are gridded reanalysis, not necessarily measurements at the sensor itself.
