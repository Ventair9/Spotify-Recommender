"""
    Seriously, this is so much nicer now. alright lets get this going    
    
    """
    
# import dependencies

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

class MusicRecommender():
    def __init__(self):
        # i guess first we need the spotify dataset, so how do we import it
        file_path = r"C:\Users\venta\OneDrive\Documents\GitHub\Spotify-Recommender\dataset.csv"
        df = pd.read_csv(file_path)
        print(df.head())
        # it works, hallelujah
        self.song = input("Enter your song: ")
        self.artist = input("Enter your artist: ")
        
        """
        what do i even want to do? so i read dataset, dataset has all data i need like
        track_id, artists, album_name, track_name, popularity, duration_ms, explicit, danceability, energy,
        key, loudness, mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo,
        time_signature, track_genre
        """
        
        """
        So, we got all this data, i want to *INPUT* a song, search the song(maybe i can search the song in the dataset instead of spotify)
        why do we even search on spotify in the first place?
        to get the track_id. ok so i guess we still need it then.
        alright so lets do that first
        """
        
    def search_track(self, song, artist):
        token = session.get("access_token")
        url = "https://api.spotify.com/v1/search"
        request_parameters = {
            "q": f"track:{song} artist:{artist}",
            "type": "track",
            "limit": 1
        }
        headers = {"Authorization": "Bearer " + token}
        
        response = requests.get(url, params=request_parameters, headers=headers)
        data = response.json()
        
        return_track = data["tracks"]["items"][0]
        
        """
        what do i rly want to return? i want the track_id, since technically there is only
        1 track for each 1 id, but i guess for precision sake i can also search for
        artists and track_name
        """
        return {
            "track_id": return_track["id"],
            "artist_id": return_track["artists"][0]["id"],
            "track_name": return_track["name"],
            "artist_name": return_track["artists"][0]["name"]
        }
        """
        alright now what, i have the song data extracted from spotify, to use in the search
        from my csv file. But that isnt enough, i also want to analyze the lyrics in order
        to make the algorithm more accurate. How do i do that then?
        Lowkey doing the same thing i just did but with the Genuis API endpoint instead.
        """
        
    
    def search_lyrics(self, song, artist):
        url = f"https://api.genius.com/search?q={artist} {song}"
        headers = {"Authorization": "Bearer " + os.getenv("GENIUS_KEY")}
        response = requests.get(url, headers=headers)
        
        data = response.json()
        if not data["response"]["hits"]:
            print(f"Error, no data found for song: {song} artist: {artist} ")
        
        """
        looking for the song url in order to get the lyrics data from genius.com
        """        
        song_url = data["response"]["hits"][0]["result"]["url"]
        
        
                    
MusicRecommender()