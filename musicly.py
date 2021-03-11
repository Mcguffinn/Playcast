import os
import logging
import json
import types
import tagger
from hasher import hashsong
from icecream import ic as debug
from flask import Flask, render_template, Response
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

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


@app.route("/<string:stream_id>")
def streamer(stream_id):
    global mysong
    # not required, but way of explicity referencing global
    # stop iterating through everything to get to 1 thing, you have dictionary
    # song = mysong.songid
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


if __name__ == "__main__":
    port = 5000
    http_server = HTTPServer(WSGIContainer(app))
    logging.debug("Started server, site: " + "http://localhost:" + str(port))
    http_server.listen(port)
    IOLoop.instance().start()
