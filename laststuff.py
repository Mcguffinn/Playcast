import pylast
import os
from dotenv import load_dotenv

load_dotenv()

# API credentials
network = pylast.LastFMNetwork(
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET"),
    username="Mcguffinn",
    password_hash=pylast.md5(os.environ.get("API_PASS")),
)


def getartistinfo(artist):
    return network.get_artist(artist)


# print(os.environ.get("API_KEY"))
# print(getartistinfo("System of a Down").get_bio_content(language="en"))