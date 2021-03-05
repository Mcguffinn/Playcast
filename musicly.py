import os
import logging
import json
import types
import tagger 
from flask import Flask, render_template, Response
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

app = Flask(__name__)
app.secret_key = "music"
app.config['TESTING'] = True

root = logging.getLogger()
root.setLevel(logging.DEBUG)

songsname = tagger.Tagger()

def return_music_dict():
    d = []
    id_counter = 0
    for filename in os.listdir(r'F:/Music'):
        if filename.endswith('.mp3') and id_counter <= len(d):
            id_counter += 1
            d.append(
                { 'id' : id_counter, 'name' : filename.replace('.mp3',''), 'link' : r'F:/Music/' + filename })
    return d

@app.route('/')
def show_music():
    general_data = {
        'title': 'Music Player'
    }
    stream_entries = return_music_dict()
    # songsname.music_directory(directory = r"F:/Music")
    # tagger.Tagger.music_directory(directory=r'F:/Music')
    return render_template('index.html', entries=songsname.music_directory(), **general_data)

@app.route('/<int:stream_id>')
def streamer(stream_id):
    def generate():
        data = songsname.music_directory()
        count = 1
        song = types.SimpleNamespace()
        for item in data:
            if item['id'] == stream_id:
                song = item['link']
        with open(song, "rb") as fwav:
            data = fwav.read(1024)
            while data:
                yield data
                data = fwav.read(1024)
                count += 1
                logging.debug('Music data cluster : ' + str(count))
    return Response(generate(), mimetype= "audio/mp3")


if __name__ == "__main__":
    port = 5000
    http_server = HTTPServer(WSGIContainer(app))
    logging.debug("Started sever, site: " + "http://localhost:" + str(port))
    http_server.listen(port)
    IOLoop.instance().start()