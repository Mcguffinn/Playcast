import logging
import os
from dotenv import load_dotenv
from icecream import ic as debug
from flask import (
    Flask,
    render_template,
    request,
)
from werkzeug.middleware.proxy_fix import ProxyFix
from weatherApi import Weather
from spotifyApi import SpotifyAPI

load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)
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
        4201: ["Heavy Rain", "static\icons\rain_heavy.svg"],
        4001: ["Rain", "static\icons\rain.svg"],
        4200: ["Light Rain", "static\icons\rain_light.svg"],
        6201: ["Heavy Freezing Rain", "static\icons\freezing_rain_heavy.svg"],
        6001: ["Freezing Rain", "static\icons\freezing_rain.svg"],
        6200: ["Light Freezing Rain", "static\icons\freezing_rain_light.svg"],
        6000: ["Freezing Drizzle", "static\icons\freezing_drizzle.svg"],
        4000: ["Drizzle" "static\icons\drizzle.svg"],
        7101: ["Heavy Ice Pellets", "static\icons\ice_pellets_heavy.svg"],
        7000: ["Ice Pellets", "static\icons\ice_pellets.svg"],
        7102: ["Light Ice Pellets", "static\icons\ice_pellets_light.svg"],
        5101: ["Heavy Snow", "static\icons\snow_heavy.svg"],
        5000: ["Snow", "static\icons\snow.svg"],
        5100: ["Light Snow", "static\icons\snow_light.svg"],
        5001: ["Flurries", "static\icons\flurries.svg"],
        8000: ["Thunderstorm", "static\icons\tstorm.svg"],
        2100: ["Light Fog", "static\icons\fog_light.svg"],
        2000: ["Fog", "static\icons\fog.svg"],
        1001: ["Cloudy", "static\icons\cloudy.svg"],
        1102: ["Mostly Cloudy", "static\icons\mostly_cloudy.svg"],
        1101: ["Partly Cloudy", "static\icons\partly_cloudy_day.svg"],
        1100: ["Mostly Clear", "static\icons\mostly_clear_day.svg"],
        1000: ["Clear", "static\icons\clear_day.svg"],
    }
    
    ip = (
        request.remote_addr
        # if request.remote_addr != None
        # else os.environ.get("REMOTE_ADDR")
    )
    
    key = weather.get_user_weather(ip)
    weatherCodes = key["data"]["timelines"][0]["intervals"][0]["values"]
    mark = weatherCodes.get("weatherCode")
    svg = weatherInfo[mark]
    temp = weatherCodes.get("temperature")
    weatherStatus = weatherInfo[mark]

    return (svg[1], str(temp), weatherStatus[0])


@app.route("/playlist/<query>")
def get_playlist_data(query):
    data = spotify.search(query=query, search_type="playlist")
    playlistData = []

    for items in data["playlists"]["items"]:
        image = items["images"][0]["url"]
        name = items["name"]
        description = items["description"]
        outurl = items["external_urls"]["spotify"]
        playlistData.append(
            {"image": image, "name": name, "description": description, "outurl": outurl}
        )
    return playlistData


@app.route("/playcast")
def playcast():
    weatherInfo = get_weather_status()
    #debug(weatherInfo)
    (weatherSVG, temperature, weatherStatus) = weatherInfo
    playlist = get_playlist_data(weatherStatus)
    return render_template(
        "playlist.html",
        playlistData=playlist,
        weatherSVG=weatherSVG,
        weatherStatus=weatherStatus,
        temperature=temperature,
    )


if __name__ == "__main__":
    app.run()