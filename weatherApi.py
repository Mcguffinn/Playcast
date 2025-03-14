import requests
import os
import logging
from flask import request
from datetime import datetime, timedelta
from icecream import ic as debug
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Dict, Any, Optional, Tuple
from flask import request, session

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

    # In weatherApi.py, modify the get_location_from_browser method
    def get_location_from_browser(self) -> Dict[str, Any]:
        """
        Get location from browser coordinates
        """
        try:
            # Get latitude and longitude from request parameters
            lat = request.args.get('lat')
            lng = request.args.get('lng')
            
            # Also check session for lat/lng if not in request params
            if not lat and 'user_lat' in session:
                lat = session.get('user_lat')
            if not lng and 'user_lng' in session:
                lng = session.get('user_lng')
            
            if not lat or not lng:
                logger.warning("Browser coordinates not provided, falling back to IP geolocation")
                return self.get_location_from_ip()
            
            logger.info(f"Using browser coordinates: {lat}, {lng}")
            
            # Try to get city, region, country information using reverse geocoding
            location_data = self.reverse_geocode(lat, lng)
            
            # Return location data with the browser coordinates
            return {
                "loc": f"{lat},{lng}",
                "city": location_data.get("city", "Unknown"),
                "region": location_data.get("region", "Unknown"),
                "country": location_data.get("country", "Unknown"),
                "timezone": location_data.get("timezone", "America/New_York")
            }
        except Exception as e:
            logger.error(f"Error getting location from browser: {str(e)}")
            return self.get_location_from_ip()

    def reverse_geocode(self, lat: str, lng: str) -> Dict[str, str]:
        """
        Get location details from coordinates using a reverse geocoding service
        """
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": lat,
                "lon": lng,
                "format": "json",
                "addressdetails": 1,
                "zoom": 10
            }
            
            headers = {
                "User-Agent": "PlaycastApp/1.0"  # Required by Nominatim
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            location_data = response.json()
            
            if not location_data or "address" not in location_data:
                return {"city": "Unknown", "region": "Unknown", "country": "Unknown", "timezone": "America/New_York"}
            
            address = location_data["address"]
            
            # Try different fields for city name based on what's available
            city = address.get("city") or address.get("town") or address.get("village") or "Unknown"
            
            return {
                "city": city,
                "region": address.get("state", "Unknown"),
                "country": address.get("country", "Unknown"),
                "timezone": "America/New_York"  # Would need a separate timezone API
            }
        except Exception as e:
            logger.error(f"Error in reverse geocoding: {str(e)}")
            return {"city": "Unknown", "region": "Unknown", "country": "Unknown", "timezone": "America/New_York"}

    def get_client_ip(self) -> str:
        """
        Get client IP address with improved header handling for Render.com deployment
        """
        headers_to_check = [
        'CF-Connecting-IP',
        'X-Forwarded-For',
        'X-Real-IP', 
        'X-Client-IP',
        'X-Forwarded',
        'Forwarded-For',
        'Forwarded',
        'True-Client-IP'
        ]
        
        # Log all headers for debugging
        logger.info(f"Headers: {dict(request.headers)}")
        
        for header in headers_to_check:
            if header in request.headers:
                value = request.headers[header]
                logger.info(f"Using {header}: {value}")
                if header == 'X-Forwarded-For':
                    # Extract first IP from potentially comma-separated list
                    return value.split(',')[0].strip()
                return value
        
        # Last resort
        logger.info(f"Using remote_addr: {request.remote_addr}")
        return request.remote_addr

    def get_location_from_ip(self) -> Dict[str, Any]:
        """
        Get location information from IP address as fallback
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
            
            # Use location from browser if available, otherwise fall back to IP
            location_data = self.get_location_from_browser()
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
                "timezone": location_data.get('timezone', "America/New_York"),
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