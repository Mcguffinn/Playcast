import os
import logging
import json
import types
import tagger
import hashlib
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
    for song in tagger.Tagger().scan():
        m = hashlib.sha256()
        m.update(song.link.encode("utf-8"))
        x[m.digest()] = song
    return x


mysong = loadsong()


def return_music_dict():
    d = []
    id_counter = 0
    for filename in os.listdir(r"F:/Music"):
        if filename.endswith(".mp3") and id_counter <= len(d):
            id_counter += 1
            d.append(
                {
                    "id": id_counter,
                    "name": filename.replace(".mp3", ""),
                    "link": r"F:/Music/" + filename,
                }
            )
    return d


@app.route("/")
def show_music():
    general_data = {"title": "Music Player"}
    stream_entries = songsname.scan()
    return render_template("index.html", entries=stream_entries, **general_data)


@app.route("/<int:stream_id>")
def streamer(stream_id):
    song = mysong

    def generate():
        count = 1

        for link, track in song.items():

            if track.songid == stream_id:
                with open(track.link, "rb") as fwav:
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
