import requests
import geocoder
import socket
import os
import logging
import json
import types
from datetime import datetime, timedelta
from icecream import ic as debug
from dotenv import load_dotenv

load_dotenv()


def get_user_latlng():
    # userLocation = userLocationData.state + userLocationData.city
    userIp = geocoder.ip("me")  # <--- this works but userip doesnt?!
    userLocation = userIp.latlng
    return userLocation


def get_user_location():

    latlng = get_user_latlng()
    url = "https://maps.googleapis.com/maps/api/geocode/json?"

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

    fakeload = {
        "data": {
            "timelines": [
                {
                    "endTime": "2021-04-01T22:40:00-04:00",
                    "intervals": [
                        {
                            "startTime": "2021-04-01T22:40:00-04:00",
                            "values": {
                                "precipitationIntensity": 0,
                                "precipitationType": 1,
                                "temperature": 59.22,
                                "temperatureApparent": 59.22,
                                "weatherCode": 5100,
                                "windSpeed": 8.95,
                            },
                        }
                    ],
                    "startTime": "2021-04-01T22:40:00-04:00",
                    "timestep": "current",
                },
                {
                    "endTime": "2021-04-01T23:40:00-04:00",
                    "intervals": [
                        {
                            "startTime": "2021-04-01T18:40:00-04:00",
                            "values": {
                                "precipitationIntensity": 0,
                                "precipitationType": 1,
                                "temperature": 64.06,
                                "temperatureApparent": 64.06,
                                "weatherCode": 1100,
                                "windSpeed": 10.35,
                            },
                        },
                        {
                            "startTime": "2021-04-01T19:40:00-04:00",
                            "values": {
                                "precipitationIntensity": 0,
                                "precipitationType": 1,
                                "temperature": 62.04,
                                "temperatureApparent": 62.04,
                                "weatherCode": 1100,
                                "windSpeed": 9.93,
                            },
                        },
                        {
                            "startTime": "2021-04-01T20:40:00-04:00",
                            "values": {
                                "precipitationIntensity": 0,
                                "precipitationType": 1,
                                "temperature": 61.14,
                                "temperatureApparent": 61.14,
                                "weatherCode": 1100,
                                "windSpeed": 7.97,
                            },
                        },
                        {
                            "startTime": "2021-04-01T21:40:00-04:00",
                            "values": {
                                "precipitationIntensity": 0,
                                "precipitationType": 1,
                                "temperature": 59.79,
                                "temperatureApparent": 59.79,
                                "weatherCode": 1000,
                                "windSpeed": 7.69,
                            },
                        },
                        {
                            "startTime": "2021-04-01T22:40:00-04:00",
                            "values": {
                                "precipitationIntensity": 0,
                                "precipitationType": 1,
                                "temperature": 59.22,
                                "temperatureApparent": 59.22,
                                "weatherCode": 1000,
                                "windSpeed": 8.95,
                            },
                        },
                        {
                            "startTime": "2021-04-01T23:40:00-04:00",
                            "values": {
                                "precipitationIntensity": 0,
                                "precipitationType": 1,
                                "temperature": 56.52,
                                "temperatureApparent": 56.52,
                                "weatherCode": 1000,
                                "windSpeed": 7.54,
                            },
                        },
                    ],
                    "startTime": "2021-04-01T18:40:00-04:00",
                    "timestep": "1h",
                },
            ]
        },
        "warnings": [
            {
                "code": 246009,
                "message": "The timestep is not supported in full for the time "
                "range requested.",
                "meta": {"from": "now", "timestep": "current", "to": "+1m"},
                "type": "Missing Time Range",
            }
        ],
    }
    # return weather.json()

    return fakeload


# debug(get_user_weather())

# def get_svg():
#     currentWeather = get_user_weather()
#     finalIcon = ''
    
    
#     key = currentWeather["data"]["timelines"][0]["intervals"][0]["values"]["weatherCode"]
    

#     if key in weatherCodes.keys():
#         svg = open(weatherCodes[key][1]).read()
#         print(weatherCodes[key])
    
#     # svgFile= open('./icons/color/{}')
#     return (svg,key )

# debug(get_svg())