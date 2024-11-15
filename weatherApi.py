import requests
import os
from flask import request
from datetime import datetime, timedelta
from icecream import ic as debug
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Optional

load_dotenv()

class Weather:

    def get_client_ip(self) -> str:
        """
        Get the real client IP address when behind a reverse proxy.
        Checks various headers in order of preference while considering security.
        """
        # List of proxy-related headers to check in order of preference
        PROXY_HEADERS = [
            'X-Forwarded-For',
            'X-Real-IP',
            'CF-Connecting-IP',  # Cloudflare
            'True-Client-IP'
        ]
        
        # Check proxy headers first
        for header in PROXY_HEADERS:
            ip_header = request.headers.get(header)
            if ip_header:
                # X-Forwarded-For can contain multiple IPs; get the first one
                # which is typically the original client IP
                return ip_header.split(',')[0].strip()
        
        # Fall back to remote_addr if no proxy headers are present
        return request.remote_addr
    
    def validate_ip(self, ip: str) -> bool:
        """
        Basic validation for IPv4 and IPv6 addresses.
        """
        try:
            # Split IP into octets
            if '.' in ip:  # IPv4
                octets = ip.split('.')
                if len(octets) != 4:
                    return False
                return all(0 <= int(octet) <= 255 for octet in octets)
            elif ':' in ip:  # IPv6
                # Basic IPv6 validation
                parts = ip.split(':')
                return len(parts) <= 8
            return False
        except (ValueError, AttributeError):
            return False
        
    def get_location(self) -> dict:
        """
        Get location information based on the client's IP address.
        Returns location data from ipinfo.io.
        """
        user_ip = self.get_client_ip()
        
        if not self.validate_ip(user_ip):
            raise ValueError(f"Invalid IP address: {user_ip}")

        url = "https://ipinfo.io"
        params = {
            "ip": user_ip,
            "token": os.environ.get("IPINFO_KEY"),
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            debug(f"Error getting location data: {e}")
            raise


    def build_params(self) -> dict:
        """
        Build parameters for the weather API request.
        Uses location data to get weather information.
        """
        now = datetime.now()
        start_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = (now + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        try:
            location_data = self.get_location()
            # Location data typically includes lat,lng in the format "12.345,-67.890"
            latlng = location_data.get('loc')
            
            if not latlng:
                raise ValueError("Could not determine location coordinates")
            
            fields = [
                "precipitationIntensity",
                "precipitationType",
                "windSpeed",
                "temperature",
                "temperatureApparent",
                "weatherCode",
            ]

            return {
                "apikey": os.environ.get("WEATHER_API_KEY"),
                "location": latlng,
                "fields": fields,
                "units": "imperial",
                "timesteps": "1h",
                "startTime": start_time,
                "endTime": end_time,
                "timezone": "America/New_York",
            }
        except Exception as e:
            debug(f"Error building parameters: {e}")
            raise

    def get_user_weather(self) -> dict:
        """
        Get weather data for the user's location.
        Implements retry logic for API stability.
        """
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        url = "https://api.tomorrow.io/v4/timelines"
        
        try:
            response = session.get(url, params=self.build_params(), timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            debug(f"Error getting weather data: {e}")
            raise
