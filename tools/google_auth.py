"""
Google OAuth2 authentication for Sheets, Gmail, Slides, and Drive APIs.

Usage:
    from tools.google_auth import get_credentials, get_sheets_service, get_gmail_service
    from tools.google_auth import get_slides_service, get_drive_service

First run will open a browser for OAuth consent. Subsequent runs use cached token.json.
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Scopes required for the app
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive",
]

CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"


def get_credentials() -> Credentials:
    """Get valid Google OAuth2 credentials, refreshing or re-authenticating as needed."""
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
                    "Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def get_sheets_service():
    """Return an authenticated Google Sheets API service."""
    creds = get_credentials()
    return build("sheets", "v4", credentials=creds)


def get_gmail_service():
    """Return an authenticated Gmail API service."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def get_slides_service():
    """Return an authenticated Google Slides API service."""
    creds = get_credentials()
    return build("slides", "v1", credentials=creds)


def get_drive_service():
    """Return an authenticated Google Drive API service."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


if __name__ == "__main__":
    # Test authentication
    print("Authenticating with Google...")
    creds = get_credentials()
    print(f"Authenticated successfully. Token saved to {TOKEN_FILE}")
