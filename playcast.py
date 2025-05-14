import os
import logging
import re
import time
import random
from flask import session
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import (Flask, render_template, jsonify, request, redirect, session, make_response)
from dotenv import load_dotenv
from spotifyApi import SpotifyAPI
from weatherApi import Weather
from icecream import ic as debug
from datetime import timedelta, datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['PROXY_FIX_FOR'] = 1  # Number of proxies in front of your app
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.secret_key = os.environ.get("SECRET_KEY")

app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

if os.environ.get("FLASK_ENV") == "development":
    app.debug = True
    port = os.environ.get("PORT")
    logging.debug("Started server, site: " + "http://localhost:" + str(port))
else:
    app.debug = False

weather = Weather()
spotify = SpotifyAPI(
    client_id=os.environ.get("CLIENT_ID"),
    client_secret=os.environ.get("CLIENT_SECERET"),
)

weatherInfo = {
    4201: ["Heavy Rain", "static/icons/rain_heavy.svg"],
    4001: ["Rain", "static/icons/rain.svg"],
    4200: ["Light Rain", "static/icons/rain_light.svg"],
    6201: ["Heavy Freezing Rain", "static/icons/freezing_rain_heavy.svg"],
    6001: ["Freezing Rain", "static/icons/freezing_rain.svg"],
    6200: ["Light Freezing Rain", "static/icons/freezing_rain_light.svg"],
    6000: ["Freezing Drizzle", "static/icons/freezing_drizzle.svg"],
    4000: ["Drizzle", "static/icons/drizzle.svg"],
    7101: ["Heavy Ice Pellets", "static/icons/ice_pellets_heavy.svg"],
    7000: ["Ice Pellets", "static/icons/ice_pellets.svg"],
    7102: ["Light Ice Pellets", "static/icons/ice_pellets_light.svg"],
    5101: ["Heavy Snow", "static/icons/snow_heavy.svg"],
    5000: ["Snow", "static/icons/snow.svg"],
    5100: ["Light Snow", "static/icons/snow_light.svg"],
    5001: ["Flurries", "static/icons/flurries.svg"],
    8000: ["Thunderstorm", "static/icons/tstorm.svg"],
    2100: ["Light Fog", "static/icons/fog_light.svg"],
    2000: ["Fog", "static/icons/fog.svg"],
    1001: ["Cloudy", "static/icons/cloudy.svg"],
    1102: ["Mostly Cloudy", "static/icons/mostly_cloudy.svg"],
    1101: ["Partly Cloudy", "static/icons/partly_cloudy_day.svg"],
    1100: ["Mostly Clear", "static/icons/mostly_clear_day.svg"],
    1000: ["Clear", "static/icons/clear_day.svg"],
}

# Session-based weather cache to avoid multiple API calls per session
_weather_cache = {}

@app.after_request
def add_cors_headers(response):
    if os.environ.get("FLASK_ENV") == "development":
        response.headers['Access-Control-Allow-Origin'] = '*'
    else:
        # In production, only allow your domain
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@app.before_request
def validate_session():
    if request.endpoint in ['playcast', 'play_playlist']:
        if 'current_playlist' in session:
            # Check playlist expiration
            if session['current_playlist'].get('expires_at', 0) < time.time():
                session.pop('current_playlist', None)

@app.route('/api/weather', methods=['OPTIONS'])
@app.route('/api/update-location', methods=['OPTIONS'])
@app.route('/api/ip-location', methods=['OPTIONS'])
def handle_options():
    return '', 204

@app.route("/")
def index():
    return render_template("base.html")

@app.route("/home", methods=["GET", "POST"])
def get_weather_status():
    try:
        # Create cache key from user session id and current hour
        session_id = session.get('_id', request.cookies.get('session', 'default'))
        now = datetime.now()
        hour_key = f"{now.year}-{now.month}-{now.day}-{now.hour}"
        cache_key = f"{session_id}_{hour_key}"

        # Check if we have cached weather for this session in this hour
        if cache_key in _weather_cache and time.time() < _weather_cache[cache_key]["expires"]:
            logger.info("Using cached weather status for this session")
            return _weather_cache[cache_key]["data"]

        # Store lat/lng in session if provided
        params = {
            'lat': request.args.get('lat') or session.get('user_lat'),
            'lng': request.args.get('lng') or session.get('user_lng')
        }
        
        # Only include params that have values
        params = {k: v for k, v in params.items() if v}
        
        # Get weather data (optimized with caching in the Weather class)
        key = weather.get_user_weather()
        weatherCodes = key["data"]["timelines"][0]["intervals"][0]["values"]
        mark = weatherCodes.get("weatherCode")
        svg = weatherInfo[mark]
        temp = weatherCodes.get("temperature")
        weatherStatus = weatherInfo[mark]

        # Cache the result for 15 minutes
        result = (svg[1], str(temp), weatherStatus[0])
        _weather_cache[cache_key] = {
            "data": result,
            "timestamp": time.time(),
            "expires": time.time() + 900  #15 min
        }

        return result
    except Exception as e:
        logger.error(f"Error getting weather status: {str(e)}")
        # Return a default in case of error
        return ("static/icons/clear_day.svg", "75", "Clear")


