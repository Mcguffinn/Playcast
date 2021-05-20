import requests
import geocoder
import os
from flask import request
from datetime import datetime, timedelta
from icecream import ic as debug
from dotenv import load_dotenv

load_dotenv()


def get_user_latlng():
    userIp = geocoder.ip("me")  # <--- this works but userip doesnt?!
    userLocation = userIp.latlng
    return userLocation


def get_user_location():

    latlng = get_user_latlng()
    url = "https://maps.googleapis.com/maps/api/geocode/json?".format(
        request.remote_addr)

    try:
        params = {
            "key": os.environ.get("GOOGLE_KEY"),
            "latlng": str(latlng).strip("[]"),
        }
        userLocationData = requests.get(url, params=params)

        return userLocationData.json()

    except:
        print("There was an error")


def build_params():

    now = datetime.now()
    startTime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    endTime = now + timedelta(hours=5)
    latlng = get_user_latlng()

    timeSteps = [
        "current",
        "1h",
    ]

    fields = [
        "precipitationIntensity",
        "precipitationType",
        "windSpeed",
        "temperature",
        "temperatureApparent",
        "weatherCode",
    ]

    payload = {
        "apikey": os.environ.get("WEATHER_API_KEY"),
        "location": str(latlng).strip("[]"),
        "fields": fields,
        "units": "imperial",
        "timesteps": timeSteps,
        "startTime": startTime,
        "endTime": endTime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timezone": "America/New_York",
    }

    return payload


def get_user_weather():

    url = "https://data.climacell.co/v4/timelines?"
    weather = requests.get(url, params=build_params())

    return weather.json()
