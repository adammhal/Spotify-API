# main.py
import os
import base64
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

# Spotify API endpoints
TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"
NOW_PLAYING_ENDPOINT = "https://api.spotify.com/v1/me/player/currently-playing"
RECENTLY_PLAYED_ENDPOINT = "https://api.spotify.com/v1/me/player/recently-played"
TOP_TRACKS_ENDPOINT = "https://api.spotify.com/v1/me/top/tracks"
TOP_ARTISTS_ENDPOINT = "https://api.spotify.com/v1/me/top/artists"

# FastAPI app setup
app = FastAPI()

# Configure CORS to allow requests from your frontend
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
    "https://adammhal.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_access_token():
    """
    Uses the refresh token to get a new access token.
    """
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
    }

    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.post(TOKEN_ENDPOINT, data=payload, headers=headers)
    response.raise_for_status() # Raise an exception for bad status codes
    return response.json()['access_token']


@app.get("/api/now-playing")
def get_now_playing():
    """
    Gets the user's currently playing song, or the last played song as a fallback.
    """
    try:
        access_token = get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(NOW_PLAYING_ENDPOINT, headers=headers)

        # If nothing is playing (204), get the last played song
        if response.status_code == 204:
            recent_params = {'limit': 1}
            recent_response = requests.get(RECENTLY_PLAYED_ENDPOINT, headers=headers, params=recent_params)
            recent_response.raise_for_status()
            recent_data = recent_response.json()
            
            if not recent_data.get("items"):
                return {"isPlaying": False, "hasData": False}

            last_track = recent_data["items"][0]["track"]
            track_info = {
                "isPlaying": False,
                "hasData": True,
                "title": last_track["name"],
                "artist": ", ".join(artist["name"] for artist in last_track["artists"]),
                "album": last_track["album"]["name"],
                "albumImageUrl": last_track["album"]["images"][0]["url"],
                "songUrl": last_track["external_urls"]["spotify"],
            }
            return track_info

        response.raise_for_status()
        data = response.json()

        if not data or not data.get("is_playing") or not data.get("item"):
            return {"isPlaying": False, "hasData": False}

        track_info = {
            "isPlaying": True,
            "hasData": True,
            "title": data["item"]["name"],
            "artist": ", ".join(artist["name"] for artist in data["item"]["artists"]),
            "album": data["item"]["album"]["name"],
            "albumImageUrl": data["item"]["album"]["images"][0]["url"],
            "songUrl": data["item"]["external_urls"]["spotify"],
        }
        return track_info

    except requests.exceptions.RequestException as e:
        return {"error": f"Could not connect to Spotify API: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}


@app.get("/api/top-tracks")
def get_top_tracks():
    """
    Gets the user's top 5 tracks from the last 4 weeks.
    """
    try:
        access_token = get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'time_range': 'short_term', # last 4 weeks
            'limit': 5
        }
        response = requests.get(TOP_TRACKS_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        tracks = []
        for item in data.get("items", []):
            track = {
                "title": item["name"],
                "artist": ", ".join(artist["name"] for artist in item["artists"]),
                "albumImageUrl": item["album"]["images"][2]["url"], # smaller image
                "songUrl": item["external_urls"]["spotify"],
            }
            tracks.append(track)
        
        return {"tracks": tracks}

    except requests.exceptions.RequestException as e:
        return {"error": f"Could not connect to Spotify API: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

@app.get("/api/top-artists")
def get_top_artists():
    """
    Gets the user's top 5 artists from the last 4 weeks.
    """
    try:
        access_token = get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'time_range': 'short_term',
            'limit': 5
        }
        response = requests.get(TOP_ARTISTS_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        artists = []
        for item in data.get("items", []):
            artist = {
                "name": item["name"],
                "imageUrl": item["images"][1]["url"] if len(item["images"]) > 1 else (item["images"][0]["url"] if item["images"] else "https://placehold.co/64x64/0b0c1a/ffffff?text=?"),
                "artistUrl": item["external_urls"]["spotify"],
            }
            artists.append(artist)
        
        return {"artists": artists}

    except requests.exceptions.RequestException as e:
        return {"error": f"Could not connect to Spotify API: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
