import openmeteo_requests
import requests
import os

import requests_cache
import pandas as pd
from retry_requests import retry
from dotenv import load_dotenv

load_dotenv()


def get_weather():
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 50.4547,
        "longitude": 30.5238,
        "hourly": ["temperature_2m", "relative_humidity_2m"],
        "timezone": "auto",
        "past_days": 1,
        "forecast_days": 1
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temp"] = hourly_temperature_2m
    hourly_data["humidity"] = hourly_relative_humidity_2m

    hourly_dataframe = pd.DataFrame(data = hourly_data, index=None)    

    df_styled = hourly_dataframe.iloc[-10:].style\
        .format(precision=1)\
        .highlight_min(color='yellow',axis=0, subset='temp')\
        .highlight_max(color='green', axis=0, subset='temp')
        
    return df_styled.to_string(sparse_columns=True)


def send_message(message):

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    params = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': message
    }
    res = requests.get(url, params=params)
    return res

if __name__ == '__main__' :
    weather = get_weather()
    send_message(weather)