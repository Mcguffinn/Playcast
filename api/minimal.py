import os
import sys
import json
import random
import traceback
import urllib.request
import urllib.error
import urllib.parse
import base64
from datetime import datetime
from flask import Flask, jsonify, request, render_template, redirect, make_response, session, url_for, send_from_directory

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get absolute paths for better reliability
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_folder = os.path.join(base_dir, 'static')
template_folder = os.path.join(base_dir, 'templates')

# Weather codes mapping (simplified from original app)
WEATHER_INFO = {
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

# Helper function to fetch JSON data from a URL using urllib
def fetch_json_data(url, timeout=5):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Playcast Weather App'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except urllib.error.URLError as e:
        print(f"URL Error: {e}")
        return None
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching data: {e}")
        return None

# Weather API function that uses urllib instead of requests
def get_real_weather(lat=None, lng=None):
    try:
        # Default coordinates if none provided (Orlando, FL)
        if not lat or not lng:
            lat = "28.5383"
            lng = "-81.3792"
        
        # Get your API key from environment or use a test key
        api_key = os.environ.get("TOMORROW_IO_API_KEY")
        if not api_key:
            print("No Tomorrow.io API key found, using mock weather data")
            return ("static/icons/clear_day.svg", "75", "Clear")
        
        # Tomorrow.io API URL
        url = f"https://api.tomorrow.io/v4/weather/realtime?location={lat},{lng}&apikey={api_key}"
        
        data = fetch_json_data(url)
        if not data:
            print("Failed to fetch weather data")
            return ("static/icons/clear_day.svg", "75", "Clear")
        
        # Extract weather data
        weather_code = data.get("data", {}).get("values", {}).get("weatherCode")
        temperature = data.get("data", {}).get("values", {}).get("temperature")
        
        # If weather code is not in our mapping, default to Clear
        if weather_code not in WEATHER_INFO:
            return ("static/icons/clear_day.svg", str(temperature), "Clear")
        
        # Get weather info from mapping
        weather_info = WEATHER_INFO[weather_code]
        return (weather_info[1], str(temperature), weather_info[0])
    except Exception as e:
        print(f"Error getting weather: {str(e)}")
        # Return default in case of error
        return ("static/icons/clear_day.svg", "75", "Clear")

# Create a simple Flask app with explicit paths
app = Flask(__name__, 
            static_url_path='/static', 
            static_folder=static_folder,
            template_folder=template_folder)

# Print paths for debugging
print(f"Base directory: {base_dir}")
print(f"Static folder path: {static_folder}")
print(f"Template folder path: {template_folder}")

app.secret_key = os.environ.get("SECRET_KEY", "vercel-deployment-key")

# Explicit route for static files as a fallback
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(static_folder, path)

# Add CORS headers
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

# Handle OPTIONS requests
@app.route('/api/weather', methods=['OPTIONS'])
@app.route('/api/update-location', methods=['OPTIONS'])
@app.route('/api/ip-location', methods=['OPTIONS'])
def handle_options():
    return '', 204

# Mock playlist data for demonstration
SAMPLE_PLAYLISTS = [
    {
        "image": "https://i.scdn.co/image/ab67706c0000da84c0b5f1c90bb3d3fee05ab25d",
        "name": "Sunny Day Playlist",
        "description": "Bright tunes for a sunny day",
        "outurl": "https://open.spotify.com/playlist/37i9dQZF1DX6P1Nck3wgwJ",
        "id": "37i9dQZF1DX6P1Nck3wgwJ"
    },
    {
        "image": "https://i.scdn.co/image/ab67706c0000da84fc2129f9e2ff6df521158fcf",
        "name": "Rainy Day Vibes",
        "description": "Perfect for watching raindrops on your window",
        "outurl": "https://open.spotify.com/playlist/37i9dQZF1DXbvABJXBIyiY",
        "id": "37i9dQZF1DXbvABJXBIyiY"
    },
    {
        "image": "https://i.scdn.co/image/ab67706c0000da8491a75738158f9c42e53a0bce",
        "name": "Cloudy Day Tunes",
        "description": "Mellow tracks for overcast skies",
        "outurl": "https://open.spotify.com/playlist/37i9dQZF1DX4E3UdUs7fUx",
        "id": "37i9dQZF1DX4E3UdUs7fUx"
    }
]

# Add a direct HTML template in case the regular templates don't load
FALLBACK_BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Playcast</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <style>
        /* Fallback styles in case the CSS doesn't load */
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            color: #333;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 1100px;
            margin: auto;
            padding: 20px;
            text-align: center;
        }
        h1 {
            color: #2A5DB0;
            margin-bottom: 20px;
        }
        button {
            background-color: #2A5DB0;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #1D4995;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Playcast</h1>
        <p>Discover playlists that match your weather!</p>
        <button id="getWeatherBtn">Get a Playcast</button>
    </div>
    
    <script>
        document.getElementById('getWeatherBtn').addEventListener('click', function() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    window.location.href = `/playcast?lat=${lat}&lng=${lng}`;
                }, function(error) {
                    console.error("Error getting location:", error);
                    window.location.href = '/playcast';
                });
            } else {
                console.error("Geolocation is not supported by this browser");
                window.location.href = '/playcast';
            }
        });
    </script>