def extract_playlist_id(spotify_url):
    """Extract the playlist ID from a Spotify URL"""
    # Check if it's already an ID (no slashes)
    if '/' not in spotify_url:
        return spotify_url
        
    # Try to extract using regex
    match = re.search(r'playlist/([a-zA-Z0-9]+)', spotify_url)
    if match:
        return match.group(1)
    return None


@app.route("/playlist/<query>")
def get_playlist_data(query):
    try:
        logger.info(f"Searching for playlists with query: {query}")

        weather_variations = {
            "Clear": ["clear day", "sunny playlist", "sunshine vibes", query + " day"],
            "Mostly Clear": ["mostly clear", "sunny tunes", "bright day", query + " music"],
            "Partly Cloudy": ["partly cloudy", "mild weather", "light clouds", query + " mix"],
            "Cloudy": ["cloudy day", "overcast mood", "gray skies", query + " playlist"],
            "Rain": ["rainy day", "rain sounds", "rainy mood", query + " rain"],
            "Light Rain": ["light rain", "drizzle vibes", "gentle rain", query + " drizzle"],
            "Heavy Rain": ["heavy rain", "storm playlist", "rainstorm", query + " downpour"],
            "Snow": ["snowy day", "winter playlist", "snow vibes", query + " snow"],
            "Thunderstorm": ["thunderstorm", "stormy weather", "thunder sounds", query + " storm"],
            "Fog": ["foggy day", "misty morning", "fog music", query + " mist"],
            # Add more variations for other weather conditions
        }
        
        # Get variations for this weather condition, or just use the query if no specific variations
        query_variations = weather_variations.get(query, [query, query + " playlist", query + " music"])
        
        # Pick a random variation
        random_query = random.choice(query_variations)
        logger.info(f"Using randomized query: {random_query} (based on {query})")

        data = spotify.search(query=random_query, search_type="playlist")
        
        playlistData = []
        
        # Safely handle API response structure
        items = data.get("playlists", {}).get("items", []) if data else []
        
        for item in items:
            # Skip None items and items missing critical data
            if not item or not isinstance(item, dict):
                logger.warning("Skipping invalid playlist item")
                continue

            # Original processing logic with added safety checks
            try:
                # Images handling
                if not item.get("images") or len(item["images"]) == 0:
                    image = "static/icons/default_playlist.svg"
                else:
                    first_image = item["images"][0]
                    image = first_image["url"] if first_image else "static/icons/default_playlist.svg"

                # Name handling
                name = item.get("name", "Unnamed Playlist")

                # URL handling
                external_urls = item.get("external_urls", {})
                outurl = external_urls.get("spotify", "https://open.spotify.com")
                playlist_id = extract_playlist_id(outurl)

                # Description handling
                description = item.get("description", "No description available")

                playlistData.append({
                    "image": image,
                    "name": name,
                    "description": description,
                    "outurl": outurl,
                    "id": playlist_id
                })
                
            except Exception as item_error:
                logger.warning(f"Skipping invalid playlist item: {str(item_error)}")
                continue

        random.shuffle(playlistData)

        max_playlists = 9
        if len(playlistData) > max_playlists:
            playlistData = playlistData[:max_playlists]

        # Fallback to default playlist if empty
        if not playlistData:
            logger.info("Returning default playlist")
            return [{
                "image": "static/icons/default_playlist.svg",
                "name": "No playlists found",
                "description": f"No playlists found for '{query}'. Try a different search term.",
                "outurl": "https://open.spotify.com",
                "id": ""
            }]

        return playlistData
        
    except Exception as e:
        logger.error(f"Error in get_playlist_data: {str(e)}", exc_info=True)
        return [{
            "image": "static/icons/default_playlist.svg",
            "name": "Error finding playlists",
            "description": "We encountered an error finding playlists. Please try again later.",
            "outurl": "https://open.spotify.com",
            "id": ""
        }]


@app.route("/play-playlist/<playlist_id>")
def play_playlist(playlist_id):
    try:
        # Validate playlist ID format first
        if not re.match(r'^[a-zA-Z0-9]{22}$', playlist_id):
            return jsonify({"success": False, "message": "Invalid playlist ID format"}), 400

        # Get playlist details with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                playlist_details = spotify.get_playlist(playlist_id)
                if playlist_details and 'error' not in playlist_details:
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.5)

        # Validate critical response data
        required_fields = ['id', 'name', 'external_urls']
        for field in required_fields:
            if field not in playlist_details:
                raise ValueError(f"Missing required field: {field}")

        # Store playlist data with expiration timestamp
        session['current_playlist'] = {
            'id': playlist_id,
            'name': playlist_details['name'],
            'image': playlist_details['images'][0]['url'] if playlist_details.get('images') else 'static/icons/default_playlist.svg',
            'expires_at': time.time() + 3600  # 1 hour validity
        }

        # Force session save
        session.modified = True
        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Playlist error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to load playlist details",
            "debug": str(e)
        }), 500


