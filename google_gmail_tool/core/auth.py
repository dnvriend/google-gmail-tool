"""Authentication and credential management for Google APIs.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


def get_credentials() -> Credentials:
    """Load OAuth2 credentials from environment variables or file.

    Supports multiple authentication methods in order:
    1. GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON - Full credentials as JSON string
    2. GOOGLE_GMAIL_TOOL_CREDENTIALS - Path to credentials JSON file
    3. GOOGLE_APPLICATION_CREDENTIALS - Application Default Credentials (not supported)

    Returns:
        Credentials object for accessing Google APIs

    Raises:
        AuthenticationError: If credentials cannot be loaded or are invalid

    Example credential JSON format:
        {
            "type": "authorized_user",
            "client_id": "...",
            "client_secret": "...",
            "refresh_token": "..."
        }
    """
    # Method 1: JSON string from environment
    creds_json = os.environ.get("GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON")
    if creds_json:
        try:
            creds_data = json.loads(creds_json)
            credentials = Credentials.from_authorized_user_info(creds_data)  # type: ignore[no-untyped-call]
            return _refresh_if_needed(credentials)
        except (json.JSONDecodeError, ValueError) as e:
            raise AuthenticationError(
                f"Invalid GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON format: {e}\n"
                "Expected JSON with: client_id, client_secret, refresh_token"
            ) from e

    # Method 2: File path from environment
    creds_file = os.environ.get("GOOGLE_GMAIL_TOOL_CREDENTIALS")
    if creds_file:
        creds_path = Path(creds_file).expanduser()
        if not creds_path.exists():
            raise AuthenticationError(
                f"Credentials file not found: {creds_path}\n"
                f"Set GOOGLE_GMAIL_TOOL_CREDENTIALS to valid path or use "
                f"GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON"
            )
        try:
            credentials = Credentials.from_authorized_user_file(str(creds_path))  # type: ignore[no-untyped-call]
            return _refresh_if_needed(credentials)
        except (ValueError, json.JSONDecodeError) as e:
            raise AuthenticationError(
                f"Invalid credentials file format: {creds_path}\n"
                f"Error: {e}\n"
                f"Expected JSON with: client_id, client_secret, refresh_token"
            ) from e

    # Method 3: Application Default Credentials (not supported)
    adc_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if adc_file:
        raise AuthenticationError(
            "GOOGLE_APPLICATION_CREDENTIALS detected but not supported for OAuth flows.\n"
            "Use GOOGLE_GMAIL_TOOL_CREDENTIALS or GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON instead.\n\n"
            "To create OAuth credentials:\n"
            "1. Visit Google Cloud Console: https://console.cloud.google.com/apis/credentials\n"
            "2. Create OAuth 2.0 Client ID (Desktop application)\n"
            "3. Download JSON and set GOOGLE_GMAIL_TOOL_CREDENTIALS=/path/to/credentials.json"
        )

    # No credentials found
    raise AuthenticationError(
        "No Google OAuth credentials found.\n\n"
        "Set one of the following environment variables:\n"
        "  GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON  - Full credentials as JSON string\n"
        "  GOOGLE_GMAIL_TOOL_CREDENTIALS       - Path to credentials JSON file\n\n"
        "To obtain credentials:\n"
        "1. Visit: https://console.cloud.google.com/apis/credentials\n"
        "2. Create OAuth 2.0 Client ID (Desktop application)\n"
        "3. Download JSON file\n"
        "4. Set: export GOOGLE_GMAIL_TOOL_CREDENTIALS=/path/to/credentials.json"
    )


def _refresh_if_needed(credentials: Credentials) -> Credentials:
    """Refresh credentials if expired or no access token.

    Args:
        credentials: Credentials object to refresh

    Returns:
        Refreshed credentials

    Raises:
        AuthenticationError: If refresh fails
    """
    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())  # type: ignore[no-untyped-call]
            except Exception as e:
                raise AuthenticationError(
                    f"Failed to refresh access token: {e}\n"
                    "Your refresh token may be invalid or revoked.\n"
                    "Generate new credentials from Google Cloud Console."
                ) from e
        else:
            raise AuthenticationError(
                "Credentials are invalid and cannot be refreshed.\n"
                "Missing refresh_token. Generate new credentials."
            )
    return credentials


def verify_api_access(credentials: Credentials) -> dict[str, dict[str, str | bool | None]]:
    """Verify access to Gmail, Calendar, Tasks, and Drive APIs.

    Args:
        credentials: OAuth2 credentials to test

    Returns:
        Dictionary with test results for each API:
        {
            "gmail": {"success": True, "message": "Access granted", "error": None},
            "calendar": {"success": False, "message": "...", "error": "..."},
            "tasks": {"success": True, "message": "Access granted", "error": None},
            "drive": {"success": True, "message": "Access granted", "error": None}
        }
    """
    results: dict[str, dict[str, str | bool | None]] = {}

    # Test Gmail API
    try:
        service = build("gmail", "v1", credentials=credentials)
        service.users().getProfile(userId="me").execute()
        results["gmail"] = {
            "success": True,
            "message": "Gmail API access granted",
            "error": None,
        }
    except Exception as e:
        results["gmail"] = {
            "success": False,
            "message": "Gmail API access denied",
            "error": str(e),
        }

    # Test Calendar API
    try:
        service = build("calendar", "v3", credentials=credentials)
        service.calendarList().list(maxResults=1).execute()
        results["calendar"] = {
            "success": True,
            "message": "Calendar API access granted",
            "error": None,
        }
    except Exception as e:
        results["calendar"] = {
            "success": False,
            "message": "Calendar API access denied",
            "error": str(e),
        }

    # Test Tasks API
    try:
        service = build("tasks", "v1", credentials=credentials)
        service.tasklists().list(maxResults=1).execute()
        results["tasks"] = {
            "success": True,
            "message": "Tasks API access granted",
            "error": None,
        }
    except Exception as e:
        results["tasks"] = {
            "success": False,
            "message": "Tasks API access denied",
            "error": str(e),
        }

    # Test Drive API
    try:
        service = build("drive", "v3", credentials=credentials)
        service.about().get(fields="user").execute()
        results["drive"] = {
            "success": True,
            "message": "Drive API access granted",
            "error": None,
        }
    except Exception as e:
        results["drive"] = {
            "success": False,
            "message": "Drive API access denied",
            "error": str(e),
        }

    return results
