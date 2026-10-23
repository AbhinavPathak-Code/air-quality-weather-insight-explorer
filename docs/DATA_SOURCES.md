# Data sources and coverage

The interactive dashboard accepts city searches worldwide. Weather and air-quality forecasts are model outputs, while OpenAQ readings are measurements reported by individual monitoring stations. Global search does not mean every place has a station or a recent reading.

## OpenAQ

The weather and model forecast dashboard does not require an OpenAQ key. To display nearby monitoring locations and sensor observations, create an API key at https://explore.openaq.org/register and save it only in a local `.env` file as `OPENAQ_API_KEY=your_key`. OpenAQ expects the `X-API-Key` request header. The dashboard searches locations within a user-selected radius of the city coordinates, maps returned location coordinates, and displays available latest readings for the selected location's sensors.

A nearby location may have no recent measurements, and an API's latest returned observation should not be assumed to be live. The saved historical sample uses New Delhi location ID `8118` from OpenAQ's quick start. OpenAQ location records include provider, owner, sensor, and license metadata. Check the selected station's current metadata and underlying provider terms before publishing or redistributing readings. Coverage, pollutants, units, and reporting times vary by location.

- [Quick start](https://docs.openaq.org/using-the-api/quick-start)
- [API key](https://docs.openaq.org/using-the-api/api-key)
- [Locations and license metadata](https://docs.openaq.org/resources/locations)
- [Daily aggregates](https://docs.openaq.org/resources/measurements)
- [Terms](https://docs.openaq.org/about/terms)

## Open-Meteo

The original sample collector uses the New Delhi sample station coordinates to get historical hourly weather data and aggregates it to calendar days. The interactive dashboard uses Open-Meteo Geocoding, Weather Forecast, and Air Quality APIs for worldwide city search, current modelled conditions, and forecasts. Credit Open-Meteo and the underlying data providers. The free API is for non-commercial use; check current terms before other use.

The weather dashboard displays a seven-day forecast. The air-quality outlook uses global model data and displays up to five days. These are grid-model estimates, not sensor readings at the selected address. Open-Meteo's pollen species variables are limited to Europe, so pollen is not currently shown in the worldwide dashboard.

- [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- [Weather Forecast API](https://open-meteo.com/en/docs)
- [Air Quality API](https://open-meteo.com/en/docs/air-quality-api)
- [Terms](https://open-meteo.com/en/terms)
