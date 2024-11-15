import requests
import os
import logging
from flask import request, current_app
from datetime import datetime, timedelta
from icecream import ic as debug
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Optional, Tuple, Dict, Any

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Weather:
    def __init__(self):
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a session with retry logic"""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def get_client_ip(self) -> str:
        """
        Get client IP address with detailed logging for debugging
        """
        # Log all relevant headers for debugging
        headers_debug = {
            'X-Forwarded-For': request.headers.get('X-Forwarded-For'),
            'X-Real-IP': request.headers.get('X-Real-IP'),
            'CF-Connecting-IP': request.headers.get('CF-Connecting-IP'),
            'Remote-Addr': request.remote_addr,
            'Host': request.headers.get('Host'),
        }
        logger.info(f"Request headers: {headers_debug}")

        # Check headers in priority order
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
            logger.info(f"Using X-Forwarded-For IP: {ip}")
            return ip
        
        if request.headers.get('X-Real-IP'):
            ip = request.headers.get('X-Real-IP')
            logger.info(f"Using X-Real-IP: {ip}")
            return ip
        
        if request.headers.get('CF-Connecting-IP'):
            ip = request.headers.get('CF-Connecting-IP')
            logger.info(f"Using CF-Connecting-IP: {ip}")
            return ip

        logger.info(f"Using remote_addr: {request.remote_addr}")
        return request.remote_addr

    def get_location(self) -> Dict[str, Any]:
        """
        Get location information with fallback options and error handling
        """
        try:
            # First try IP-based location
            user_ip = self.get_client_ip()
            logger.info(f"Attempting to get location for IP: {user_ip}")
            
            url = "https://ipinfo.io"
            params = {
                "ip": user_ip,
                "token": os.environ.get("IPINFO_KEY"),
            }

            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            location_data = response.json()
            
            # Validate location data
            if 'loc' not in location_data or not location_data['loc']:
                raise ValueError("Invalid location data received from IPInfo")
                
            logger.info(f"Successfully got location data: {location_data}")
            return location_data

        except Exception as e:
            logger.error(f"Error getting location: {str(e)}")
            # Fallback to a default location (e.g., New York City)
            return {
                "loc": "40.7128,-74.0060",  # NYC coordinates
                "city": "New York",
                "region": "New York",
                "country": "US"
            }

    def build_params(self) -> Dict[str, Any]:
        """
        Build weather API parameters with enhanced error handling
        """
        try:
            now = datetime.now()
            start_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_time = (now + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            location_data = self.get_location()
            logger.info(f"Building params with location data: {location_data}")
            
            fields = [
                "precipitationIntensity",
                "precipitationType",
                "windSpeed",
                "temperature",
                "temperatureApparent",
                "weatherCode",
            ]

            params = {
                "apikey": os.environ.get("WEATHER_API_KEY"),
                "location": location_data['loc'],
                "fields": fields,
                "units": "imperial",
                "timesteps": "1h",
                "startTime": start_time,
                "endTime": end_time,
                "timezone": "America/New_York",
            }
            
            logger.info(f"Built weather API params (excluding apikey): {params}")
            return params

        except Exception as e:
            logger.error(f"Error building parameters: {str(e)}")
            raise

    def get_user_weather(self) -> Dict[str, Any]:
        """
        Get weather data with comprehensive error handling and logging
        """
        try:
            url = "https://api.tomorrow.io/v4/timelines"
            params = self.build_params()
            
            logger.info("Requesting weather data from Tomorrow.io API")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Validate weather data
            if 'data' not in weather_data or 'timelines' not in weather_data['data']:
                raise ValueError("Invalid weather data received from API")
            
            logger.info("Successfully retrieved weather data")
            # Log the first interval's weather code for debugging
            first_interval = weather_data['data']['timelines'][0]['intervals'][0]
            logger.info(f"Weather code: {first_interval['values'].get('weatherCode')}")
            
            return weather_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting weather data: {str(e)}")
            # Return a minimal error response that won't break the frontend
            return {
                "data": {
                    "timelines": [{
                        "intervals": [{
                            "values": {
                                "weatherCode": 1000,  # Clear weather as default
                                "temperature": 70,  # Default temperature
                            }
                        }]
                    }]
                }
            }