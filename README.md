# Global Air Quality & Weather Explorer

A global city-search weather and air-quality dashboard with seven-day weather forecasts, a five-day modelled air-quality outlook, nearby OpenAQ monitoring locations and latest sensor readings when available, and a transparent data-backed insight assistant. A saved New Delhi sample analysis remains available as a worked historical analytics example.

## Project question

What weather and air-quality information is available for a searched city, where are nearby monitoring stations, and how do observed readings compare with modelled forecasts? The app searches cities worldwide. Station observations and model estimates are labelled separately; association does not establish that weather caused air-quality changes.

## Current dashboard

- Search for a city worldwide and view current modelled weather conditions.
- Explore a seven-day weather forecast and up to five days of modelled air-quality estimates.
- Explore nearby OpenAQ monitoring locations on a map and view available latest sensor readings, provider, and license details. Coverage varies by place. The OpenAQ API key is optional for weather and model forecasts and required for station data.
- Use the data-backed text brief to summarize the selected city's latest forecast. It uses simple transparent rules and does not call a generative-AI service.
- See animated weather symbols and the Sky & Air Buddy mascot. These are decorative and do not provide health or pet-safety advice.
- Open the previous New Delhi sample analysis to view the saved data and its Isolation Forest review flags.

Weather and air-quality forecasts are grid-model estimates, not measurements at the selected address. OpenAQ provides real monitoring locations and sensor observations, but global coverage is uneven and some places have no nearby station or recent reading. Station dates, providers, update times, measured pollutants, and licenses vary. Open-Meteo's listed pollen forecast variables are limited to Europe, so pollen is not currently shown globally.

## Data sources

- Air quality observations: OpenAQ API v3, queried around the selected city. Confirm station coverage, sensors, provider, update time, and license metadata before interpreting or redistributing readings. An API key is required for station data.
- Weather and modelled air quality: Open-Meteo Geocoding, Weather Forecast, and Air Quality APIs. Credit Open-Meteo and its data providers; check the current terms for your intended use.

See [data source details](docs/DATA_SOURCES.md). Do not commit API keys or downloaded raw data.

## Current sample and results

The current local sample covers **2026-04-21 through 2026-10-18**. It contains **161 daily PM2.5 observations** and **181 daily weather records**. There are **20 calendar dates without a PM2.5 observation** in that span; these dates are gaps in station coverage, not zero readings. The joined sample has one PM2.5 sensor at the New Delhi location, with readings reported in **µg/m³**.

The dashboard's Isolation Forest flagged **8 of 161 usable days** for review. These are statistical review prompts, not confirmed errors, health alerts, or evidence that weather caused a pollution change. The result depends on the chosen model settings and this station's sample.

Before presenting or comparing results, confirm current station and sensor metadata, coverage, and source attribution. Weather is gridded reanalysis for the station coordinates, not a measurement taken by the air-quality sensor. The current sample is local and is excluded from GitHub; rerun the download script to reproduce it.

## Stack

Python, Pandas, Requests, OpenAQ API, Open-Meteo Geocoding, Weather Forecast and Air Quality APIs, Plotly, Streamlit, and scikit-learn.

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

4. To enable nearby OpenAQ station readings, create an OpenAQ API key at https://explore.openaq.org/register. Copy `.env.example` to `.env` and set `OPENAQ_API_KEY=your_key`. The city forecast works without this key. Never add the key to source code or GitHub.
5. To recreate the saved New Delhi historical sample (the live dashboard search is worldwide):

   ```powershell
   python src/download_data.py
   ```

6. Review the saved CSV files in `data/raw`. Check date coverage, units, missing dates, and the station's attribution/license metadata.
7. Launch the dashboard:

   ```powershell
   streamlit run app.py
   ```

## GitHub checklist

- Recommended repository name: `global-air-quality-weather-explorer`.
- Keep `.env` and downloaded files out of Git. The supplied `.gitignore` excludes them.
- Add verified source links, license/attribution, date range, collection method, and limitations.
- Add dashboard screenshots after you have built and reviewed the dashboard.
- Never upload keys or data whose terms prohibit redistribution.

## Current status and next improvements

- [x] Download and join a sample of daily air-quality and weather data
- [x] Display the time series, data table, and Isolation Forest review flags in Streamlit
- [x] Document the current sample size, date gaps, and interpretation of model flags
- [ ] Review OpenAQ coverage, sensor/provider metadata, source attribution, and data terms for locations you feature
- [ ] Add a screenshot of the dashboard and a short, evidence-based analysis of the observed trends
- [ ] Review the public GitHub repository to confirm `.env` and downloaded raw data are excluded

The project is educational and is not a health advisory. OpenAQ's latest observation may not be a real-time reading or the newest measurement ingested. Global station coverage is uneven; stations vary in sensor, provider, units, license, and sampling coverage. Check these details before comparing readings. Open-Meteo forecast values are model estimates for grid cells, not measurements at the sensor or exact address. Weather forecasts cover seven days; the global air-quality forecast is limited to five days in this dashboard. Pollen is not currently shown because the pollen variables offered by this service are limited to Europe.
