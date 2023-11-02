import requests
import os
from flask import request
from datetime import datetime, timedelta
from icecream import ic as debug
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

load_dotenv()

class Weather:

    def get_client_ip(self):
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ip = request.remote_addr
        return ip
    
    def get_location(self):
        user_ip = self.get_client_ip()
        url = "https://ipinfo.io"
        params = {
            "ip": user_ip,
            "token": os.environ.get("IPINFO_KEY"),
        }

        userLocationData = requests.get(url, params=params).json()
        debug(user_ip, userLocationData)
        return userLocationData

    def build_params(self):

        now = datetime.now()
        startTime = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        endTime = now + timedelta(hours=5)
        latlng = self.get_location()

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

    def get_user_weather(self):

        # A method to slow down api calls so they arent rejected
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        url = "https://api.tomorrow.io/v4/timelines?"
        weather = session.get(url, params=self.build_params())

        return weather.json()
