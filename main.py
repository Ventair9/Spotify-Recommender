"""
Functionalities for the process of finding the ideal match for queried song
    """

from flask import Flask, session, redirect, request, jsonify
import requests
import re
from bs4 import BeautifulSoup
from transformers import pipeline, AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import torch
from SpotifyOAuth2 import SpotifyOAuth2
import os

class Main():
    def __init__(self):
        #reading in spotify song dataset(they removed API access for all this, grr)
        path = os.path.abspath(os.path.realpath(__file__))
        print(path)
        self.song_df = pd.read_csv(path)
        
    def precompute_song_data(self, song_df):
        #Precomputing for performance reasons, its a very large dataset lol.)
        song_data = []
        for _, row in song_df.iterrows():
            lyrics = row["lyrics"]
            sentiment = self.analyze_lyrics_sentiment(lyrics)
            embedding = embedding_model.encode(lyrics, convert_to_tensor=True)
            song_data.append({"lyrics": lyrics, "sentiment": sentiment[0]["label"], "embedding": embedding})
        return song_data
    #getting user input, searching the user input in spotify, returning one track.
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
        #returns track id, artist id, track name, and artist name in a dictionary.
        return {
            "track_id": track["id"],
            "artist_id": track["artists"][0]["id"],
            "track_name": track["name"],
            "artist_name": track["artists"][0]["name"]
        }
       
    #Getting the songs lyrics from the genius API
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
    
    """
    Using HuggingFace's pre-trained sentiment model in order to analyze lyrics sentiment, limited to the first 512 characters due to
    model restraints
    """
    def analyze_lyrics_sentiment(self, lyrics):
        return sentiment_model(lyrics[:512])

    def find_similar_songs(self, lyrics, song_data):
        input_sentiment = self.analyze_lyrics_sentiment(lyrics)[0]["label"]
        filtered_songs = [s for s in song_data if s["sentiment"] == input_sentiment]
       
        if not filtered_songs:
            print("No similar songs found")
           
        song_embeddings = torch.stack([s["embedding"] for s in filtered_songs])
        input_embedding = embedding_model.encode(lyrics, convert_to_tensor=True)
        #calculates the vector distances to find closest matching song.
        similarities = util.pytorch_cos_sim(input_embedding, song_embeddings)
       
        best_match = song_data[similarities.argmax().item()]["lyrics"]
        return best_match

#Initializing 
spotify = SpotifyOAuth2()
mainn = Main()
song_data = mainn.precompute_song_data(mainn.song_df)
sentiment_model = pipeline("sentiment-analysis")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


if __name__ == "__main__":
    song_name = input("Enter a song name: ")
    song_data = Main.search_track(song_name)
   
    if not song_data:
        print("Error: song not found")
       
    else:
        print(f"Found: {song_data["track_name"]} by {song_data["artist"]}")
        lyrics = spotify.get_song_lyrics(song_data["artist"], song_data["track_name"])
        if lyrics:
            print("\nLyrics:")
            print(lyrics[:500] + "...")
            sentiment = spotify.analyze_lyrics_sentiment(lyrics)
            print("\nSentiment analysis:", sentiment)
           
            similar_song = spotify.find_similar_songs(lyrics, song_data)
            print(f"\n Similar Song: {similar_song}")
        else:
            print("Lyrics not found")
            
            
        """
        spotify authentication -> use token to do what? uhm
        
        
        
        
        """