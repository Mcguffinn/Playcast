import os
import sys
import json
import random
import traceback
from datetime import datetime
from flask import Flask, jsonify, request, render_template, redirect, make_response, session, url_for, send_from_directory

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get absolute paths for better reliability
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_folder = os.path.join(base_dir, 'static')
template_folder = os.path.join(base_dir, 'templates')

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

# Default weather information as fallback
DEFAULT_WEATHER = {
    "Clear": ["Clear", "static/icons/clear_day.svg"],
    "Cloudy": ["Cloudy", "static/icons/cloudy.svg"],
    "Rain": ["Rain", "static/icons/rain.svg"],
    "Snow": ["Snow", "static/icons/snow.svg"],
    "Thunderstorm": ["Thunderstorm", "static/icons/tstorm.svg"],
    "Fog": ["Fog", "static/icons/fog.svg"],
    "Partly Cloudy": ["Partly Cloudy", "static/icons/partly_cloudy_day.svg"],
}

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
    """Mock weather status route - redirects to home/playcast"""
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    return redirect(f"/home?lat={lat}&lng={lng}" if lat and lng else "/home")

@app.route("/playlist/<query>")
def get_playlist_data(query):
    """Return playlist data for a given weather type"""
    try:
        # Get all playlists and randomly shuffle them
        playlists = SAMPLE_PLAYLISTS.copy()
        random.shuffle(playlists)
        
        # Modify the first playlist to match the query for better UX
        if playlists:
            playlists[0]["name"] = f"{query.title()} Day Playlist"
            playlists[0]["description"] = f"Perfect for {query.lower()} weather"
        
        return playlists
    except Exception as e:
        return [{
            "image": "static/icons/default_playlist.svg",
            "name": "Error finding playlists",
            "description": f"We encountered an error: {str(e)}",
            "outurl": "https://open.spotify.com",
            "id": ""
        }]

@app.route("/play-playlist/<playlist_id>")
def play_playlist(playlist_id):
    """Handle playlist selection"""
    try:
        # Find the selected playlist in our sample data
        selected_playlist = next((p for p in SAMPLE_PLAYLISTS if p["id"] == playlist_id), None)
        
        if not selected_playlist:
            selected_playlist = {
                "id": playlist_id,
                "name": "Selected Playlist",
                "image": "static/icons/default_playlist.svg",
                "expires_at": datetime.now().timestamp() + 3600  # 1 hour validity
            }
        
        # Store in session
        session['current_playlist'] = selected_playlist
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to load playlist: {str(e)}"
        }), 500

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
        
        # Mock weather and location data - in a real app, this would use the coordinates
        weatherSVG = "static/icons/clear_day.svg"
        temperature = "75"
        weatherStatus = "Clear"
        
        # In a real app, we'd use the coordinates to get location info
        city = "Example City"
        region = "Example Region"
        if lat and lng:
            # Just for demonstration
            city = f"Location at {lat[:4]}..."
            region = f"Region near {lng[:4]}..."
        
        # Get playlist data
        playlists = SAMPLE_PLAYLISTS.copy()
        random.shuffle(playlists)
        
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
        # Mock weather and location data
        weatherSVG = "static/icons/clear_day.svg"
        temperature = "75"
        weatherStatus = "Clear"
        city = "Example City"
        region = "Example Region"
        
        return jsonify({
            "weatherSVG": weatherSVG,
            "temperature": temperature,
            "weatherStatus": weatherStatus,
            "city": city,
            "region": region
        })
    except Exception as e:
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