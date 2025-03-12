import os
import logging
import re
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import (Flask, render_template, jsonify, request, redirect, session)
from dotenv import load_dotenv
from spotifyApi import SpotifyAPI
from weatherApi import Weather
from icecream import ic as debug

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['PROXY_FIX_FOR'] = 1  # Number of proxies in front of your app
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.secret_key = os.environ.get("SECRET_KEY")
ENV = os.environ.get("ENV")


if ENV == "dev":
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


@app.route("/")
def index():
    return render_template("base.html")


@app.route("/home", methods=["GET", "POST"])
def get_weather_status():
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
    
    key = weather.get_user_weather()
    weatherCodes = key["data"]["timelines"][0]["intervals"][0]["values"]
    mark = weatherCodes.get("weatherCode")
    svg = weatherInfo[mark]
    temp = weatherCodes.get("temperature")
    weatherStatus = weatherInfo[mark]

    return (svg[1], str(temp), weatherStatus[0])


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
        data = spotify.search(query=query, search_type="playlist")
        playlistData = []
        
        # Debug print the data structure
        logger.info(f"Spotify API response structure: {data.keys() if data else 'None'}")
        if data and "playlists" in data:
            logger.info(f"Playlists structure: {data['playlists'].keys() if data['playlists'] else 'None'}")
        
        # Check if the API returned valid data
        if not data or "playlists" not in data or "items" not in data["playlists"] or not data["playlists"]["items"]:
            logger.warning(f"No playlist data found for query: {query}")
            # Return a default playlist when no results are found
            return [{
                "image": "static/icons/default_playlist.svg",
                "name": "No playlists found",
                "description": f"No playlists found for '{query}'. Try a different search term.",
                "outurl": "https://open.spotify.com",
                "id": ""
            }]

        # Process each playlist item
        for items in data["playlists"]["items"]:
            # Skip items that are None
            if items is None:
                logger.warning("Found None item in playlist results, skipping")
                continue
                
            # Debug the item structure
            logger.info(f"Processing playlist item: {items.get('name', 'Unknown')}")
            
            # Check if playlist has images
            if not items.get("images") or len(items["images"]) == 0:
                logger.info("No images found for playlist, using default")
                # Use a default image
                image = "static/icons/default_playlist.svg"
            else:
                # Check if the first image is None or missing url
                if items["images"][0] is None or "url" not in items["images"][0]:
                    image = "static/icons/default_playlist.svg"
                else:
                    image = items["images"][0]["url"]
                
            name = items.get("name", "Unnamed Playlist")
            description = items.get("description", "No description available")
            
            # Check if external_urls exists and contains spotify link
            if items.get("external_urls") and "spotify" in items["external_urls"]:
                outurl = items["external_urls"]["spotify"]
                # Extract playlist ID
                playlist_id = extract_playlist_id(outurl)
            else:
                outurl = "https://open.spotify.com"
                playlist_id = ""
            
            playlistData.append({
                "image": image, 
                "name": name, 
                "description": description, 
                "outurl": outurl,
                "id": playlist_id
            })
        
        return playlistData
        
    except Exception as e:
        logger.error(f"Error in get_playlist_data: {str(e)}")
        # Return a default playlist in case of any error
        return [{
            "image": "static/icons/default_playlist.svg",
            "name": "Error finding playlists",
            "description": "We encountered an error finding playlists. Please try again later.",
            "outurl": "https://open.spotify.com",
            "id": ""
        }]


@app.route("/play-playlist/<playlist_id>")
def play_playlist(playlist_id):
    """Handle playing a specific playlist"""
    try:
        # Get the playlist details to store in session
        playlist_details = spotify.get_playlist(playlist_id)
        
        # Get the playlist image if available
        image_url = None
        if playlist_details.get('images') and len(playlist_details['images']) > 0:
            image_url = playlist_details['images'][0].get('url')
        
        # Store as current playlist in session
        session['current_playlist'] = {
            'id': playlist_id,
            'name': playlist_details.get('name', 'Unknown Playlist'),
            'image': image_url
        }
        
        # Redirect back to playcast page
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error playing playlist: {str(e)}")
        return jsonify({"success": False, "message": str(e)})


@app.route("/playcast")
def playcast():
    try:
        # Get location info for display
        location_data = weather.get_location_from_browser()
        city = location_data.get('city', 'Unknown')
        region = location_data.get('region', 'Unknown')
        
        # Get weather info
        weatherInfo = get_weather_status()
        (weatherSVG, temperature, weatherStatus) = weatherInfo
        
        # Check if there's a current playlist from session
        current_playlist = session.get('current_playlist')
        
        # Get playlist data with error handling
        try:
            playlist = get_playlist_data(weatherStatus)
            
            return render_template(
                "playlist.html",
                playlistData=playlist,
                weatherSVG=weatherSVG,
                weatherStatus=weatherStatus,
                temperature=temperature,
                city=city,
                region=region,
                currentPlaylist=current_playlist
            )
        except Exception as e:
            logger.error(f"Error getting playlist data: {str(e)}")
            # Just render the base template with a simple message
            return render_template(
                "base.html",
                error_message="We couldn't load your weather-based playlist right now. Please try again later."
            )
    except Exception as e:
        logger.error(f"Error in playcast route: {str(e)}")
        # Use base.html instead of error.html
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
        weatherInfo = get_weather_status()
        (weatherSVG, temperature, weatherStatus) = weatherInfo
        
        # Get location info for display
        location_data = weather.get_location_from_browser()
        city = location_data.get('city', 'Unknown')
        region = location_data.get('region', 'Unknown')
        
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


"""
Great route for testing api endpoints in a production environment
"""
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
    app.run(debug=True)