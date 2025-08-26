from fastapi import FastAPI, Request
import httpx, json, os

app = FastAPI()

DATA_FILE = "authorized_users.json"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.get("/api/oauth_callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # e.g., "USERID-GUILDID"
    
    if not code or not state:
        return {"status": "error", "message": "Missing code or state"}

    user_id, guild_id = map(int, state.split("-"))

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

    # Save user info to authorized_users.json
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
        authorized_users.append({"user_id": user_id, "guild_id": guild_id, "token": access_token})

    with open(DATA_FILE, "w") as f:
        json.dump(authorized_users, f)

    return {"status": "ok", "message": "Authorization complete!"}
