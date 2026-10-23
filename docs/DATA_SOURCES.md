# Data source setup

## OpenAQ

Create an API key at https://explore.openaq.org/register and save it only in a local `.env` file. OpenAQ expects the `X-API-Key` request header. The starter uses New Delhi location ID `8118` from OpenAQ's quick start, but verify current station coverage, sensors, and license metadata before analysis. Provider-specific terms may apply.

- [Quick start](https://docs.openaq.org/using-the-api/quick-start)
- [API key](https://docs.openaq.org/using-the-api/api-key)
- [Locations and license metadata](https://docs.openaq.org/resources/locations)
- [Daily aggregates](https://docs.openaq.org/resources/measurements)
- [Terms](https://docs.openaq.org/about/terms)

## Open-Meteo

The collector uses the station's coordinates to get historical hourly weather data and aggregates it to calendar days. Credit Open-Meteo and the underlying data providers. The free API is for non-commercial use; check current terms before other use.

- [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [Terms](https://open-meteo.com/en/terms)
