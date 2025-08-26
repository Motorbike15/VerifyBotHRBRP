import json
import os
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

# File in repo where authorized users will be stored
DATA_FILE = "authorized_users.json"

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # must match Discord OAuth2 redirect

@app.get("/oauth_callback")
async def oauth_callback(code: str, user_id: str, guild_id: str):
    # Exchange code for token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "guilds.join"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://discord.com/api/oauth2/token", data=data)
        token_json = resp.json()
        access_token = token_json.get("access_token")
    
    if not access_token:
        return {"status": "error", "message": "Failed to get token"}

    # Read current authorized users
    try:
        with open(DATA_FILE, "r") as f:
            authorized_users = json.load(f)
    except FileNotFoundError:
        authorized_users = []

    # Add new authorized user
    authorized_users.append({
        "user_id": int(user_id),
        "guild_id": int(guild_id),
        "token": access_token
    })

    # Save back to GitHub repo (or local file if testing)
    with open(DATA_FILE, "w") as f:
        json.dump(authorized_users, f)

    return {"status": "ok", "message": "Authorization complete!"}
