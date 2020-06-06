from flask import Flask, render_template, Response
import logging
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


app = Flask(__name__)
app.config['TESTING'] = True

root = logging.getLogger()
root.setLevel(logging.DEBUG)

from app import routes

if __name__ == "__main__":
    port = 5000
    http_server = HTTPServer(WSGIContainer(app))
    logging.debug("Started sever, site: " + "http://localhost:" + str(port))
    http_server.listen(port)
    IOLoop.instance().start()