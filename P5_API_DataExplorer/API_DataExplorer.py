import requests

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/era5"

def fetch_historical_weather(latitude, longitude, start_date, end_date, hourly_params=None, timezone="UTC"):
    hourly_params = hourly_params or ["temperature_2m", "precipitation", "wind_speed_10m"]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,           # YYYY-MM-DD (in the past)
        "end_date": end_date,               # YYYY-MM-DD
        "hourly": ",".join(hourly_params),
        "timezone": timezone,
    }
    r = requests.get(ARCHIVE_URL, params=params, timeout=20)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        print("Request URL:", r.url)
        print("Response text:", r.text[:500])
        raise
    return r.json()

if __name__ == "__main__":
    hist = fetch_historical_weather(
        52.52, 13.405,
        start_date="2023-10-01",
        end_date="2023-10-07",
        timezone="Europe/Berlin",
    )
    print("Historical temp sample:", hist["hourly"]["temperature_2m"][:3])
