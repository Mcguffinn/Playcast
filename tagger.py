import requests
import json
import os
import mutagen
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import pylast

API_KEY = '76e2d6fda82f6c2377d2bc5728e8aa8d'
API_SECRET = '540fd48e6f06d8306016d6d592b160a8'

network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
directory = r"F:/Music"
songlist = os.listdir(directory)
path = str


# Testing ID3
# for song in songlist:
#     if song.endswith("mp3"):
#         path = os.path.join(directory,song)
#         keys = EasyID3(path)
# print(keys["artist"])


class Tagger:
    # Grabs ID3 Tags from audio file
    def getid3(self, filename):
        return EasyID3(filename)

    # Grabs location of audio file
    def music_directory(self, directory):
        songlist = []
        id_counter = 0
        for song in os.listdir(directory):
            if song.endswith('.mp3') and id_counter <= len(songlist):
                id_counter += 1
                path = os.path.join(directory, song)
                # songlist.append({ 'id' : id_counter, 'name' : song.replace('.mp3',''), 'link' : r'F:/Music/' + song })
                songlist.append(self.getid3(path))
        return (songlist)

    # Function used to query the data of the song, find artists, genre etc....
    def find_tags(self, tag):
        for id in self.music_directory(directory):
            if id[tag] is None:
                pass
            musictag = id[tag]
            yield(musictag)

    def grab_all_tags(self):
        for tags in self.music_directory(directory):
            album = tags.keys()
        return album


tag = Tagger()
tag.music_directory(directory=directory)
# print(tag.find_tags('genre'))

for songs in tag.find_tags('artist'):
    print(songs)