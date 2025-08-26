# oauth_callback.py
import os, json, base64, requests
from urllib.parse import parse_qs

# Environment variables in Vercel
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]          # GitHub token with repo write
GITHUB_REPO = os.environ["GITHUB_REPO"]            # e.g., Motorbike15/VerifyBotHRBRP
AUTHORIZED_FILE = "authorized_users.json"
BRANCH = "main"

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REDIRECT_URI = os.environ["REDIRECT_URI"]          # e.g., https://verify-bot-hrbrp.vercel.app/api/oauth_callback

# ---------------- Update GitHub JSON ----------------
def update_github_json(user_id, guild_id, token):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    data = r.json()

    if "content" in data:
        content = base64.b64decode(data["content"]).decode("utf-8")
        users = json.loads(content)
        sha = data["sha"]
    else:
        users = {}
        sha = None

    users[str(user_id)] = {"guild_id": str(guild_id), "token": token}

    payload = {
        "message": f"Add/update authorized user {user_id}",
        "content": base64.b64encode(json.dumps(users).encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    r2 = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}",
        headers=headers, json=payload
    )
    return r2.status_code in [200, 201]

# ---------------- Vercel handler ----------------
def handler(event, context=None):
    try:
        # Parse query string
        query = parse_qs(event.get("queryStringParameters") or {})
        code = query.get("code", [""])[0]
        state = query.get("state", [""])[0]
        user_id, guild_id = state.split("-")

        # Exchange code for access token
        token_url = "https://discord.com/api/oauth2/token"
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "scope": "guilds.join"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = requests.post(token_url, data=data, headers=headers)
        r.raise_for_status()
        access_token = r.json()["access_token"]

        # Update GitHub JSON
        success = update_github_json(user_id, guild_id, access_token)
        if success:
            return {"statusCode": 200, "body": "✅ Verified successfully!"}
        return {"statusCode": 500, "body": "⚠️ Failed to update GitHub."}
    except Exception as e:
        return {"statusCode": 500, "body": f"⚠️ Exception: {e}"}
