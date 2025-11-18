"""Drive file operation CLI commands (upload, rename, move, delete).

This module provides CLI commands for write operations on Google Drive files.
Follows the Agent-Friendly CLI Help pattern with inline examples for self-correction.

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
@click.argument("local_path", type=click.Path(exists=True))
@click.option(
    "--folder-id",
    "-d",
    default=None,
    help="Destination folder ID (default: My Drive root)",
)
@click.option(
    "--name",
    "-n",
    default=None,
    help="Name for the file in Drive (default: use local filename)",
)
@click.option(
    "--mime-type",
    "-m",
    default=None,
    help="MIME type of the file (default: auto-detect)",
)
@click.option(
    "--description",
    default=None,
    help="Description for the file",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite if file with same name exists",
)
@click.option(
    "--auto-approve",
    "-a",
    is_flag=True,
    help="Skip confirmation prompts",
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
def upload_file(
    local_path: str,
    folder_id: str | None,
    name: str | None,
    mime_type: str | None,
    description: str | None,
    force: bool,
    auto_approve: bool,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """Upload a file to Google Drive.

    Uploads a local file to Google Drive. By default, uploads to My Drive root.
    Checks for duplicate filenames and prompts for confirmation unless --force or
    --auto-approve is specified.

    \b
    Examples:

    \b
        # Upload file to My Drive root
        google-gmail-tool drive upload "/path/to/document.pdf"

    \b
        # Upload to specific folder
        google-gmail-tool drive upload "/path/to/report.pdf" \\
            --folder-id "1abc123xyz"

    \b
        # Upload with custom name
        google-gmail-tool drive upload "/tmp/file.pdf" \\
            --name "Monthly Report.pdf"

    \b
        # Upload with description
        google-gmail-tool drive upload "/path/to/doc.pdf" \\
            --description "Q4 2025 financial report"

    \b
        # Upload with custom MIME type
        google-gmail-tool drive upload "/path/to/data.bin" \\
            --mime-type "application/octet-stream"

    \b
        # Overwrite existing file (with force flag)
        google-gmail-tool drive upload "/path/to/updated.pdf" \\
            --force --auto-approve

    \b
        # Human-readable output
        google-gmail-tool drive upload "/path/to/file.pdf" --text

    \b
    Output Format (JSON):
        File object with metadata to stdout
        {
          "id": "1abc123xyz",
          "name": "document.pdf",
          "mimeType": "application/pdf",
          "size": "2621440",
          "webViewLink": "https://drive.google.com/file/d/...",
          ...
        }

    \b
    Exit Codes:
        0: Success
        1: Authentication or upload error
        2: File already exists (without --force) or operation cancelled
    """
    # Set up logging
    setup_logging(verbose)

    # Resolve format flag
    output_format = "text" if text else format

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Determine target filename
        import os

        target_name = name if name else os.path.basename(local_path)

        # Check for existing file
        logger.info(f"Checking if file '{target_name}' exists in target location")
        try:
            query_parts = [f"name='{target_name.replace("'", "\\'")}'", "trashed=false"]
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            else:
                query_parts.append("'root' in parents")

            check_query = " and ".join(query_parts)
            existing_files = client.list_files(query=check_query, max_results=1)

            if existing_files:
                existing_file = existing_files[0]
                if not force and not auto_approve:
                    click.echo(
                        f"⚠️  File '{target_name}' already exists (ID: {existing_file['id']})",
                        err=True,
                    )
                    if not click.confirm("Do you want to continue anyway?", err=True):
                        click.echo("❌ Upload cancelled", err=True)
                        sys.exit(2)
        except Exception as e:
            logger.warning(f"Could not check for existing files: {e}")

        # Upload file
        logger.info(f"Uploading file: {local_path}")
        click.echo(f"⬆️  Uploading {target_name}...", err=True)

        file = client.upload_file(
            local_path=local_path,
            folder_id=folder_id,
            name=name,
            mime_type=mime_type,
            description=description,
        )

        # Output results
        if output_format == "json":
            click.echo(json.dumps(file, indent=2))
        else:
            _print_file_success_text(file, "Uploaded")

        logger.info(f"Successfully uploaded file: {file['name']} (ID: {file['id']})")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        click.echo(f"❌ File not found: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Upload validation error: {e}")
        click.echo(f"❌ {e}", err=True)
        click.echo("\n💡 Use --force to overwrite existing files", err=True)
        sys.exit(2)
    except Exception as e:
        logger.error(f"Failed to upload file: {type(e).__name__}: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("file_id")
@click.argument("new_name")
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
def rename_file(
    file_id: str,
    new_name: str,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """Rename a file in Google Drive.

    Changes the name of an existing file. The file ID remains the same.

    \b
    Examples:

    \b
        # Rename a file
        google-gmail-tool drive rename "1abc123xyz" "New Document Name.pdf"

    \b
        # Rename with spaces in name
        google-gmail-tool drive rename "1abc123xyz" "Monthly Report - January.pdf"

    \b
        # Human-readable output
        google-gmail-tool drive rename "1abc123xyz" "Updated Name.pdf" --text

    \b
        # With debug logging
        google-gmail-tool drive rename "1abc123xyz" "New Name.pdf" -vv

    \b
    Output Format (JSON):
        Updated file object with metadata to stdout
        {
          "id": "1abc123xyz",
          "name": "New Document Name.pdf",
          "mimeType": "application/pdf",
          "modifiedTime": "2025-01-18T...",
          "webViewLink": "https://drive.google.com/file/d/...",
          ...
        }

    \b
    Exit Codes:
        0: Success
        1: Authentication or rename error
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

        # Rename file
        logger.info(f"Renaming file {file_id} to: {new_name}")
        click.echo("✏️  Renaming file...", err=True)

        file = client.rename_file(file_id, new_name)

        # Output results
        if output_format == "json":
            click.echo(json.dumps(file, indent=2))
        else:
            _print_file_success_text(file, "Renamed")

        logger.info(f"Successfully renamed file to: {file['name']}")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to rename file: {type(e).__name__}: {e}")
        if "404" in str(e) or "not found" in str(e).lower():
            click.echo(f"❌ File not found: {file_id}", err=True)
            sys.exit(2)
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("file_id")
@click.argument("destination_folder_id")
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
def move_file(
    file_id: str,
    destination_folder_id: str,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """Move a file to a different folder in Google Drive.

    Moves a file from its current location to a new folder. The file will be
    removed from all current parent folders and placed in the destination folder.

    \b
    Examples:

    \b
        # Move file to a folder
        google-gmail-tool drive move "1abc123xyz" "1folder456"

    \b
        # Move file to My Drive root
        google-gmail-tool drive move "1abc123xyz" "root"

    \b
        # Human-readable output
        google-gmail-tool drive move "1abc123xyz" "1folder456" --text

    \b
        # With debug logging
        google-gmail-tool drive move "1abc123xyz" "1folder456" -vv

    \b
    Output Format (JSON):
        Updated file object with metadata to stdout
        {
          "id": "1abc123xyz",
          "name": "document.pdf",
          "parents": ["1folder456"],
          "webViewLink": "https://drive.google.com/file/d/...",
          ...
        }

    \b
    Exit Codes:
        0: Success
        1: Authentication or move error
        2: File or folder not found
    """
    # Set up logging
    setup_logging(verbose)

    # Resolve format flag
    output_format = "text" if text else format

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Move file
        logger.info(f"Moving file {file_id} to folder: {destination_folder_id}")
        click.echo("📁 Moving file...", err=True)

        file = client.move_file(file_id, destination_folder_id)

        # Output results
        if output_format == "json":
            click.echo(json.dumps(file, indent=2))
        else:
            _print_file_success_text(file, "Moved")

        logger.info(f"Successfully moved file: {file['name']}")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to move file: {type(e).__name__}: {e}")
        if "404" in str(e) or "not found" in str(e).lower():
            click.echo(f"❌ File or folder not found: {file_id}, {destination_folder_id}", err=True)
            sys.exit(2)
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("file_id")
@click.option(
    "--permanent",
    is_flag=True,
    help="Permanently delete (irreversible). Default: move to trash",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.option(
    "--auto-approve",
    "-a",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG)",
)
def delete_file(
    file_id: str,
    permanent: bool,
    force: bool,
    auto_approve: bool,
    verbose: int,
) -> None:
    """Delete a file from Google Drive.

    By default, moves the file to trash (recoverable). Use --permanent to
    permanently delete the file (irreversible).

    \b
    Examples:

    \b
        # Move file to trash (recoverable)
        google-gmail-tool drive delete "1abc123xyz"

    \b
        # Permanently delete without confirmation
        google-gmail-tool drive delete "1abc123xyz" \\
            --permanent --force

    \b
        # Delete with auto-approve
        google-gmail-tool drive delete "1abc123xyz" --auto-approve

    \b
        # With debug logging
        google-gmail-tool drive delete "1abc123xyz" -vv

    \b
    Note:
        - Default behavior moves files to trash (recoverable via Drive web UI)
        - --permanent flag bypasses trash and deletes permanently (IRREVERSIBLE)
        - Confirmation prompt can be skipped with --force or --auto-approve

    \b
    Exit Codes:
        0: Success
        1: Authentication or delete error
        2: File not found or operation cancelled
    """
    # Set up logging
    setup_logging(verbose)

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Get file metadata for confirmation
        logger.info(f"Getting file metadata for: {file_id}")
        try:
            file = client.get_file(file_id)
            file_name = file.get("name", "unknown")
        except Exception as e:
            logger.warning(f"Could not get file metadata: {e}")
            file_name = "unknown"

        # Confirmation prompt
        action_word = "permanently delete" if permanent else "trash"
        if not force and not auto_approve:
            warning_emoji = "⚠️" if permanent else "🗑️"
            click.echo(
                f"{warning_emoji}  About to {action_word}: {file_name} (ID: {file_id})", err=True
            )
            if permanent:
                click.echo("⚠️  This action is IRREVERSIBLE!", err=True)

            if not click.confirm(f"Are you sure you want to {action_word} this file?", err=True):
                click.echo("❌ Delete cancelled", err=True)
                sys.exit(2)

        # Delete file
        logger.info(f"Deleting file {file_id} (permanent={permanent})")
        click.echo("🗑️  Deleting file...", err=True)

        client.delete_file(file_id, permanent=permanent)

        # Output success message
        if permanent:
            click.echo(f"✅ Permanently deleted: {file_name}", err=True)
        else:
            click.echo(f"✅ Moved to trash: {file_name}", err=True)
            click.echo("   (Recoverable from Drive trash)", err=True)

        logger.info(f"Successfully deleted file: {file_id}")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to delete file: {type(e).__name__}: {e}")
        if "404" in str(e) or "not found" in str(e).lower():
            click.echo(f"❌ File not found: {file_id}", err=True)
            sys.exit(2)
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def _print_file_success_text(file: dict[str, Any], action: str) -> None:
    """Print file success message in human-readable format."""
    click.echo(f"✅ {action}: {file.get('name', 'unknown')}")
    click.echo(f"   ID:          {file.get('id', 'N/A')}")
    click.echo(f"   MIME Type:   {file.get('mimeType', 'N/A')}")

    size = file.get("size", "")
    if size and size.isdigit():
        click.echo(f"   Size:        {_format_size(int(size))}")

    if file.get("webViewLink"):
        click.echo(f"   Link:        {file['webViewLink']}")

    if file.get("parents"):
        parents = ", ".join(file["parents"])
        click.echo(f"   Folder(s):   {parents}")


def _format_size(bytes_size: int) -> str:
    """Format file size in human-readable format."""
    size = float(bytes_size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
