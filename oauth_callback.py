import json
import requests
import os

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
AUTHORIZED_FILE = os.environ.get("AUTHORIZED_FILE", "authorized_users.json")
BRANCH = os.environ.get("BRANCH", "main")

def handler(request):
    code = request.args.get("code")
    state = request.args.get("state")  # user_id-guild_id

    if not code or not state:
        return {"statusCode": 400, "body": "Missing code or state"}

    user_id, guild_id = state.split("-")

    # Here, exchange code for access_token via Discord OAuth2
    data = {
        "client_id": os.environ["CLIENT_ID"],
        "client_secret": os.environ["CLIENT_SECRET"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.environ["REDIRECT_URI"],
        "scope": "guilds.join"
    }
    token_res = requests.post("https://discord.com/api/oauth2/token", data=data)
    token_json = token_res.json()
    access_token = token_json.get("access_token")

    # Fetch existing authorized_users.json from GitHub
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        gh_data = r.json()
        content = json.loads(base64.b64decode(gh_data["content"]).decode("utf-8"))
        sha = gh_data["sha"]
    else:
        content = {}
        sha = None

    # Add new user
    content[user_id] = {"guild_id": guild_id, "token": access_token}

    # Push back to GitHub
    push_data = {
        "message": f"Add verified user {user_id}",
        "content": base64.b64encode(json.dumps(content).encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        push_data["sha"] = sha

    push_res = requests.put(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}", 
                            headers=headers, json=push_data)
    if push_res.status_code in [200, 201]:
        return {"statusCode": 200, "body": "User verified!"}
    else:
        return {"statusCode": push_res.status_code, "body": push_res.text}