</body>
</html>
"""

# Add a fallback route that uses the direct HTML
@app.route("/fallback")
def fallback_index():
    """Fallback index page with inline HTML"""
    return FALLBACK_BASE_HTML

@app.route("/")
def index():
    """Index route that renders the base template"""
    try:
        print("Attempting to render index page from template")
        return render_template("base.html")
    except Exception as e:
        print(f"Error rendering template: {str(e)}, using fallback HTML")
        return FALLBACK_BASE_HTML

# Redirect from home to playcast (for the Get a Playcast button)
@app.route("/home", methods=["GET", "POST"])
def home():
    """Redirect to playcast with coordinates"""
    # Get coordinates from request
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    
    # Build the playcast URL with coordinates if available
    if lat and lng:
        playcast_url = f"/playcast?lat={lat}&lng={lng}"
    else:
        playcast_url = "/playcast"
    
    print(f"Redirecting to: {playcast_url}")
    return redirect(playcast_url)

# For backwards compatibility
@app.route("/get_weather_status", methods=["GET", "POST"])
def get_weather_status():
    """Get real weather status"""
    lat = request.args.get('lat') or session.get('user_lat')
    lng = request.args.get('lng') or session.get('user_lng')
    
    # If we got coordinates in this request, store them in session
    if lat and lng:
        session['user_lat'] = lat
        session['user_lng'] = lng
    
    # Get real weather data
    return get_real_weather(lat, lng)

# Simplified Spotify API client using urllib instead of requests
def get_spotify_playlists(query):
    """Get Spotify playlists matching a query using urllib"""
    try:
        # Get Spotify API credentials
        client_id = os.environ.get("CLIENT_ID")
        client_secret = os.environ.get("CLIENT_SECERET")
        
        if not client_id or not client_secret:
            print("No Spotify credentials found, using sample playlists")
            return None
        
        # Get an access token first
        token_url = "https://accounts.spotify.com/api/token"
        auth_bytes = f"{client_id}:{client_secret}".encode('ascii')
        auth_header = f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"
        
        token_headers = {
            "Authorization": auth_header,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        token_data = "grant_type=client_credentials"
        
        # Create a request for the token
        token_req = urllib.request.Request(
            token_url, 
            data=token_data.encode('ascii'),
            headers=token_headers
        )
        
        # Get the token
        with urllib.request.urlopen(token_req) as token_response:
            token_data = json.loads(token_response.read().decode('utf-8'))
            access_token = token_data.get('access_token')
            
            if not access_token:
                print("Failed to get Spotify access token")
                return None
                
            # Now search for playlists
            search_url = f"https://api.spotify.com/v1/search?q={urllib.parse.quote(query)}&type=playlist&limit=12"
            search_headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            search_req = urllib.request.Request(search_url, headers=search_headers)
            
            with urllib.request.urlopen(search_req) as search_response:
                search_data = json.loads(search_response.read().decode('utf-8'))
                return search_data.get('playlists', {}).get('items', [])
                
    except Exception as e:
        print(f"Error fetching Spotify playlists: {str(e)}")
        return None

@app.route("/playlist/<query>")
def get_playlist_data(query):
    """Return playlist data for a given weather type"""
    try:
        # Try to get real Spotify playlists
        spotify_playlists = get_spotify_playlists(query)
        
        # If we couldn't get real playlists, use sample data
        if not spotify_playlists:
            playlists = SAMPLE_PLAYLISTS.copy()
            random.shuffle(playlists)
            
            # Modify the first playlist to match the query for better UX
            if playlists:
                playlists[0]["name"] = f"{query.title()} Day Playlist"
                playlists[0]["description"] = f"Perfect for {query.lower()} weather"
            
            return playlists
            
        # Process real Spotify playlists
        processed_playlists = []
        for item in spotify_playlists:
            try:
                # Get the image
                image = "static/icons/default_playlist.svg"
                if item.get("images") and len(item["images"]) > 0:
                    image = item["images"][0].get("url", image)
                
                # Get the name
                name = item.get("name", "Unnamed Playlist")
                
                # Get the URL and ID
                external_urls = item.get("external_urls", {})
                outurl = external_urls.get("spotify", "https://open.spotify.com")
                
                # Extract playlist ID from URL
                playlist_id = outurl.split("/")[-1] if "/" in outurl else outurl
                
                # Get description
                description = item.get("description", "No description available")
                
                processed_playlists.append({
                    "image": image,
                    "name": name,
                    "description": description,
                    "outurl": outurl,
                    "id": playlist_id
                })
            except Exception as e:
                print(f"Error processing playlist item: {str(e)}")
                
        # Limit to 9 playlists
        if len(processed_playlists) > 9:
            processed_playlists = processed_playlists[:9]
            
        # If no playlists were processed, fall back to sample data
        if not processed_playlists:
            return SAMPLE_PLAYLISTS
            
        return processed_playlists
    except Exception as e:
        print(f"Error in get_playlist_data: {str(e)}")
        return [{
            "image": "static/icons/default_playlist.svg",
            "name": "Error finding playlists",
            "description": f"We encountered an error: {str(e)}",
            "outurl": "https://open.spotify.com",
            "id": ""
        }]

# Get a specific Spotify playlist by ID
def get_spotify_playlist_by_id(playlist_id):
    """Get details for a specific Spotify playlist using urllib"""
    try:
        # Get Spotify API credentials
        client_id = os.environ.get("CLIENT_ID")
        client_secret = os.environ.get("CLIENT_SECERET")
        
        if not client_id or not client_secret:
            print("No Spotify credentials found, using sample playlists")
            return None
        
        # Get an access token first
        token_url = "https://accounts.spotify.com/api/token"
        auth_bytes = f"{client_id}:{client_secret}".encode('ascii')
        auth_header = f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"
        
        token_headers = {
            "Authorization": auth_header,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        token_data = "grant_type=client_credentials"
        
        # Create a request for the token
        token_req = urllib.request.Request(
            token_url, 
            data=token_data.encode('ascii'),
            headers=token_headers
        )
        
        # Get the token
        with urllib.request.urlopen(token_req) as token_response:
            token_data = json.loads(token_response.read().decode('utf-8'))
            access_token = token_data.get('access_token')
            
            if not access_token:
                print("Failed to get Spotify access token")
                return None
                
            # Now get the playlist
            playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
            playlist_headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            playlist_req = urllib.request.Request(playlist_url, headers=playlist_headers)
            
            with urllib.request.urlopen(playlist_req) as playlist_response:
                return json.loads(playlist_response.read().decode('utf-8'))
                
    except Exception as e:
        print(f"Error fetching Spotify playlist: {str(e)}")
        return None

@app.route("/play-playlist/<playlist_id>")
def play_playlist(playlist_id):
    """Handle playlist selection"""
    try:
        # Try to get the real playlist from Spotify
        playlist_details = get_spotify_playlist_by_id(playlist_id)
        
        if not playlist_details:
            # If we couldn't get the real playlist, find in samples or create a default
            selected_playlist = next((p for p in SAMPLE_PLAYLISTS if p["id"] == playlist_id), None)
            
            if not selected_playlist:
                selected_playlist = {
                    "id": playlist_id,
                    "name": "Selected Playlist",
                    "image": "static/icons/default_playlist.svg",
                    "expires_at": datetime.now().timestamp() + 3600  # 1 hour validity
                }
        else:
            # Format the real playlist data
            selected_playlist = {
                "id": playlist_id,
                "name": playlist_details.get("name", "Selected Playlist"),
                "image": playlist_details.get("images", [{}])[0].get("url", "static/icons/default_playlist.svg"),
                "expires_at": datetime.now().timestamp() + 3600  # 1 hour validity
            }
        
        # Store in session
        session['current_playlist'] = selected_playlist
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error in play_playlist: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to load playlist: {str(e)}"
        }), 500

# Function to get location information from coordinates
def get_location_info(lat, lng):
    """Get city and region information from coordinates using urllib"""
    try:
        if not lat or not lng:
            return "Unknown City", "Unknown Region"
            
        # Use the free BigDataCloud API for reverse geocoding
        geocode_url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lng}&localityLanguage=en"
        
        geo_data = fetch_json_data(geocode_url, timeout=3)
        if not geo_data:
            return f"Location at {lat[:4]}...", f"Region near {lng[:4]}..."
            
        city = geo_data.get("city", "")
        region = geo_data.get("principalSubdivision", "")
        
        # If city is empty, try alternative fields
        if not city:
            city = geo_data.get("locality", "")
        if not city:
            city = geo_data.get("lookupSource", "Unknown City")
            
        if not region:
            region = geo_data.get("countryName", "Unknown Region")
            
        return city, region
    except Exception as e:
        print(f"Error getting location: {str(e)}")
        # If we can't get real location data, use the coordinates
        return f"Location at {lat[:4]}..." if lat else "Unknown City", f"Region near {lng[:4]}..." if lng else "Unknown Region"

@app.route("/playcast")
def playcast():
    """Main playcast route that handles lat/lng parameters"""
    try:
        # Get location info from browser parameters
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        
        # Save these parameters to the session to persist them
        if lat and lng:
            session['user_lat'] = lat
            session['user_lng'] = lng
            print(f"Received coordinates: {lat}, {lng}")
        
        # Get weather info using browser location
        weatherInfo = get_real_weather(lat, lng)
        (weatherSVG, temperature, weatherStatus) = weatherInfo
        
        # Get city and region using our helper function
        city, region = get_location_info(lat, lng)
        
        # Get playlist data based on weather status
        playlists = SAMPLE_PLAYLISTS.copy()
        random.shuffle(playlists)
        
        # Modify the first playlist to match the weather if possible
        if playlists:
            playlists[0]["name"] = f"{weatherStatus} Day Playlist"
            playlists[0]["description"] = f"Perfect for {weatherStatus.lower()} weather"
        
        # Check for current playlist in session
        current_playlist = session.get('current_playlist', {})
        
        # Render the playlist template
        response = make_response(render_template(
            "playlist.html",
            playlistData=playlists,
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
        print(f"Error in playcast route: {str(e)}")
        return render_template(
            "base.html",
            error_message=f"Error loading playcast: {str(e)}"
        )

@app.route("/api/weather")
def api_weather():
    """API endpoint to get weather data"""
    try:
        # Get location info from request or session
        lat = request.args.get('lat') or session.get('user_lat')
        lng = request.args.get('lng') or session.get('user_lng')
        
        # Get real weather data
        weatherInfo = get_real_weather(lat, lng)
        (weatherSVG, temperature, weatherStatus) = weatherInfo
        
        # Get city and region using our helper function
        city, region = get_location_info(lat, lng)
        
        return jsonify({
            "weatherSVG": weatherSVG,
            "temperature": temperature,
            "weatherStatus": weatherStatus,
            "city": city,
            "region": region
        })
    except Exception as e:
        print(f"Error in weather API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/update-location")
def update_location():
    """API endpoint to update location"""
    try:
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        
        if lat and lng:
            session['user_lat'] = lat
            session['user_lng'] = lng
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Missing coordinates"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/ip-location")
def ip_location():
    """API endpoint to get location based on IP"""
    try:
        return jsonify({
            "city": "Orlando",  # Default city
            "region": "Florida",
            "country": "US",
            "loc": "28.6214,-81.4294",
            "timezone": "America/New_York"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/status")
def status():
    """API endpoint to check status"""
    return jsonify({
        "status": "operational",
        "environment": os.environ.get("VERCEL_ENV", "development"),
        "framework": "Flask",
        "python_version": sys.version,
    })

# For debugging purposes
@app.route("/debug-env")
def debug_env():
    """Debug endpoint to view environment variables"""
    env_vars = {key: value for key, value in os.environ.items() 
               if not key.startswith(('AWS_', 'VERCEL_')) and 'TOKEN' not in key and 'KEY' not in key}
    
    return jsonify(env_vars)

@app.route("/debug-app")
def debug_app():
    """Debug endpoint to check app configuration"""
    try:
        import os
        available_templates = []
        template_dir = app.template_folder
        
        if os.path.exists(template_dir):
            available_templates = os.listdir(template_dir)
        
        debug_info = {
            "app_config": {
                "debug": app.debug,
                "testing": app.testing,
                "secret_key_set": bool(app.secret_key),
                "template_folder": template_dir,
                "template_folder_exists": os.path.exists(template_dir),
                "available_templates": available_templates,
                "static_folder": app.static_folder,
                "static_folder_exists": os.path.exists(app.static_folder),
            },
            "routes": [str(rule) for rule in app.url_map.iter_rules()],
            "session_enabled": app.config.get("SESSION_TYPE", "filesystem"),
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "absolute_template_path": os.path.abspath(template_dir) if template_dir else None,
        }
        
        if "base.html" in available_templates:
            try:
                # Test template rendering
                test_render = render_template("base.html")
                debug_info["template_render_test"] = "success"
            except Exception as e:
                debug_info["template_render_test"] = f"error: {str(e)}"
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500 