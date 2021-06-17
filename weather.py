import requests
import geocoder
import os
from flask import request
from datetime import datetime, timedelta
from icecream import ic as debug
from dotenv import load_dotenv

load_dotenv()


class Weather():
    def get_user_latlng(self, ip):
        url = "https://ipgeolocation.abstractapi.com/v1/"
        params = {
            "api_key": os.environ.get("ABSTRACT_KEY"),
            "ip_address": str(ip),
        }

        userLocationData = requests.get(url, params=params)
        latlng = userLocationData.json()

        debug(latlng)
        return latlng

    def get_user_location(self,):

        latlng = self.get_user_latlng()
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

    def build_params(self, ip):

        now = datetime.now()
        startTime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        endTime = now + timedelta(hours=5)
        latlng = self.get_user_latlng(ip)

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
            "location": str(latlng.get("latitude")) + "," + str(latlng.get("longitude")),
            "fields": fields,
            "units": "imperial",
            "timesteps": timeSteps,
            "startTime": startTime,
            "endTime": endTime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timezone": "America/New_York",
        }
        debug(payload)
        return payload

    def get_user_weather(self, ip):

        url = "https://data.climacell.co/v4/timelines?"
        weather = requests.get(url, params=self.build_params(ip))
        debug(weather.json())
        return weather.json()

# ic| get_user_weather(): {'data': {'timelines': [{'endTime': '2021-06-02T20:19:00-04:00',
#                                                  'intervals': [{'startTime': '2021-06-02T20:19:00-04:00',
#                                                                 'values': {'precipitationIntensity': 0.0006,
#                                                                            'precipitationType': 1,
#                                                                            'temperature': 76.24,
#                                                                            'temperatureApparent': 76.24,
#                                                                            'weatherCode': 4000,
#                                                                            'windSpeed': 11.92}}],
#                                                  'startTime': '2021-06-02T20:19:00-04:00',
#                                                  'timestep': 'current'},
#                                                 {'endTime': '2021-06-02T21:00:00-04:00',
#                                                  'intervals': [{'startTime': '2021-06-02T16:00:00-04:00',
#                                                                 'values': {'precipitationIntensity': 0,
#                                                                            'precipitationType': 1,
#                                                                            'temperature': 80.37,
#                                                                            'temperatureApparent': 84.2,
#                                                                            'weatherCode': 1001,
#                                                                            'windSpeed': 12.57}},
#                                                                {'startTime': '2021-06-02T17:00:00-04:00',
#                                                                 'values': {'precipitationIntensity': 0,
#                                                                            'precipitationType': 1,
#                                                                            'temperature': 79.12,
#                                                                            'temperatureApparent': 79.12,
#                                                                            'weatherCode': 1001,
#                                                                            'windSpeed': 12.3}},
#                                                                {'startTime': '2021-06-02T18:00:00-04:00',
#                                                                 'values': {'precipitationIntensity': 0,
#                                                                            'precipitationType': 1,
#                                                                            'temperature': 77.22,
#                                                                            'temperatureApparent': 77.22,
#                                                                            'weatherCode': 1001,
#                                                                            'windSpeed': 6}},
#                                                                {'startTime': '2021-06-02T19:00:00-04:00',
#                                                                 'values': {'precipitationIntensity': 0,
#                                                                            'precipitationType': 1,
#                                                                            'temperature': 79.47,
#                                                                            'temperatureApparent': 79.47,
#                                                                            'weatherCode': 1001,
#                                                                            'windSpeed': 9.78}},
#                                                                {'startTime': '2021-06-02T20:00:00-04:00',
#                                                                 'values': {'precipitationIntensity': 0,
#                                                                            'precipitationType': 1,
#                                                                            'temperature': 76.42,
#                                                                            'temperatureApparent': 76.42,
#                                                                            'weatherCode': 1101,
#                                                                            'windSpeed': 11.88}},
#                                                                {'startTime': '2021-06-02T21:00:00-04:00',
#                                                                 'values': {'precipitationIntensity': 0.0132,
#                                                                            'precipitationType': 1,
#                                                                            'temperature': 75.42,
#                                                                            'temperatureApparent': 75.42,
#                                                                            'weatherCode': 4000,
#                                                                            'windSpeed': 12.17}}],
#                                                  'startTime': '2021-06-02T16:00:00-04:00',
#                                                  'timestep': '1h'}]},
#                          'warnings': [{'code': 246009,
#                                        'message': 'The timestep is not supported in full for the time '
#                                                   'range requested.',
#                                        'meta': {'from': 'now', 'timestep': 'current', 'to': '+1m'},
# 'to': '+1m'},
#                                        'type': 'Missing Time Range'}]}
