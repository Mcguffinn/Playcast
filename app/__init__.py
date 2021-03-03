
from flask import Flask, render_template, Response
import logging
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


app = Flask(__name__)
app.secret_key = "music"
app.config['TESTING'] = True

root = logging.getLogger()
root.setLevel(logging.DEBUG)


@app.route('/')
def show_music():
    general_data = {
        'title': 'Music Player'
    }
    stream_entries = return_music_dict()
    return render_template('design.html', entries=stream_entries, **general_data)


if __name__ == "__main__":
    port = 5000
    http_server = HTTPServer(WSGIContainer(app))
    logging.debug("Started sever, site: " + "http://localhost:" + str(port))
    http_server.listen(port)
    IOLoop.instance().start()
