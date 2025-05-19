from flask import Flask, jsonify
from flask_cors import CORS
import msal
import requests
import os

app = Flask(__name__)
CORS(app)

# Load config from environment variables
TENANT_ID = os.getenv('TENANT_ID')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
WORKSPACE_ID = os.getenv('WORKSPACE_ID')
REPORT_ID = os.getenv('REPORT_ID')

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
POWER_BI_API = "https://api.powerbi.com/v1.0/myorg"

@app.route("/get-embed-config")
def get_embed_config():
    # Authenticate using MSAL
    app_auth = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )

    token_response = app_auth.acquire_token_for_client(scopes=SCOPE)
    access_token = token_response["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Get Embed Token
    embed_token_url = f"{POWER_BI_API}/groups/{WORKSPACE_ID}/reports/{REPORT_ID}/GenerateToken"
    embed_token_body = {
        "accessLevel": "view"
    }

    token_resp = requests.post(embed_token_url, headers=headers, json=embed_token_body)
    embed_token = token_resp.json()["token"]

    # Get Embed URL
    report_info_url = f"{POWER_BI_API}/groups/{WORKSPACE_ID}/reports/{REPORT_ID}"
    report_info = requests.get(report_info_url, headers=headers).json()

    return jsonify({
        "id": REPORT_ID,
        "embedUrl": report_info["embedUrl"],
        "accessToken": embed_token
    })

if __name__ == '__main__':
    app.run(debug=True)
