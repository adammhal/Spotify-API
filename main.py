# main.py
import os
import base64
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

# API endpoints
TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"
NOW_PLAYING_ENDPOINT = "https://api.spotify.com/v1/me/player/currently-playing"
RECENTLY_PLAYED_ENDPOINT = "https://api.spotify.com/v1/me/player/recently-played"
TOP_TRACKS_ENDPOINT = "https://api.spotify.com/v1/me/top/tracks"
TOP_ARTISTS_ENDPOINT = "https://api.spotify.com/v1/me/top/artists"
STEAM_API_ENDPOINT = "https://store.steampowered.com/api/appdetails"

# FastAPI app setup
app = FastAPI()

origins = [
    "http://127.0.0.1:5500",
    "https://adammhal.github.io",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_access_token():
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    payload = {'grant_type': 'refresh_token', 'refresh_token': REFRESH_TOKEN}
    headers = {'Authorization': f'Basic {b64_auth_str}', 'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(TOKEN_ENDPOINT, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()['access_token']

# ... (all your existing Spotify endpoints remain here) ...

@app.get("/api/now-playing")
def get_now_playing():
    try:
        access_token = get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(NOW_PLAYING_ENDPOINT, headers=headers)
        if response.status_code == 204:
            recent_params = {'limit': 1}
            recent_response = requests.get(RECENTLY_PLAYED_ENDPOINT, headers=headers, params=recent_params)
            recent_response.raise_for_status()
            recent_data = recent_response.json()
            if not recent_data.get("items"): return {"isPlaying": False, "hasData": False}
            last_track = recent_data["items"][0]["track"]
            return {"isPlaying": False, "hasData": True, "title": last_track["name"], "artist": ", ".join(artist["name"] for artist in last_track["artists"]), "album": last_track["album"]["name"], "albumImageUrl": last_track["album"]["images"][0]["url"], "songUrl": last_track["external_urls"]["spotify"]}
        response.raise_for_status()
        data = response.json()
        if not data or not data.get("is_playing") or not data.get("item"): return {"isPlaying": False, "hasData": False}
        return {"isPlaying": True, "hasData": True, "title": data["item"]["name"], "artist": ", ".join(artist["name"] for artist in data["item"]["artists"]), "album": data["item"]["album"]["name"], "albumImageUrl": data["item"]["album"]["images"][0]["url"], "songUrl": data["item"]["external_urls"]["spotify"]}
    except requests.exceptions.RequestException as e: return {"error": f"Could not connect to Spotify API: {e}"}
    except Exception as e: return {"error": f"An unexpected error occurred: {e}"}

@app.get("/api/top-tracks")
def get_top_tracks():
    try:
        access_token = get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'time_range': 'short_term', 'limit': 4}
        response = requests.get(TOP_TRACKS_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        tracks = [{"title": item["name"], "artist": ", ".join(artist["name"] for artist in item["artists"]), "albumImageUrl": item["album"]["images"][1]["url"] if len(item["album"]["images"]) > 1 else item["album"]["images"][0]["url"], "songUrl": item["external_urls"]["spotify"]} for item in data.get("items", [])]
        return {"tracks": tracks}
    except requests.exceptions.RequestException as e: return {"error": f"Could not connect to Spotify API: {e}"}
    except Exception as e: return {"error": f"An unexpected error occurred: {e}"}

@app.get("/api/top-artists")
def get_top_artists():
    try:
        access_token = get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'time_range': 'short_term', 'limit': 4}
        response = requests.get(TOP_ARTISTS_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        artists = [{"name": item["name"], "imageUrl": item["images"][1]["url"] if len(item["images"]) > 1 else (item["images"][0]["url"] if item["images"] else "https://placehold.co/64x64/0b0c1a/ffffff?text=?"), "artistUrl": item["external_urls"]["spotify"]} for item in data.get("items", [])]
        return {"artists": artists}
    except requests.exceptions.RequestException as e: return {"error": f"Could not connect to Spotify API: {e}"}
    except Exception as e: return {"error": f"An unexpected error occurred: {e}"}


@app.get("/api/steam-game")
def get_steam_game_details(appid: str):
    """
    Gets details for a specific Steam game by its App ID.
    """
    try:
        params = {'appids': appid}
        response = requests.get(STEAM_API_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()

        if not data or not data.get(appid) or not data[appid].get('success'):
            raise HTTPException(status_code=404, detail="Game not found or API error.")

        game_data = data[appid]['data']
        
        return {
            "name": game_data.get("name"),
            "description": game_data.get("short_description"),
            "imageUrl": game_data.get("header_image"), # This is the horizontal banner
            "steamUrl": f"https://store.steampowered.com/app/{appid}"
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not connect to Steam API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
# END: New Steam Game Endpoint
