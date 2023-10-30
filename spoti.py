import requests
import socket
import os
import logging
import json
import base64
import datetime
from icecream import ic as debug
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECERET")

class SpotifyAPI():
    accessToken = None
    accessTokenExpires = None
    accessTokenDidExpire = bool
    client_id = None
    client_secret = None
    tokenUrl = 'https://accounts.spotify.com/api/token?'

    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_client_creds(self):
        clientId = self.client_id
        clientSecret = self.client_secret

        if clientId == None or clientId == None:
            raise Exception("You need a client_id and client_secret")

        clientCreds = f"{clientId}:{clientSecret}"
        clientCredsb64 = base64.b64encode(clientCreds.encode())
        return clientCredsb64.decode()

    def get_token_header(self):
        clientCredsb64 = self.get_client_creds()
        return {
        "Authorization": f"Basic {clientCredsb64}"
        }
    
    def get_token_data(self):
        return {
        "grant_type":"client_credentials"
        }

    def extract_access_token(self):
        tokenUrl = self.tokenUrl
        tokenData = self.get_token_data()
        tokenHeaders = self.get_token_header()
        
        r = requests.post(tokenUrl, data=tokenData, headers=tokenHeaders)
        tokenResponseData = r.json()

        if r.status_code not in range(200, 299):
            raise Exception("could not authenticate client") 
            
        data = r.json()
        now = datetime.datetime.now()
        accessToken = data['access_token']
        expiresIn = data['expires_in']
        expires = now + datetime.timedelta(seconds=expiresIn)
        self.accessToken = accessToken
        self.accessTokenExpires = expires
        self.accessTokenDidExpire = expires < now
        return True

    def get_access_token(self):
        self.extract_access_token()
        token = self.accessToken
        expires = self.accessTokenExpires
        now = datetime.datetime.now()
        if expires < now:
            self.extract_access_token()
            return self.get_access_token
        elif token == None:
            self.extract_access_token()
            return self.get_access_token()
        return token

    def get_resource_header(self):
        accessToken = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {accessToken}"
        }
        return headers

    def get_playlist(self, id):
        headers = self.get_resource_header()
        url = f"https://api.spotify.com/v1/playlists/{id}"
        r = requests.get(url, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()

    def search(self, query, search_type="playlist"):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        payload = urlencode({"q": query, "type": search_type.lower()})

        lookupUrl = f"{endpoint}?{payload}"
        debug(lookupUrl)

        r = requests.get(lookupUrl, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()

spotify = SpotifyAPI(client_id, client_secret)

# data = spotify.search(query="Freezing Rain", )
# data = spotify.search("Light Rain",search_type="playlist")
# for items in data['playlists']["items"]:
#     image = items["images"][0]["url"]
#     name = items["name"]
#     debug(image, name)





# debug(spotify.search("Light Rain",search_type="playlist"))