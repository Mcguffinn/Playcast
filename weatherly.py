from flask import Flask, render_template, Response
import logging
from weather import get_user_weather

app = Flask(__name__)


@app.route("/")
def index():
    currentWeather = get_user_weather()
    return render_template("weather.html", entries=currentWeather["data"])


if __name__ == "__main__":
    port = 5000
    app.run(debug=True)
    logging.debug("Started server, site: " + "http://localhost:" + str(port))