@app.route("/playcast")
def playcast():
    try:
        # Get location info from browser parameters
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        
        # Save these parameters to the session to persist them
        if lat and lng:
            session['user_lat'] = lat
            session['user_lng'] = lng
            
        # Get weather info using browser location
        location_data = weather.get_location_from_browser()
        city = location_data.get('city', 'Unknown')
        region = location_data.get('region', 'Unknown')
        
        # Get weather info
        weatherInfo = get_weather_status()
        (weatherSVG, temperature, weatherStatus) = weatherInfo
        
        # Check if there's a current playlist from session
        current_playlist = session.get('current_playlist', {})
        
        logger.info(f"Current playlist from session: {current_playlist}")
        
        # Get playlist data
        playlist = get_playlist_data(weatherStatus)
        
        response = make_response(render_template(
            "playlist.html",
            playlistData=playlist,
            weatherSVG=weatherSVG,
            weatherStatus=weatherStatus,
            temperature=temperature,
            city=city,
            region=region,
            currentPlaylist=current_playlist
        ))

        response.headers['Content-Security-Policy'] = "frame-src 'self' https://*.spotify.com;"

        return response
    
    except Exception as e:
        logger.error(f"Error in playcast route: {str(e)}")
        return render_template(
            "base.html",
            error_message="We couldn't load your weather-based playlist right now. Please try again later."
        )


@app.route("/api/weather")
def api_weather():
    """
    API endpoint to get weather data
    This allows the frontend to request weather with browser location
    """
    try:
        # Save the lat/lng to session if provided
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        
        # Log the complete request information for debugging
        logger.info(f"Weather API request: {request.url}, Args: {request.args}, IP: {request.remote_addr}")
        
        if lat and lng:
            try:
                lat_f = float(lat)
                lng_f = float(lng)
                if not (-90 <= lat_f <= 90) or not (-180 <= lng_f <= 180):
                    raise ValueError
                session['user_lat'] = lat
                session['user_lng'] = lng
                logger.info(f"Valid coordinates saved: {lat}, {lng}")
            except ValueError:
                logger.warning(f"Invalid coordinates received: {lat}, {lng}")
        
        # Check if we have coordinates
        if 'user_lat' in session and 'user_lng' in session:
            logger.info(f"Using session coordinates: {session['user_lat']}, {session['user_lng']}")
        else:
            logger.warning("No coordinates in session, using IP location")
        
        # Get location data
        location_data = weather.get_location_from_browser()
        
        # Get weather info
        weatherInfo = get_weather_status()
        (weatherSVG, temperature, weatherStatus) = weatherInfo
        
        city = location_data.get('city', 'Unknown')
        region = location_data.get('region', 'Unknown')
        
        logger.info(f"Sending location data: {city}, {region}")
        
        return jsonify({
            "weatherSVG": weatherSVG,
            "temperature": temperature,
            "weatherStatus": weatherStatus,
            "city": city,
            "region": region
        })
    except Exception as e:
        logger.error(f"Error in weather API: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/update-location")
def update_location():
    """API endpoint to update session with browser location"""
    try:
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        
        if lat and lng:
            session['user_lat'] = lat
            session['user_lng'] = lng
            logger.info(f"Updated user location in session: {lat}, {lng}")
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Missing coordinates"}), 400
    except Exception as e:
        logger.error(f"Error updating location: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/ip-location")
def ip_location():
    """API endpoint to get location based on IP address"""
    try:
        # Get location from IP as fallback when browser geolocation fails
        weather_instance = Weather()
        location_data = weather_instance.get_location_from_ip()
        
        # Log what we're sending back
        logger.info(f"Providing IP-based location: {location_data}")
        
        return jsonify(location_data)
    except Exception as e:
        logger.error(f"Error getting IP location: {str(e)}")
        return jsonify({
            "city": "Orlando",  # Default to Orlando
            "region": "Florida",
            "country": "US",
            "loc": "28.6214,-81.4294",  # Orlando coordinates
            "timezone": "America/New_York"
        })
      
@app.route("/debug-weather")
def debug_weather():
    try:
        weather_instance = Weather()
        client_ip = weather_instance.get_client_ip()
        browser_location = weather_instance.get_location_from_browser()
        ip_location = weather_instance.get_location_from_ip()
        weather_data = weather_instance.get_user_weather()
        
        return {
            "client_ip": client_ip,
            "browser_location": browser_location,
            "ip_location": ip_location,
            "weather": weather_data
        }
    except Exception as e:
        return {"error": str(e)}, 500
    
if __name__ == "__main__":
    app.run(debug=app.debug, port=int(os.environ.get("PORT", 5000)))