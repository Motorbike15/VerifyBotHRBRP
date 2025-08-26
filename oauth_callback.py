# oauth_callback.py
import os, json, base64, requests
from urllib.parse import parse_qs

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPO"]   # e.g., Motorbike15/VerifyBotHRBRP
AUTHORIZED_FILE = "authorized_users.json"
BRANCH = "main"

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

    # add/update the authorized user
    users[str(user_id)] = {"guild_id": str(guild_id), "token": token}

    payload = {
        "message": f"Add/update authorized user {user_id}",
        "content": base64.b64encode(json.dumps(users).encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    r2 = requests.put(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{AUTHORIZED_FILE}",
                      headers=headers, json=payload)
    return r2.status_code in [200, 201]

# Simulated Vercel request handling
def handler(event):
    query = parse_qs(event.get("queryStringParameters") or {})
    code = query.get("code", [""])[0]
    state = query.get("state", [""])[0]
    user_id, guild_id = state.split("-")
    
    # Here you would exchange `code` for a token from Discord
    # For now, we simulate with a dummy token
    token = "SIMULATED_ACCESS_TOKEN"

    success = update_github_json(user_id, guild_id, token)
    if success:
        return {"statusCode": 200, "body": "✅ Verified!"}
    return {"statusCode": 500, "body": "⚠️ Failed to update GitHub"}
