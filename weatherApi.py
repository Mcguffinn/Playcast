import requests
import os
import logging
from flask import request
from datetime import datetime, timedelta
from icecream import ic as debug
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Dict, Any

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Weather:
    def __init__(self):
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def get_client_ip(self) -> str:
        """
        Get client IP address with improved header handling for Render.com deployment
        """
        headers_debug = {
            'X-Forwarded-For': request.headers.get('X-Forwarded-For'),
            'CF-Connecting-IP': request.headers.get('CF-Connecting-IP'),
            'Remote-Addr': request.remote_addr
        }
        logger.info(f"Request headers: {headers_debug}")

        # Use CF-Connecting-IP as it's the most reliable for actual client IP
        if cf_ip := request.headers.get('CF-Connecting-IP'):
            logger.info(f"Using CF-Connecting-IP: {cf_ip}")
            return cf_ip
        
        # Fallback to first IP in X-Forwarded-For
        if x_forwarded_for := request.headers.get('X-Forwarded-For'):
            # Split on commas and get the first IP (client IP)
            client_ip = x_forwarded_for.split(',')[0].strip()
            logger.info(f"Using first X-Forwarded-For IP: {client_ip}")
            return client_ip

        # Last resort: use remote_addr
        logger.info(f"Using remote_addr: {request.remote_addr}")
        return request.remote_addr

    def get_location(self) -> Dict[str, Any]:
        """
        Get location information with improved error handling
        """
        try:
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
            
            # Log the actual location data received
            logger.info(f"Location data received: {location_data}")
            
            # Validate location data
            if 'loc' not in location_data or not location_data['loc']:
                raise ValueError("Invalid location data received from IPInfo")
            
            return location_data

        except Exception as e:
            logger.error(f"Error getting location: {str(e)}")
            # Return a default location as fallback
            return {
                "ip": user_ip,
                "city": "Orlando",  # Default to Orlando
                "region": "Florida",
                "country": "US",
                "loc": "28.6214,-81.4294",  # Orlando coordinates
                "timezone": "America/New_York"
            }

    def build_params(self) -> Dict[str, Any]:
        """
        Build weather API parameters
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
            
            # Log params without API key
            log_params = params.copy()
            log_params['apikey'] = '***'
            logger.info(f"Built weather API params: {log_params}")
            
            return params

        except Exception as e:
            logger.error(f"Error building parameters: {str(e)}")
            raise

    def get_user_weather(self) -> Dict[str, Any]:
        """
        Get weather data with error handling
        """
        try:
            url = "https://api.tomorrow.io/v4/timelines"
            params = self.build_params()
            
            logger.info("Requesting weather data from Tomorrow.io API")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            weather_data = response.json()
            logger.info("Successfully retrieved weather data")
            
            return weather_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting weather data: {str(e)}")
            raise