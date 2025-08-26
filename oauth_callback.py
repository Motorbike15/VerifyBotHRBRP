import json
import base64
import os
import requests

# ---------------- ENV VARIABLES ----------------
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
AUTHORIZED_FILE = os.environ.get("AUTHORIZED_FILE", "authorized_users.json")
BRANCH = os.environ.get("BRANCH", "main")
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REDIRECT_URI = os.environ["REDIRECT_URI"]

# ---------------- HELPER ----------------
def fetch_github_json():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    else:
        return {}, None

def push_github_json(content, sha=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    payload = {
        "message": "Add new verified user",
        "content": base64.b64encode(json.dumps(content).encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in [200, 201]

# ---------------- CALLBACK ----------------
def handler(request):
    code = request.args.get("code")
    state = request.args.get("state")  # user_id-guild_id

    if not code or not state:
        return {"statusCode": 400, "body": "Missing code or state"}

    user_id, guild_id = state.split("-")

    # Exchange code for access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "guilds.join"
    }
    token_res = requests.post("https://discord.com/api/oauth2/token", data=data)
    if token_res.status_code != 200:
        return {"statusCode": 400, "body": f"Failed to get token: {token_res.text}"}
    token_json = token_res.json()
    access_token = token_json.get("access_token")

    # Fetch current authorized_users.json
    users_json, sha = fetch_github_json()
    users_json[user_id] = {"guild_id": guild_id, "token": access_token}

    # Push back to GitHub
    if push_github_json(users_json, sha):
        return {"statusCode": 200, "body": "✅ Verified successfully!"}
    else:
        return {"statusCode": 500, "body": "Failed to update GitHub JSON."}
