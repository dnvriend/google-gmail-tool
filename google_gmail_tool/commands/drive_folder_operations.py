"""Drive folder operations CLI commands.

This module provides Click CLI commands for Google Drive folder operations including
creating, uploading, renaming, moving, and deleting folders. Follows the Agent-Friendly
CLI Help pattern with inline examples.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
import os
import sys

import click

from google_gmail_tool.core.auth import AuthenticationError, get_credentials
from google_gmail_tool.core.drive_client import DriveClient
from google_gmail_tool.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@click.command()
@click.argument("name")
@click.argument("parent_id", required=False)
@click.option(
    "--description",
    "-d",
    default=None,
    help="Description for the folder",
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
def create_folder(
    name: str,
    parent_id: str | None,
    description: str | None,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """Create a folder in Google Drive.

    Creates a new folder in Google Drive. If parent_id is not provided, the folder
    is created in My Drive root. Checks for duplicate folder names in the target location.

    \b
    Arguments:
        NAME        Name for the new folder (required)
        PARENT_ID   ID of parent folder (optional, default: My Drive root)

    \b
    Examples:

    \b
        # Create folder in My Drive root
        google-gmail-tool drive create-folder "Projects"

    \b
        # Create folder in specific location
        google-gmail-tool drive create-folder "2025" "1abc123xyz"

    \b
        # Create folder with description
        google-gmail-tool drive create-folder "Documents" \\
            --description "Important documents"

    \b
        # Create subfolder with full options
        google-gmail-tool drive create-folder "Reports" "1parent456" \\
            --description "Monthly reports" \\
            --text

    \b
    Output Format (JSON):
        {
          "id": "1newFolder789",
          "name": "Projects",
          "mimeType": "application/vnd.google-apps.folder",
          "createdTime": "2025-01-18T10:30:00.000Z",
          "webViewLink": "https://drive.google.com/drive/folders/1newFolder789"
        }

    \b
    Exit Codes:
        0: Success
        1: Authentication or API error
        2: Folder with same name already exists
    """
    # Set up logging
    setup_logging(verbose)

    # Resolve format flag
    output_format = "text" if text else format

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Create folder
        logger.info(f"Creating folder: {name} in parent: {parent_id or 'root'}")
        folder = client.create_folder(name, parent_id=parent_id, description=description)

        # Output results
        if output_format == "json":
            click.echo(json.dumps(folder, indent=2))
        else:
            click.echo(f"✅ Created folder: {folder['name']}", err=True)
            click.echo(f"   ID: {folder['id']}", err=True)
            click.echo(f"   Link: {folder.get('webViewLink', 'N/A')}", err=True)

        logger.info(f"Successfully created folder: {folder['name']} (ID: {folder['id']})")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        # Duplicate folder name
        logger.error(f"Folder already exists: {e}")
        click.echo(f"❌ {e}", err=True)
        sys.exit(2)
    except Exception as e:
        logger.error(f"Failed to create folder: {type(e).__name__}: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("local_path", type=click.Path(exists=True))
@click.argument("parent_id", required=False)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Upload folder contents recursively (default: True)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompts",
)
@click.option(
    "--auto-approve",
    "-a",
    is_flag=True,
    help="Automatically approve the upload",
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
def upload_folder(
    local_path: str,
    parent_id: str | None,
    recursive: bool,
    force: bool,
    auto_approve: bool,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """Upload a folder to Google Drive.

    Uploads a local folder to Google Drive. By default, uploads all contents recursively.
    Use --no-recursive to only create the folder without uploading files.

    \b
    Arguments:
        LOCAL_PATH  Path to local folder to upload (required)
        PARENT_ID   ID of parent folder in Drive (optional, default: My Drive root)

    \b
    Examples:

    \b
        # Upload folder to My Drive root
        google-gmail-tool drive upload-folder "/path/to/folder"

    \b
        # Upload to specific location
        google-gmail-tool drive upload-folder "/path/to/folder" "1parent456"

    \b
        # Upload without contents (folder only)
        google-gmail-tool drive upload-folder "/path/to/folder" --no-recursive

    \b
        # Upload with auto-approval
        google-gmail-tool drive upload-folder "/path/to/folder" \\
            --auto-approve \\
            --text

    \b
    Output Format (JSON):
        {
          "folder": {...},
          "uploaded_files": [...],
          "uploaded_folders": [...],
          "total_files": 15,
          "total_folders": 3,
          "total_bytes": 5242880
        }

    \b
    Exit Codes:
        0: Success
        1: Authentication or upload error
        2: Path not found or user cancelled
    """
    # Set up logging
    setup_logging(verbose)

    # Resolve format flag
    output_format = "text" if text else format

    try:
        # Validate path
        if not os.path.exists(local_path):
            click.echo(f"❌ Path not found: {local_path}", err=True)
            sys.exit(2)

        if not os.path.isdir(local_path):
            click.echo(f"❌ Path is not a directory: {local_path}", err=True)
            sys.exit(2)

        # Count files if recursive
        file_count = 0
        folder_count = 0
        if recursive:
            for dirpath, dirnames, filenames in os.walk(local_path):
                file_count += len(filenames)
                folder_count += len(dirnames) + 1  # +1 for root

        # Confirmation prompt
        if not (force or auto_approve):
            folder_name = os.path.basename(local_path)
            if recursive:
                click.echo(
                    f"⚠️  About to upload folder '{folder_name}' with "
                    f"{file_count} files and {folder_count} folders",
                    err=True,
                )
            else:
                click.echo(f"⚠️  About to create folder '{folder_name}' (no contents)", err=True)

            if not click.confirm("Continue?", err=True):
                click.echo("❌ Upload cancelled", err=True)
                sys.exit(2)

        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Upload folder
        logger.info(f"Uploading folder: {local_path} to parent: {parent_id or 'root'}")
        click.echo("⬆️  Uploading folder...", err=True)

        result = client.upload_folder(local_path, parent_id=parent_id, recursive=recursive)

        # Output results
        if output_format == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            folder = result["folder"]
            click.echo(f"✅ Uploaded folder: {folder['name']}", err=True)
            click.echo(f"   ID: {folder['id']}", err=True)
            click.echo(f"   Files: {result['total_files']}", err=True)
            click.echo(f"   Folders: {result['total_folders']}", err=True)
            click.echo(f"   Size: {_format_size(result['total_bytes'])}", err=True)
            click.echo(f"   Link: {folder.get('webViewLink', 'N/A')}", err=True)

        logger.info(
            f"Successfully uploaded folder: {result['folder']['name']} "
            f"({result['total_files']} files, {result['total_folders']} folders)"
        )
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Folder already exists: {e}")
        click.echo(f"❌ {e}", err=True)
        sys.exit(2)
    except Exception as e:
        logger.error(f"Failed to upload folder: {type(e).__name__}: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("folder_id")
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
def rename_folder(
    folder_id: str,
    new_name: str,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """Rename a folder in Google Drive.

    Renames an existing folder. Works the same as renaming files since folders
    are a special type of file in Drive.

    \b
    Arguments:
        FOLDER_ID   Drive folder ID (required)
        NEW_NAME    New name for the folder (required)

    \b
    Examples:

    \b
        # Rename folder
        google-gmail-tool drive rename-folder "1abc123xyz" "Projects 2025"

    \b
        # Rename with text output
        google-gmail-tool drive rename-folder "1folder456" "Archive" --text

    \b
    Output Format (JSON):
        {
          "id": "1abc123xyz",
          "name": "Projects 2025",
          "mimeType": "application/vnd.google-apps.folder",
          "modifiedTime": "2025-01-18T14:20:00.000Z",
          "parents": ["0AErQ..."]
        }

    \b
    Exit Codes:
        0: Success
        1: Authentication or API error
        2: Folder not found
    """
    # Set up logging
    setup_logging(verbose)

    # Resolve format flag
    output_format = "text" if text else format

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Rename folder
        logger.info(f"Renaming folder {folder_id} to: {new_name}")
        folder = client.rename_file(folder_id, new_name)

        # Output results
        if output_format == "json":
            click.echo(json.dumps(folder, indent=2))
        else:
            click.echo(f"✅ Renamed folder to: {folder['name']}", err=True)
            click.echo(f"   ID: {folder['id']}", err=True)

        logger.info(f"Successfully renamed folder to: {folder['name']}")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to rename folder: {type(e).__name__}: {e}")
        if "404" in str(e) or "not found" in str(e).lower():
            click.echo(f"❌ Folder not found: {folder_id}", err=True)
            sys.exit(2)
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("folder_id")
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
def move_folder(
    folder_id: str,
    destination_folder_id: str,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """Move a folder to a different parent folder.

    Moves a folder from its current location to a new parent folder. All contents
    of the folder are moved along with it.

    \b
    Arguments:
        FOLDER_ID               Folder to move (required)
        DESTINATION_FOLDER_ID   Destination parent folder (required)

    \b
    Examples:

    \b
        # Move folder to another folder
        google-gmail-tool drive move-folder "1abc123xyz" "1destination456"

    \b
        # Move with text output
        google-gmail-tool drive move-folder "1folder789" "1parent000" --text

    \b
    Output Format (JSON):
        {
          "id": "1abc123xyz",
          "name": "Projects",
          "mimeType": "application/vnd.google-apps.folder",
          "parents": ["1destination456"]
        }

    \b
    Exit Codes:
        0: Success
        1: Authentication or API error
        2: Folder not found
    """
    # Set up logging
    setup_logging(verbose)

    # Resolve format flag
    output_format = "text" if text else format

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Move folder
        logger.info(f"Moving folder {folder_id} to {destination_folder_id}")
        folder = client.move_file(folder_id, destination_folder_id)

        # Output results
        if output_format == "json":
            click.echo(json.dumps(folder, indent=2))
        else:
            click.echo(f"✅ Moved folder: {folder['name']}", err=True)
            click.echo(f"   ID: {folder['id']}", err=True)
            click.echo(f"   New parent: {destination_folder_id}", err=True)

        logger.info(f"Successfully moved folder: {folder['name']}")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to move folder: {type(e).__name__}: {e}")
        if "404" in str(e) or "not found" in str(e).lower():
            click.echo("❌ Folder or destination not found", err=True)
            sys.exit(2)
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("folder_id")
@click.option(
    "--permanent",
    is_flag=True,
    help="Permanently delete (cannot be recovered)",
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
    help="Automatically approve the deletion",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG)",
)
def delete_folder(
    folder_id: str,
    permanent: bool,
    force: bool,
    auto_approve: bool,
    verbose: int,
) -> None:
    """Delete a folder from Google Drive.

    By default, moves the folder to trash (recoverable). Use --permanent for
    irreversible deletion. WARNING: Deleting a folder deletes all its contents.

    \b
    Arguments:
        FOLDER_ID   Folder to delete (required)

    \b
    Examples:

    \b
        # Move folder to trash (recoverable)
        google-gmail-tool drive delete-folder "1abc123xyz"

    \b
        # Permanently delete folder
        google-gmail-tool drive delete-folder "1abc123xyz" --permanent

    \b
        # Delete without confirmation
        google-gmail-tool drive delete-folder "1folder456" --force

    \b
        # Permanent delete with auto-approval
        google-gmail-tool drive delete-folder "1old789" \\
            --permanent \\
            --auto-approve

    \b
    Exit Codes:
        0: Success
        1: Authentication or API error
        2: Folder not found or user cancelled
    """
    # Set up logging
    setup_logging(verbose)

    try:
        # Get credentials and initialize client
        credentials = get_credentials()
        client = DriveClient(credentials)

        # Get folder info for confirmation
        logger.info(f"Getting folder info: {folder_id}")
        folder = client.get_file(folder_id)
        folder_name = folder.get("name", "unknown")

        # Confirmation prompt
        if not (force or auto_approve):
            action = "permanently delete" if permanent else "move to trash"
            click.echo(
                f"⚠️  About to {action} folder '{folder_name}' (ID: {folder_id})",
                err=True,
            )
            click.echo("   WARNING: This will delete all contents of the folder!", err=True)

            if not click.confirm("Continue?", err=True):
                click.echo("❌ Deletion cancelled", err=True)
                sys.exit(2)

        # Delete folder
        logger.info(f"Deleting folder {folder_id} (permanent={permanent})")
        client.delete_file(folder_id, permanent=permanent)

        action = "Permanently deleted" if permanent else "Moved to trash"
        click.echo(f"✅ {action} folder: {folder_name}", err=True)

        logger.info(f"Successfully deleted folder: {folder_name} (ID: {folder_id})")
        sys.exit(0)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        click.echo(f"❌ Authentication error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to delete folder: {type(e).__name__}: {e}")
        if "404" in str(e) or "not found" in str(e).lower():
            click.echo(f"❌ Folder not found: {folder_id}", err=True)
            sys.exit(2)
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def _format_size(bytes_size: int) -> str:
    """Format file size in human-readable format."""
    size = float(bytes_size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
