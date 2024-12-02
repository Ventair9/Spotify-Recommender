from flask import Flask, session, redirect, request, jsonify
import requests
import base64
import urllib.parse
import os
import secrets

app = Flask(__name__)

class SpotifyOAuth2:
    def __init__(self):
        self.app = app
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.client_id = os.getenv("CLIENT_ID")
        self.redirect_uri = os.getenv("REDIRECT_URI")
        app.secret_key = os.getenv("SECRET_KEY")

    def login(self):
        state = secrets.token_urlsafe(16)
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
    
    # with user input for track_name, search for track and return track name
    def search_track(self, track_name):
        token = session.get("access_token")
        endpoint_url = "https://api.spotify.com/v1/search"
        request_parameters = {
            "q": track_name,
            "type": "track",
            "limit": 1
        }
        headers = {"Authorization": "Bearer " + token}

        response = requests.get(endpoint_url, params=request_parameters, headers=headers)
        data = response.json()

        track = data["tracks"]["items"][0]
        return {
            "track_id": track["id"],
            "artist_id": track["artists"][0]["id"],
            "track_name": track["name"],
            "artist_name": track["artists"][0]["name"]
        }

    def get_audio_features(self, track_id):
        token = session.get("access_token")
        url = f"https://api.spotify.com/v1/audio-features/{track_id}"
        headers = {"Authorization": "Bearer " + token}

        response = requests.get(url, headers=headers)
        return response.json()

    def get_recommendations(self, seed_tracks, seed_artists):
        token = session.get("access_token")
        url = "https://api.spotify.com/v1/recommendations"
        parameters = {
            "seed_tracks": ",".join(seed_tracks),
            "seed_artists": ",".join(seed_artists),
            "limit": 10
        }
        headers = {"Authorization": "Bearer " + token}

        response = requests.get(url, params=parameters, headers=headers)
        return response.json()["tracks"]
        
spotify = SpotifyOAuth2()

@app.route('/')
def home():
    return '''
        <form action="/search" method="post">
            <label for="track_name">Enter Song Name:</label>
            <input type="text" id="track_name" name="track_name" required>
            <button type="submit">Search</button>
        </form>
    '''

@app.route("/login")
def login():
    return spotify.login()

@app.route("/callback")
def callback():
    return spotify.callback()

@app.route("/search", methods=["POST"])
def search():
    track_name = request.form.get("track_name")
    track_info = spotify.search_track(track_name)
    track_id = track_info.get("track_id")
    print(f"Track ID extracted: {track_id}")
    print(track_info)
    audio_features = spotify.get_audio_features(track_id)
    return jsonify({
        "track_info": track_info,
        "audio_features": audio_features
    })

@app.route("/audio_features")
def audio_features():
    track_id  = request.args.get("track_id")
    print("Track ID:", track_id)
    features = spotify.get_audio_features(track_id)
    return jsonify(features)

@app.route("/recommendations")
def recommendations():
    seed_tracks = request.args.get("seed_tracks").split(",")
    seed_artists = request.args.get("seed_artists").split(",")
    recommendations = spotify.get_recommendations(seed_tracks, seed_artists)
    return jsonify(recommendations)

if __name__ == "__main__":
    app.run(port=8888, debug=True)
