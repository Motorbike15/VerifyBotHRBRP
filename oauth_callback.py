import os
import json
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

DATA_FILE = "authorized_users.json"  # Stored in your repo
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # e.g. https://your-vercel-project.vercel.app/api/oauth_callback

@app.get("/oauth_callback")
async def oauth_callback(code: str, state: str):
    """
    Receives Discord OAuth2 redirect.
    `state` contains user_id and guild_id: "<USER_ID>-<GUILD_ID>"
    """
    try:
        user_id_str, guild_id_str = state.split("-")
        user_id = int(user_id_str)
        guild_id = int(guild_id_str)
    except Exception:
        return {"status": "error", "message": "Invalid state parameter"}

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

    # Load existing authorized users
    try:
        with open(DATA_FILE, "r") as f:
            authorized_users = json.load(f)
    except FileNotFoundError:
        authorized_users = []

    # Add or update user
    exists = False
    for u in authorized_users:
        if u["user_id"] == user_id and u["guild_id"] == guild_id:
            u["token"] = access_token
            exists = True
            break
    if not exists:
        authorized_users.append({
            "user_id": user_id,
            "guild_id": guild_id,
            "token": access_token
        })

    # Save JSON back (push to GitHub in real setup)
    with open(DATA_FILE, "w") as f:
        json.dump(authorized_users, f)

    return {"status": "ok", "message": "Verification complete!"}
