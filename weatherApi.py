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
    def get_user_ip(self, ip):
        url = "https://ipinfo.io".format(request.headers.get('X-Forwarded-For'))
        params = {
            # "ip": ip,
            "token": os.environ.get("IPINFO_KEY"),
        }

        userLocationData = requests.get(url, params=params).json()
        debug(request.headers.get('X-Forwarded-For'), userLocationData)
        
        return userLocationData


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

        #debug(payload)
        return payload

    def get_user_weather(self, ip):

        # A method to slow down api calls so they arent rejected
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        url = "https://api.tomorrow.io/v4/timelines?"
        weather = session.get(url, params=self.build_params(ip))
        debug(ip, weather.json())
        return weather.json()

# test = Weather()
# debug(test.get_user_location())