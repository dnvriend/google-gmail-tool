"""Authentication verification commands.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
import sys
from pathlib import Path

import click
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]

from google_gmail_tool.core.auth import AuthenticationError, get_credentials, verify_api_access
from google_gmail_tool.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# OAuth scopes for Gmail, Calendar, Tasks, and Drive access
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",  # Read Gmail
    "https://www.googleapis.com/auth/gmail.send",  # Send Gmail
    "https://www.googleapis.com/auth/calendar",  # Full Calendar (read, create, update, delete)
    "https://www.googleapis.com/auth/tasks",  # Full Tasks (read, create, update, delete)
    "https://www.googleapis.com/auth/drive.readonly",  # Read Drive
]


@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)",
)
def check(verbose: int) -> None:
    """Verify Google OAuth credentials and API access.

    Tests authentication and checks access to Gmail, Calendar, and Drive APIs.
    Displays results with checkmarks (✓) for granted access or crosses (✗) for denied.

    This command validates:
    - OAuth credential format and validity
    - Access token refresh capability
    - Individual API permissions (Gmail, Calendar, Drive)

    \b
    Environment Variables:
    \b
        GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON    Full OAuth2 credentials as JSON string
        GOOGLE_GMAIL_TOOL_CREDENTIALS         Path to OAuth2 credentials JSON file

    \b
    Required Credential Format (JSON):
    \b
        {
            "type": "authorized_user",
            "client_id": "...",
            "client_secret": "...",
            "refresh_token": "..."
        }

    \b
    Examples:

    \b
        # Basic auth check (warnings only)
        google-gmail-tool auth check

    \b
        # Verbose mode (INFO level)
        google-gmail-tool auth check -v

    \b
        # Debug mode (DEBUG level)
        google-gmail-tool auth check -vv

    \b
        # Trace mode (DEBUG + Google API library internals)
        google-gmail-tool auth check -vvv

    \b
        # Using credentials from file
        export GOOGLE_GMAIL_TOOL_CREDENTIALS=~/.config/google-gmail-tool/credentials.json
        google-gmail-tool auth check

    \b
        # Using credentials from JSON string
        export GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON='{"type":"authorized_user",...}'
        google-gmail-tool auth check

    \b
    Exit Codes:
        0    All API checks passed
        1    Authentication failed or one or more API checks failed

    \b
    Troubleshooting:
        If APIs fail, ensure OAuth scopes include:
        - https://www.googleapis.com/auth/gmail.readonly
        - https://www.googleapis.com/auth/calendar (full access for create/update/delete)
        - https://www.googleapis.com/auth/tasks (full access for all operations)
        - https://www.googleapis.com/auth/drive.readonly

        Generate new credentials at:
        https://console.cloud.google.com/apis/credentials
    """
    # Setup logging based on verbosity
    setup_logging(verbose)
    logger.debug("Starting auth check command")

    click.echo("🔐 Checking Google OAuth credentials...")
    click.echo()

    # Step 1: Load credentials
    try:
        logger.info("Loading OAuth credentials from environment")
        credentials = get_credentials()
        logger.debug(f"Credentials loaded: valid={credentials.valid}")
        logger.debug(f"Has refresh token: {bool(credentials.refresh_token)}")

        click.echo("✓ Credentials loaded successfully")
        click.echo(f"  Token valid: {credentials.valid}")
        click.echo(f"  Has refresh token: {bool(credentials.refresh_token)}")
        click.echo()
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        logger.debug("Credential loading failed", exc_info=True)
        click.echo("✗ Failed to load credentials", err=True)
        click.echo()
        click.echo(str(e), err=True)
        sys.exit(1)

    # Step 2: Verify API access
    click.echo("🔍 Verifying API access...")
    click.echo()
    logger.info("Testing API access for Gmail, Calendar, Tasks, and Drive")

    results = verify_api_access(credentials)
    logger.debug(f"API access results: {results}")

    # Display results
    all_passed = True
    for api_name, result in results.items():
        success = result["success"]
        message = result["message"]

        if success:
            logger.info(f"{api_name.upper()}: Access granted")
            click.echo(f"✓ {api_name.upper()}: {message}")
        else:
            logger.error(f"{api_name.upper()}: Access denied")
            if result.get("error"):
                logger.debug(f"{api_name.upper()} error: {result['error']}")
            click.echo(f"✗ {api_name.upper()}: {message}", err=True)
            all_passed = False

            # Show error details in debug/trace mode
            if verbose >= 2 and result.get("error"):
                click.echo(f"  Error: {result['error']}", err=True)

    click.echo()

    # Summary
    if all_passed:
        logger.info("All API checks passed successfully")
        click.echo("✅ All API checks passed! You're ready to use google-gmail-tool.")
        sys.exit(0)
    else:
        logger.error("Some API checks failed")
        click.echo(
            "❌ Some API checks failed. Review errors above and ensure OAuth scopes are correct.",
            err=True,
        )
        click.echo()
        click.echo("Required OAuth scopes:", err=True)
        click.echo("  - https://www.googleapis.com/auth/gmail.readonly", err=True)
        click.echo("  - https://www.googleapis.com/auth/calendar", err=True)
        click.echo("  - https://www.googleapis.com/auth/tasks", err=True)
        click.echo("  - https://www.googleapis.com/auth/drive.readonly", err=True)
        sys.exit(1)


@click.command()
@click.option(
    "--client-id",
    help="OAuth Client ID from Google Cloud Console",
)
@click.option(
    "--client-secret",
    help="OAuth Client Secret from Google Cloud Console",
)
@click.option(
    "--json-file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to client secret JSON file (alternative to --client-id/--client-secret)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file for authorized credentials "
    "(default: ~/.config/google-gmail-tool/credentials.json)",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)",
)
def login(
    client_id: str | None,
    client_secret: str | None,
    json_file: Path | None,
    output: Path | None,
    verbose: int,
) -> None:
    """Complete OAuth flow to obtain authorized credentials.

    This command starts an OAuth flow in your browser using your Client ID and
    Client Secret. After you authorize the application, it saves the credentials
    with access and refresh tokens.

    \b
    Get Client ID and Secret:
        1. Go to: https://console.cloud.google.com/apis/credentials
        2. Click on your OAuth 2.0 Client ID
        3. Copy the Client ID and Client Secret

    \b
    Examples:

    \b
        # Using client ID and secret directly
        google-gmail-tool auth login \\
          --client-id "YOUR_CLIENT_ID.apps.googleusercontent.com" \\
          --client-secret "YOUR_CLIENT_SECRET"

    \b
        # Using client secret JSON file (downloaded from console)
        google-gmail-tool auth login --json-file ~/Downloads/client_secret.json

    \b
        # Specify custom output location
        google-gmail-tool auth login \\
          --json-file client_secret.json \\
          --output my_creds.json

    \b
        # After login, set environment variable and verify
        export GOOGLE_GMAIL_TOOL_CREDENTIALS=~/.config/google-gmail-tool/credentials.json
        google-gmail-tool auth check

    \b
    Required OAuth Scopes:
        - https://www.googleapis.com/auth/gmail.readonly
        - https://www.googleapis.com/auth/gmail.send
        - https://www.googleapis.com/auth/calendar (full access)
        - https://www.googleapis.com/auth/tasks (full access)
        - https://www.googleapis.com/auth/drive.readonly

    \b
    Exit Codes:
        0    Success - credentials saved
        1    OAuth flow failed or error occurred
    """
    # Setup logging based on verbosity
    setup_logging(verbose)
    logger.debug("Starting OAuth login flow")

    click.echo("🔐 Starting OAuth flow...")
    click.echo()

    # Validate input: either json-file OR client-id/client-secret
    if json_file:
        if client_id or client_secret:
            click.echo("Error: Cannot use --json-file with --client-id/--client-secret", err=True)
            sys.exit(2)
    else:
        if not client_id or not client_secret:
            click.echo(
                "Error: Must provide either --json-file or both --client-id and --client-secret",
                err=True,
            )
            sys.exit(2)

    # Default output location
    if output is None:
        output = Path.home() / ".config" / "google-gmail-tool" / "credentials.json"
        logger.debug(f"Using default output location: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
    else:
        logger.debug(f"Using custom output location: {output}")

    try:
        # Create OAuth flow
        logger.debug(f"Requesting OAuth scopes: {SCOPES}")

        if json_file:
            # Load from JSON file
            logger.info(f"Reading client secret file: {json_file}")
            flow = InstalledAppFlow.from_client_secrets_file(str(json_file), SCOPES)
        else:
            # Use provided client ID and secret
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        logger.info("Opening browser for OAuth authorization...")
        click.echo("🌐 Opening browser for authorization...")
        click.echo("Grant all permissions when prompted.")
        click.echo()

        credentials = flow.run_local_server(port=0)
        logger.debug("OAuth authorization completed, received credentials")

        # Save credentials
        creds_data = {
            "type": "authorized_user",
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "refresh_token": credentials.refresh_token,
        }
        logger.debug(f"Saving credentials to: {output}")

        with open(output, "w") as f:
            json.dump(creds_data, f, indent=2)
        logger.info(f"Credentials saved successfully to: {output}")

        click.echo("✓ OAuth flow completed successfully!")
        click.echo()
        click.echo(f"Credentials saved to: {output}")
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  export GOOGLE_GMAIL_TOOL_CREDENTIALS={output}")
        click.echo("  google-gmail-tool auth check")

    except Exception as e:
        logger.error(f"OAuth flow failed: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.debug("Full traceback:", exc_info=True)
        click.echo("✗ OAuth flow failed", err=True)
        click.echo()
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
