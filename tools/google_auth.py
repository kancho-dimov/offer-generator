"""
Google authentication for Sheets, Gmail, Slides, and Drive APIs.

Supports two modes:
  1. Service account (Cloud Run / headless) — via GOOGLE_SERVICE_ACCOUNT_JSON env var
     or service_account.json file. Used for Sheets, Drive, Slides.
  2. OAuth Desktop flow (local dev) — via credentials.json + token.json.
     Also used for Gmail (service accounts can't send Gmail without Workspace delegation).

Usage:
    from tools.google_auth import get_sheets_service, get_gmail_service
    from tools.google_auth import get_slides_service, get_drive_service
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Scopes required for the app (narrowed to minimum necessary)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.file",
]

# Scopes that work with service accounts (Gmail excluded)
SA_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive",
]

SERVICE_ACCOUNT_FILE = PROJECT_ROOT / "service_account.json"
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"


def _get_service_account_creds():
    """Try to load service account credentials (for Sheets/Drive/Slides)."""
    # Option 1: JSON content in env var (Cloud Run Secret Manager)
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        info = json.loads(sa_json)
        return service_account.Credentials.from_service_account_info(info, scopes=SA_SCOPES)

    # Option 2: JSON file on disk
    if SERVICE_ACCOUNT_FILE.exists():
        return service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE), scopes=SA_SCOPES
        )

    return None


def _get_oauth_creds():
    """Get OAuth2 user credentials (for Gmail, or local dev for everything)."""
    creds = None

    # Option 1: Token JSON in env var (Cloud Run — for Gmail)
    token_json = os.environ.get("GOOGLE_OAUTH_TOKEN_JSON")
    if token_json:
        info = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(info, SCOPES)
    elif TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token locally (not on Cloud Run)
            if TOKEN_FILE.exists():
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
        else:
            # Interactive flow — only works on local dev with a browser
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_FILE}. "
                    "Download it from Google Cloud Console."
                )
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

    return creds


def get_credentials():
    """Get credentials for Sheets/Drive/Slides.

    Uses OAuth user credentials because service accounts on consumer
    Google accounts have zero Drive storage and cannot create files.
    Service account credentials are only useful for Workspace accounts
    with domain-wide delegation.
    """
    return _get_oauth_creds()


def get_gmail_credentials():
    """Get OAuth2 credentials specifically for Gmail (service accounts can't send Gmail)."""
    return _get_oauth_creds()


def get_sheets_service():
    """Return an authenticated Google Sheets API service."""
    return build("sheets", "v4", credentials=get_credentials())


def get_gmail_service():
    """Return an authenticated Gmail API service (always uses OAuth, not service account)."""
    return build("gmail", "v1", credentials=get_gmail_credentials())


def get_slides_service():
    """Return an authenticated Google Slides API service."""
    return build("slides", "v1", credentials=get_credentials())


def get_drive_service():
    """Return an authenticated Google Drive API service."""
    return build("drive", "v3", credentials=get_credentials())


if __name__ == "__main__":
    print("Authenticating with Google...")
    creds = get_credentials()
    sa = _get_service_account_creds()
    if sa:
        print("Using service account credentials (Sheets/Drive/Slides)")
    else:
        print("Using OAuth desktop credentials (all APIs)")
    print(f"Token file: {TOKEN_FILE}")
    print("Authentication successful.")
