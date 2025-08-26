import os
import json
import requests
from flask import request, redirect

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
AUTHORIZED_FILE = os.getenv("AUTHORIZED_FILE", "authorized_users.json")

def handler(req):
    code = req.args.get("code")
    state = req.args.get("state")  # contains user_id-guild_id
    if not code or not state:
        return "Missing code or state", 400

    user_id, guild_id = state.split("-")

    # 1. Exchange code for access token (verify they authorized)
    token_res = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": os.getenv("DISCORD_CLIENT_ID"),
            "client_secret": os.getenv("DISCORD_CLIENT_SECRET"),
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": os.getenv("REDIRECT_URI"),
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if token_res.status_code != 200:
        return f"OAuth failed: {token_res.text}", 400

    # 2. Fetch current authorized_users.json from GitHub
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(api_url, headers=headers)

    if res.status_code == 200:
        content = json.loads(res.text)
        existing = json.loads(
            requests.utils.unquote(content["content"])
            .encode("ascii")
            .decode("base64")
        )
        sha = content["sha"]
    else:
        existing = {}
        sha = None

    # 3. Add this user
    existing[user_id] = {"guild_id": guild_id}

    # 4. Push back to GitHub
    commit_msg = f"Add verified user {user_id}"
    update_res = requests.put(
        api_url,
        headers=headers,
        json={
            "message": commit_msg,
            "content": json.dumps(existing).encode("utf-8").decode("utf-8"),
            "sha": sha,
        },
    )

    if update_res.status_code not in [200, 201]:
        return f"Failed to update GitHub: {update_res.text}", 500

    return redirect("https://discord.com/channels/@me")  # send them back to Discord
