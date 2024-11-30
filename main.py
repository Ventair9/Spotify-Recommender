#lets make this one a little bit more serious.
from flask import Flask, session, redirect, request
import requests
import base64
import urllib.parse
import os

#token logic

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

class SpotifyOAuth2:
    def __init__(self):
        self.app = app
        self.secret_key = os.getenv("CLIENT_SECRET")
        self.client_id = os.getenv("CLIENT_ID")


    def login(self):
        state = self.token_urlsafe(16)
        scope = "user-read-private user-read-email user-library-read playlist-modify-public playlist-modify-private"
        query_parameters = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": state,
            "show_dialog": True
        }
        auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(query_parameters)
        return redirect(auth_url)
    
    def callback(self):
        code = request.args.get("code")
        token_request = {
            "url": "https://accounts.spotify.com/api/token",
            "data": {
                "code": code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code"
            }
        }
        auth_credentials = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_credentials.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + auth_base64
        }

        response = requests.post(token_request["url"], data=token_request["data"], headers=headers)
        json_response = response.json()

        session["access_token"] = json_response["access_token"]
        return redirect("/token")
    
    def search_track(self):
        token = session.get("access_token")
        endpoint_url = "https://api.spotify.com/v1/search"
        request_parameters = {
            "q": track_name,
            "type": "track",
            "limit": 1
        }
        headers = {"Authorization": "Bearer " + token}

        response = requests.get(endpoint_url, params=request_parameters, headers=headers)
        return response.json()["tracks"]["items"][0]

        """
        wtf do i actually want to do? search for track, use track that was searched for to get recommendations
        recommendations required parameters: seed_artist, seed_genres, seed_tracks
        seed_artists = spotify id for artists
        seed_genres = genres(from genre seeds)
        seed_tracks = spotify id for track
        search for track -> response: tracks object -> items array -> id for the track
                            response: artist object -> items array -> id for the artist
        get audio features for searched track, requires: spotify ID for the track
        response = audio features
        save audio features of track, use them in the get recommendations request to find good songs
        """