"""Drive CLI commands.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
import sys
from typing import Any

import click

from google_gmail_tool.core.auth import AuthenticationError, get_credentials
from google_gmail_tool.core.drive_client import DriveClient
from google_gmail_tool.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@click.command()
@click.option(
    "--query",
    "-q",
    default=None,
    help="Drive API query (e.g., \"mimeType='application/pdf'\")",
)
@click.option(
    "--max-results",
    "-n",
    type=int,
    default=100,
    help="Maximum number of results (default: 100, max: 1000)",
)
@click.option(
    "--folder",
    "-f",
    default=None,
    help="List files only in this folder (provide folder ID)",
)
@click.option(
    "--order-by",
    default="modifiedTime desc",
    help="Sort order (default: modifiedTime desc, options: name, createdTime, modifiedTime)",
)
@click.option(
    "--format",
    type=click.Choice(["json", "text"], case_sensitive=False),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--text",
    is_flag=True,
    help="Output in text format (shorthand for --format text)",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG)",
)
def list_cmd(
    query: str | None,
    max_results: int,
    folder: str | None,
    order_by: str,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """List files in Google Drive with optional filtering.

    Lists files from your Google Drive with support for queries, folder filtering,
    and sorting. Outputs JSON by default for agent-friendly consumption.

    \b
    Drive Query Syntax:
        name contains 'keyword'              Search by name
        mimeType='application/pdf'           Filter by MIME type
        modifiedTime > '2025-01-01'         Modified after date
        'parent_folder_id' in parents       Files in specific folder
        sharedWithMe=true                    Files shared with you
        trashed=false                        Exclude trashed files

    \b
    Common MIME Types:
        application/pdf                      PDF documents
        image/jpeg, image/png                Images
        text/plain                           Text files
        application/vnd.google-apps.document Google Docs
        application/vnd.google-apps.spreadsheet Google Sheets
        application/vnd.google-apps.folder   Folders

    \b
    Examples:

    \b
        # List 100 most recently modified files (default)
        google-gmail-tool drive list

    \b
        # List files in a specific folder
        google-gmail-tool drive list --folder "1abc123xyz"

    \b
        # Search for PDF files
        google-gmail-tool drive list --query "mimeType='application/pdf'" -n 50

    \b
        # Search by name
        google-gmail-tool drive list --query "name contains 'report'" -n 20

    \b
        # List files shared with me
        google-gmail-tool drive list --query "sharedWithMe=true"

    \b
        # Sort by name
        google-gmail-tool drive list --order-by "name" -n 50

    \b
        # Human-readable output
        google-gmail-tool drive list --text -n 20

    \b
        # Complex query
        google-gmail-tool drive list \\
            --query "name contains 'invoice' and mimeType='application/pdf'"

    \b
    Output Format (JSON):
        Array of file objects to stdout
        Logs to stderr (use -v, -vv for verbosity)

    \b
    Output Format (Text):
        Human-readable table format
        ID              NAME              TYPE                  SIZE      MODIFIED
        1abc123...      report.pdf        application/pdf       2.5 MB    2025-01-15

    \b
    Exit Codes:
        0: Success
        1: Authentication or API error
    """
    # Set up logging
    setup_logging(verbose)

    # Resolve format flag
    output_format = "text" if text else format

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # List files
        logger.info(f"Listing Drive files with max_results={max_results}")
        files = client.list_files(
            query=query,
            max_results=max_results,
            folder_id=folder,
            order_by=order_by,
        )

        # Output results
        if output_format == "json":
            click.echo(json.dumps(files, indent=2))
        else:
            _print_files_text(files)

        logger.info(f"Successfully listed {len(files)} files")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to list files: {type(e).__name__}: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("file_id")
@click.option(
    "--format",
    type=click.Choice(["json", "text"], case_sensitive=False),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--text",
    is_flag=True,
    help="Output in text format (shorthand for --format text)",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG)",
)
def get(file_id: str, format: str, text: bool, verbose: int) -> None:
    """Get metadata for a specific Drive file.

    Retrieves detailed metadata for a file including name, type, size, creation date,
    modification date, owners, permissions, and sharing status.

    \b
    Examples:

    \b
        # Get file metadata (JSON)
        google-gmail-tool drive get "1abc123xyz"

    \b
        # Human-readable format
        google-gmail-tool drive get "1abc123xyz" --text

    \b
        # With debug logging
        google-gmail-tool drive get "1abc123xyz" -vv

    \b
    Output Format (JSON):
        File object with full metadata to stdout
        {
          "id": "1abc123xyz",
          "name": "report.pdf",
          "mimeType": "application/pdf",
          "size": "2621440",
          "createdTime": "2025-01-15T10:30:00.000Z",
          "modifiedTime": "2025-01-15T14:20:00.000Z",
          ...
        }

    \b
    Exit Codes:
        0: Success
        1: Authentication or API error
        2: File not found
    """
    # Set up logging
    setup_logging(verbose)

    # Resolve format flag
    output_format = "text" if text else format

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Get file metadata
        logger.info(f"Getting metadata for file: {file_id}")
        file = client.get_file(file_id)

        # Output results
        if output_format == "json":
            click.echo(json.dumps(file, indent=2))
        else:
            _print_file_details_text(file)

        logger.info(f"Successfully retrieved metadata for: {file.get('name')}")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to get file: {type(e).__name__}: {e}")
        if "404" in str(e) or "not found" in str(e).lower():
            click.echo(f"❌ File not found: {file_id}", err=True)
            sys.exit(2)
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("file_id")
@click.argument("output_path", type=click.Path())
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG)",
)
def download(file_id: str, output_path: str, verbose: int) -> None:
    """Download a file from Google Drive.

    Downloads a file by ID to the specified local path. Supports binary files only.
    For Google Workspace files (Docs, Sheets, etc.), they must be exported first.

    \b
    Examples:

    \b
        # Download a file
        google-gmail-tool drive download "1abc123xyz" "/tmp/report.pdf"

    \b
        # Download to current directory
        google-gmail-tool drive download "1abc123xyz" "./document.pdf"

    \b
        # With progress logging
        google-gmail-tool drive download "1abc123xyz" "/tmp/file.zip" -vv

    \b
    Note:
        Google Workspace files (Docs, Sheets, Slides) cannot be downloaded directly.
        You will receive an error with instructions to use export functionality.

    \b
    Exit Codes:
        0: Success
        1: Authentication or download error
        2: File not found or unsupported file type
    """
    # Set up logging
    setup_logging(verbose)

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Download file
        logger.info(f"Downloading file {file_id} to {output_path}")
        click.echo(f"⬇️  Downloading file...", err=True)

        bytes_downloaded = client.download_file(file_id, output_path)

        # Format size
        size_str = _format_size(bytes_downloaded)
        click.echo(f"✅ Downloaded {size_str} to: {output_path}", err=True)

        logger.info(f"Successfully downloaded {bytes_downloaded} bytes")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        # Google Workspace file type error
        logger.error(f"Unsupported file type: {e}")
        click.echo(f"❌ {e}", err=True)
        sys.exit(2)
    except Exception as e:
        logger.error(f"Failed to download file: {type(e).__name__}: {e}")
        if "404" in str(e) or "not found" in str(e).lower():
            click.echo(f"❌ File not found: {file_id}", err=True)
            sys.exit(2)
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option(
    "--name",
    "-n",
    default=None,
    help="Search for files with name containing this text",
)
@click.option(
    "--mime-type",
    "-m",
    default=None,
    help="Filter by MIME type (e.g., 'application/pdf', 'image/jpeg')",
)
@click.option(
    "--folder",
    "-f",
    default=None,
    help="Search only within this folder (provide folder ID)",
)
@click.option(
    "--shared-with-me",
    is_flag=True,
    help="Only show files shared with me",
)
@click.option(
    "--max-results",
    type=int,
    default=50,
    help="Maximum number of results (default: 50)",
)
@click.option(
    "--format",
    type=click.Choice(["json", "text"], case_sensitive=False),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--text",
    is_flag=True,
    help="Output in text format (shorthand for --format text)",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG)",
)
def search(
    name: str | None,
    mime_type: str | None,
    folder: str | None,
    shared_with_me: bool,
    max_results: int,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """Search for files in Google Drive with common filters.

    Simplified search interface with common filter options. For advanced queries,
    use 'drive list --query' instead.

    \b
    Examples:

    \b
        # Search by name
        google-gmail-tool drive search --name "report"

    \b
        # Search for PDFs
        google-gmail-tool drive search --mime-type "application/pdf" -n 100

    \b
        # Search for images
        google-gmail-tool drive search --mime-type "image/jpeg"

    \b
        # Search files shared with me
        google-gmail-tool drive search --shared-with-me

    \b
        # Combine filters
        google-gmail-tool drive search \\
            --name "invoice" \\
            --mime-type "application/pdf" \\
            --folder "1abc123xyz"

    \b
        # Human-readable output
        google-gmail-tool drive search --name "budget" --text

    \b
    Common MIME Types:
        application/pdf                      PDF documents
        image/jpeg, image/png                Images
        text/plain                           Text files
        application/zip                      ZIP archives
        video/mp4                            Videos

    \b
    Exit Codes:
        0: Success
        1: Authentication or search error
    """
    # Set up logging
    setup_logging(verbose)

    # Resolve format flag
    output_format = "text" if text else format

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Search files
        logger.info(
            f"Searching files: name={name}, mime_type={mime_type}, "
            f"folder={folder}, shared_with_me={shared_with_me}"
        )

        files = client.search_files(
            name_contains=name,
            mime_type=mime_type,
            folder_id=folder,
            shared_with_me=shared_with_me,
            max_results=max_results,
        )

        # Output results
        if output_format == "json":
            click.echo(json.dumps(files, indent=2))
        else:
            _print_files_text(files)

        logger.info(f"Search found {len(files)} files")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Search failed: {type(e).__name__}: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def _print_files_text(files: list[dict[str, Any]]) -> None:
    """Print files in human-readable table format."""
    if not files:
        click.echo("No files found.")
        return

    # Print header
    click.echo(
        f"{'ID':<35} {'NAME':<40} {'TYPE':<30} {'SIZE':<10} {'MODIFIED':<20}"
    )
    click.echo("-" * 135)

    # Print files
    for file in files:
        file_id = file.get("id", "")
        name = file.get("name", "")[:38]
        mime_type = file.get("mimeType", "")[:28]
        size = file.get("size", "")
        modified = file.get("modifiedTime", "")[:19]

        size_str = _format_size(int(size)) if size.isdigit() else "-"

        click.echo(f"{file_id:<35} {name:<40} {mime_type:<30} {size_str:<10} {modified:<20}")


def _print_file_details_text(file: dict[str, Any]) -> None:
    """Print file details in human-readable format."""
    click.echo(f"📄 File Details:")
    click.echo(f"")
    click.echo(f"  Name:         {file.get('name', 'N/A')}")
    click.echo(f"  ID:           {file.get('id', 'N/A')}")
    click.echo(f"  MIME Type:    {file.get('mimeType', 'N/A')}")

    size = file.get("size", "")
    if size and size.isdigit():
        click.echo(f"  Size:         {_format_size(int(size))}")

    click.echo(f"  Created:      {file.get('createdTime', 'N/A')}")
    click.echo(f"  Modified:     {file.get('modifiedTime', 'N/A')}")
    click.echo(f"  Shared:       {file.get('shared', False)}")
    click.echo(f"  Trashed:      {file.get('trashed', False)}")

    if file.get("webViewLink"):
        click.echo(f"  Web Link:     {file['webViewLink']}")

    if file.get("owners"):
        owners = ", ".join([o.get("displayName", "Unknown") for o in file["owners"]])
        click.echo(f"  Owners:       {owners}")


def _format_size(bytes_size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"
