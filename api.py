from flask import Flask, request

app = Flask(__name__)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    # Here you can store the code in a database or just log it
    print(f"Received OAuth2 code: {code}")
    return "✅ Authorization successful! You can close this page."

if __name__ == "__main__":
    app.run()
