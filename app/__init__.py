from flask import Flask
import logging


app = Flask(__name__)
app.config['TESTING'] = True

from app import routes

if __name__ == "__main__":
    port = 5000
    logging.debug("Started sever, site: " +"http://localhost:" +str(port))