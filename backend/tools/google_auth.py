"""
Google Auth — Application Default Credentials.
Works automatically in Cloud Run via Service Account.
"""
import google.auth
from googleapiclient.discovery import build


def get_calendar_service():
    """Get Google Calendar API service."""
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=creds)


def get_docs_service():
    """Get Google Docs API service."""
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/documents",
                "https://www.googleapis.com/auth/drive"]
    )
    return build("docs", "v1", credentials=creds)


def get_drive_service():
    """Get Google Drive API service."""
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)