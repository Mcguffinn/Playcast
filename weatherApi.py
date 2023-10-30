import requests
import geocoder
import os
from flask import request
from datetime import datetime, timedelta
from icecream import ic as debug
from dotenv import load_dotenv

load_dotenv()

class Weather:
    def get_user_ip(self, ip):
        url = "https://ipinfo.io"
        params = {
            "ip": ip,
            "token": os.environ.get("IPINFO_KEY"),
        }

        userLocationData = requests.get(url, params=params).json()

        return userLocationData

    def get_user_location(
        self, ip
    ):

        response = requests.get("http://ip-api.com/json/{}".format(ip))
        js = response.json()
        # country = js['countryCode']
        debug(js, ip)
        return js


    def build_params(self, ip):

        now = datetime.now()
        startTime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        endTime = now + timedelta(hours=5)
        latlng = self.get_user_ip(ip)

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
            "location": str(latlng.get("loc")),
            "fields": fields,
            "units": "imperial",
            "timesteps": "1h",
            "startTime": startTime,
            "endTime": endTime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timezone": "America/New_York",
        }

        return payload

    def get_user_weather(self, ip):

        url = "https://data.climacell.co/v4/timelines?"
        weather = requests.get(url, params=self.build_params(ip))

        return weather.json()
