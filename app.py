from flask import Flask, jsonify
from flask_cors import CORS
import msal
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Constants
TENANT_ID = 'e5f0cfce-d804-44f9-8ef7-d7ce7a67e625'
CLIENT_ID = '0d72d657-50de-473d-97a1-e843c3719810'
CLIENT_SECRET = 'FKA8Q~iR_lYZbxZuPBQRACzERg4Q5D2DD_zy9anG'
WORKSPACE_ID = '68873687-ccc9-4cdf-8432-44082c299565'
REPORT_ID = '01d470e6-af29-4883-80bd-4366b179ec21'

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
POWER_BI_API = "https://api.powerbi.com/v1.0/myorg"

@app.route("/get-embed-config")
def get_embed_config():
    try:
        # Acquire access token
        app_auth = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            client_credential=CLIENT_SECRET
        )
        token_response = app_auth.acquire_token_for_client(scopes=SCOPE)
        if "access_token" not in token_response:
            return jsonify({"error": "Token fetch failed", "details": token_response}), 500

        access_token = token_response["access_token"]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Get report details
        report_url = f"{POWER_BI_API}/groups/{WORKSPACE_ID}/reports/{REPORT_ID}"
        report_resp = requests.get(report_url, headers=headers)
        if report_resp.status_code != 200:
            return jsonify({"error": "Failed to get report info", "details": report_resp.json()}), 500

        report_data = report_resp.json()
        dataset_id = report_data.get("datasetId")
        embed_url = report_data.get("embedUrl")

        if not dataset_id or not embed_url:
            return jsonify({"error": "Missing datasetId or embedUrl", "details": report_data}), 500

        # Generate embed token without identities
        embed_token_url = f"{POWER_BI_API}/GenerateToken"
        embed_token_body = {
            "datasets": [{"id": dataset_id}],
            "reports": [{"id": REPORT_ID}],
            "targetWorkspaces": [{"id": WORKSPACE_ID}],
            "accessLevel": "view"
        }

        token_resp = requests.post(embed_token_url, headers=headers, json=embed_token_body)
        if token_resp.status_code != 200:
            return jsonify({"error": "Embed token request failed", "details": token_resp.json()}), 500

        embed_token = token_resp.json().get("token")
        if not embed_token:
            return jsonify({"error": "Token missing in response", "details": token_resp.json()}), 500

        return jsonify({
            "accessToken": embed_token,
            "embedUrl": embed_url,
            "id": REPORT_ID,
            "tokenType": "Embed"
        })

    except Exception as e:
        return jsonify({"error": "Server exception", "message": str(e)}), 500

# Only run the app if this script is executed directly (not via debugger)
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
