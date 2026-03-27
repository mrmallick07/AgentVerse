"""
Google API Authentication Module.
Handles OAuth2 for Calendar/Docs/Drive and API Key for Search/YouTube/Maps.
"""

import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# Scopes needed for Calendar, Docs, and Drive
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

# API Key for Search, YouTube, Maps — uses GCP_API_KEY or falls back to GOOGLE_API_KEY
GCP_API_KEY = os.getenv("GCP_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "")


def get_oauth_credentials() -> Credentials:
    """Get OAuth2 credentials, running the auth flow if needed."""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_FILE}. "
                    "Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future use
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def get_calendar_service():
    """Return an authenticated Google Calendar service object."""
    creds = get_oauth_credentials()
    return build("calendar", "v3", credentials=creds)


def get_docs_service():
    """Return an authenticated Google Docs service object."""
    creds = get_oauth_credentials()
    return build("docs", "v1", credentials=creds)


def get_drive_service():
    """Return an authenticated Google Drive service object."""
    creds = get_oauth_credentials()
    return build("drive", "v3", credentials=creds)
