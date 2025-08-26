import os
import json
import base64
import requests

# ---------- ENV VARIABLES ----------
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]      # Personal GitHub token with repo write access
GITHUB_REPO = os.environ["GITHUB_REPO"]        # e.g., Motorbike15/VerifyBotHRBRP
AUTHORIZED_FILE = os.environ.get("AUTHORIZED_FILE", "authorized_users.json")
BRANCH = os.environ.get("BRANCH", "main")
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REDIRECT_URI = os.environ["REDIRECT_URI"]      # Must match Discord exactly

# ---------- GitHub Helpers ----------
def fetch_github_json():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    return {}, None

def push_github_json(content, sha=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    payload = {
        "message": "Add/update verified user",
        "content": base64.b64encode(json.dumps(content).encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in [200, 201]

# ---------- Vercel handler ----------
def handler(request):
    code = request.args.get("code")
    state = request.args.get("state")  # user_id-guild_id
    if not code or not state:
        return {"statusCode": 400, "body": "Missing code or state."}

    user_id, guild_id = state.split("-")

    # --- Exchange code for access token ---
    token_data = {
        "client_id": str(CLIENT_ID),
        "client_secret": str(CLIENT_SECRET),
        "grant_type": "authorization_code",
        "code": str(code),
        "redirect_uri": str(REDIRECT_URI),
        "scope": "guilds.join"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_res = requests.post("https://discord.com/api/oauth2/token", data=token_data, headers=headers)

    if token_res.status_code != 200:
        return {"statusCode": 400, "body": f"Failed to get token: {token_res.text}"}

    access_token = token_res.json().get("access_token")
    if not access_token:
        return {"statusCode": 400, "body": "No access token returned."}

    # --- Update GitHub JSON ---
    users_json, sha = fetch_github_json()
    users_json[user_id] = {"guild_id": guild_id, "token": access_token}
    if push_github_json(users_json, sha):
        return {"statusCode": 200, "body": "✅ Verified successfully!"}

    return {"statusCode": 500, "body": "Failed to update GitHub JSON."}
