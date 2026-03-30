"""
Run this once on your PC to get a refresh token.
It will open a browser for you to log in with your Google account.
"""
from google_auth_oauthlib.flow import InstalledAppFlow
import json

# We use the "installed app" flow with Google's own client ID
# This is the same client ID used by many open source tools
CLIENT_CONFIG = {
    "installed": {
        "client_id": "977568789498-g5ib5qlhqhqhqhqhqhqhqhqhqhqhqhqh.apps.googleusercontent.com",
        "client_secret": "GOCSPX-placeholder",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

SCOPES = ["https://www.googleapis.com/auth/forms.responses.readonly"]

flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
creds = flow.run_local_server(port=0)

print("\n=== Save these to your .env and GitHub secrets ===")
print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
print(f"GOOGLE_CLIENT_ID={creds.client_id}")
print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
