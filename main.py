from flask import Flask, session, redirect, request, jsonify
import requests
import base64
import urllib.parse
import os
import secrets
import re
from bs4 import BeautifulSoup
from transformers import pipeline, AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import torch

class SpotifyOAuth2:
    def __init__(self):
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.client_id = os.getenv("CLIENT_ID")
        self.redirect_uri = os.getenv("REDIRECT_URI")
        self.genius_key = os.getenv("GENIUS_KEY")
        self.secret_key = os.getenv("SECRET_KEY")
        self.song_df = pd.read_csv("song_lyrics_dataset.csv")

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
    
    
    def precompute_song_data(self, song_df):
        song_data = []
        for _, row in song_df.iterrows():
            lyrics = row["lyrics"]
            sentiment = self.analyze_lyrics_sentiment(lyrics)
            embedding = embedding_model.encode(lyrics, convert_to_tensor=True)
            song_data.append({"lyrics": lyrics, "sentiment": sentiment[0]["label"], "embedding": embedding})
        return song_data
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
        
    #Function for getting song lyrics using the genius api
    def get_song_lyrics(self, artist, song):
        url = f"https://api.genius.com/search?q={artist} {song}"
        headers = {"Authorization": "Bearer " + self.genius_key}
        response = requests.get(url, headers=headers)
        
        data = response.json()
        if not data["response"]["hits"]:
            print("error, no data found")
            
        song_url = data["response"]["hits"][0]["result"]["url"]
        page = requests.get(song_url)
        soup = BeautifulSoup(page.text, "html.parser")
        lyrics_div = soup.find("div", class_=re.compile("Lyrics_Container.*"))
        lyrics = lyrics_div.get_text(separator="\n") if lyrics_div else "Lyrics not found."
        return lyrics
    
    def analyze_lyrics_sentiment(self, lyrics):
        return sentiment_model(lyrics[:512])

    def find_similar_songs(self, lyrics, song_data):
        input_sentiment = spotify.analyze_lyrics_sentiment(lyrics)[0]["label"]
        filtered_songs = [s for s in song_data if s["sentiment"] == input_sentiment]
        
        if not filtered_songs:
            print("No similar songs found")
            
        song_embeddings = torch.stack([s["embedding"] for s in filtered_songs])
        input_embedding = embedding_model.encode(lyrics, convert_to_tensor=True)
        similarities = util.pytorch_cos_sim(input_embedding, song_embeddings)
        
        best_match = song_data[similarities.argmax().item()]["lyrics"]
        return best_match

spotify = SpotifyOAuth2()
song_data = spotify.precompute_song_data(song_df)
sentiment_model = pipeline("sentiment-analysis")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


if __name__ == "__main__":
    song_name = input("Enter a song name: ")
    song_data = spotify.search_track(song_name)
    
    if not song_data:
        print("Error: song not found")
        
    else:
        print(f"Found: {song_data["name"]} by {song_data["artist"]}")
        lyrics = spotify.get_song_lyrics(song_data["artist"], song_data["name"])
        if lyrics:
            print("\nLyrics:")
            print(lyrics[:500] + "...")
            sentiment = spotify.analyze_lyrics_sentiment(lyrics)
            print("\nSentiment analysis:", sentiment)
            
            similar_song = spotify.find_similar_songs(lyrics, song_data)
            print(f"\n Similar Song: {similar_song}")
        else:
            print("Lyrics not found")
            