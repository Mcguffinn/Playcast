import requests
import json
import os
import mutagen
from icecream import ic as debug
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from dataclasses import dataclass
from typing import List
import pylast

API_KEY = "76e2d6fda82f6c2377d2bc5728e8aa8d"
API_SECRET = "540fd48e6f06d8306016d6d592b160a8"

network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
directory = r"F:/Music"
songlist = []
song_tags = []
path = str


def pop(mylist):
    try:
        return mylist.pop()
    except IndexError:
        return None


@dataclass
class MySong:
    album: str
    title: str
    artist: str
    link: str
    genre: str = ""
    songid: int = 0


class LastFm:
    pass


class Tagger:
    # Grabs ID3 Tags from audio file
    def getid3(self, filename):
        return EasyID3(filename)

    def scan(self):
        for song_file in os.listdir(directory):
            if not song_file.endswith(".mp3"):
                continue
            link = os.path.join(directory, song_file)
            data = self.getid3(link)
            MySong.songid += 1
            try:
                song = MySong(
                    album=pop(data["album"]),
                    title=pop(data["title"]),
                    artist=pop(data["artist"]),
                    genre=pop(data["genre"]),
                    link=link,
                    songid=MySong.songid,
                )

            except KeyError:
                continue

            yield song


tag = Tagger()
# tag.music_directory()
# for song in tag.scan():
#     print(f"song: {song.title}, {song.genre}, {song.artist}, {song.songid}")
