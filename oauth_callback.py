# oauth_callback.py
from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

# Bot endpoint that receives verified users
# Can be your bot running a small local API or a Discord webhook URL
BOT_WEBHOOK_URL = os.getenv("BOT_WEBHOOK_URL")  # e.g., http://<your-pi-ip>:5000/verify_user

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # e.g., https://your-vercel-project.vercel.app/oauth_callback

@app.get("/oauth_callback")
async def oauth_callback(code: str, state: str = None, guild_id: str = None, user_id: str = None):
    """
    This endpoint is called by Discord after the user authorizes the bot.
    It exchanges the OAuth2 code for an access token and notifies your bot.
    """
    if not all([code, user_id, guild_id]):
        return {"status": "error", "message": "Missing parameters"}

    # Exchange code for access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "guilds.join"
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post("https://discord.com/api/oauth2/token", data=data)
        token_json = token_response.json()
        access_token = token_json.get("access_token")

    if not access_token:
        return {"status": "error", "message": "Failed to get access token"}

    # Notify bot
    if BOT_WEBHOOK_URL:
        async with httpx.AsyncClient() as client:
            await client.post(
                BOT_WEBHOOK_URL,
                json={
                    "user_id": int(user_id),
                    "guild_id": int(guild_id),
                    "token": access_token
                }
            )

    return {"status": "ok", "message": "Authorization complete"}
