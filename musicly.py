import requests
import logging
import tagger
import geocoder
from hasher import hashsong
from laststuff import getartistinfo
from icecream import ic as debug
from flask import Flask, render_template, Response

app = Flask(__name__)
app.secret_key = "music"
app.config["TESTING"] = True

root = logging.getLogger()
root.setLevel(logging.DEBUG)

songsname = tagger.Tagger()


def loadsong():
    x = {}
    for song in songsname.scan():
        m = hashsong(song)
        x[m.digest().hex()] = song
    return x


mysong = loadsong()
# debug(mysong)


@app.route("/")
def show_music():
    global stream_entries
    stream_entries = songsname.scan()
    general_data = {"title": "Music Player"}
    return render_template("index.html", entries=stream_entries, **general_data)


def get_user_latlng():
    # hostName = socket.gethostname()
    # userIp = socket.gethostbyname(hostname)
    ip = requests.remote_addr
    userIp = geocoder.ip("me")  # <--- this works but userip doesnt?!
    userLocation = userIp.latlng
    print(ip)
    return userLocation


@app.route("/<string:stream_id>")
def streamer(stream_id):
    global mysong
    song = mysong[stream_id]

    def generate():
        count = 1
        with open(song.link, "rb") as fwav:
            data = fwav.read(1024)
            while data:
                yield data
                data = fwav.read(1024)
                count += 1
                logging.debug("Music data cluster : " + str(count))

    return Response(generate(), mimetype="audio/mp3")


@app.route("/get_info/string:artist_id")
def last_fm(artist_id):
    global mysong
    artist = mysong[artist_id]
    artistinfo = getartistinfo(artist)
    bio = request.get_json(artist.get_bio_content(language="en"))
    return bio


if __name__ == "__main__":
    port = 5000
    http_server = HTTPServer(WSGIContainer(app))
    logging.debug("Started server, site: " + "http://localhost:" + str(port))
    http_server.listen(port)
    IOLoop.instance().start()
