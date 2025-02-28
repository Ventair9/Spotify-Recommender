"""
Spotify Authentication Service, returning Spotify Token in order to query Spotify API for song
    """

import os
import secrets
import urllib.parse
from flask import redirect, request, session
import base64
import requests

class SpotifyOAuth2:
    def __init__(self):
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.client_id = os.getenv("CLIENT_ID")
        self.redirect_uri = os.getenv("REDIRECT_URI")
        self.genius_key = os.getenv("GENIUS_KEY")
        self.secret_key = os.getenv("SECRET_KEY")

    def login(self):
        state = secrets.token_urlsafe(16)
        scope = "user-read-private user-read-email user-library-read playlist-modify-public playlist-modify-private user-read-recently-played user-read-playback-state"
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
   
    def show_token(self):
        token = session.get("access_token")
        return "Your access token is " + token
   