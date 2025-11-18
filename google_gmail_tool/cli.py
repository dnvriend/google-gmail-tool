"""CLI entry point for google-gmail-tool.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import click

from google_gmail_tool.commands import (
    auth_commands,
    calendar_commands,
    calendar_create_update_delete,
    completion_commands,
    drive_commands,
    drive_file_operations,
    drive_folder_operations,
    mail_commands,
    skill_commands,
    task_commands,
    task_create_update_delete,
)


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """A CLI that provides access to Google services like Gmail, Calendar, Tasks, and Drive.

    \b
    This tool provides access to your Google data with commands for:
        - Authentication verification and OAuth flow (auth)
        - Gmail operations - list, send, get, export to Obsidian (mail)
        - Calendar operations - list, create, update, delete, export to Obsidian (calendar)
        - Task operations - list, create, update, complete, delete, export to Obsidian (task)
        - Drive operations - list, search, upload, download, create, rename, move, delete (drive)
        - Skill commands - cross-tool discovery and semantic search (skill)

    \b
    Quick Start:
        # 1. Set up OAuth credentials
        export GOOGLE_GMAIL_TOOL_CREDENTIALS=~/.config/google-gmail-tool/credentials.json

        # 2. Verify authentication
        google-gmail-tool auth check

    \b
    Getting OAuth Credentials:
        Visit https://console.cloud.google.com/apis/credentials
        Create OAuth 2.0 Client ID (Desktop application)
        Download JSON and set GOOGLE_GMAIL_TOOL_CREDENTIALS
    """
    pass


@main.group()
def auth() -> None:
    """Verify Google OAuth credentials and API access.

    Commands for testing authentication and checking API permissions.
    """
    pass


# Register auth commands
auth.add_command(auth_commands.check)
auth.add_command(auth_commands.login)


@main.group()
def mail() -> None:
    """Gmail operations (read-only).

    Commands for listing and retrieving Gmail threads and messages.
    """
    pass


# Register mail commands
mail.add_command(mail_commands.list_cmd, name="list")
mail.add_command(mail_commands.send, name="send")
mail.add_command(mail_commands.get, name="get")
mail.add_command(mail_commands.export_obsidian, name="export-obsidian")


@main.group()
def calendar() -> None:
    """Calendar operations.

    Commands for viewing and exporting Google Calendar events.
    """
    pass


# Register calendar commands
calendar.add_command(calendar_commands.list_cmd, name="list")
calendar.add_command(calendar_commands.get, name="get")
calendar.add_command(calendar_create_update_delete.create, name="create")
calendar.add_command(calendar_create_update_delete.update, name="update")
calendar.add_command(calendar_create_update_delete.delete, name="delete")
calendar.add_command(calendar_commands.export_obsidian, name="export-obsidian")


@main.group()
def task() -> None:
    """Task operations (Google Tasks).

    Commands for managing tasks, to-do items, and task lists.
    """
    pass


# Register task commands
task.add_command(task_commands.list_cmd, name="list")
task.add_command(task_commands.get, name="get")
task.add_command(task_create_update_delete.create, name="create")
task.add_command(task_create_update_delete.update, name="update")
task.add_command(task_create_update_delete.complete, name="complete")
task.add_command(task_create_update_delete.uncomplete, name="uncomplete")
task.add_command(task_create_update_delete.delete, name="delete")
task.add_command(task_commands.export_obsidian, name="export-obsidian")


@main.group()
def drive() -> None:
    """Drive operations.

    \b
    Commands for managing files and folders in Google Drive:
        - Read operations: list, search, get, download
        - File operations: upload-file, rename-file, move-file, delete-file
        - Folder operations: create-folder, upload-folder, rename-folder, move-folder, delete-folder
    """
    pass


# Register drive read commands
drive.add_command(drive_commands.list_cmd, name="list")
drive.add_command(drive_commands.get, name="get")
drive.add_command(drive_commands.download, name="download")
drive.add_command(drive_commands.search, name="search")

# Register drive file operation commands
drive.add_command(drive_file_operations.upload_file, name="upload-file")
drive.add_command(drive_file_operations.rename_file, name="rename-file")
drive.add_command(drive_file_operations.move_file, name="move-file")
drive.add_command(drive_file_operations.delete_file, name="delete-file")

# Register drive folder operation commands
drive.add_command(drive_folder_operations.create_folder, name="create-folder")
drive.add_command(drive_folder_operations.upload_folder, name="upload-folder")
drive.add_command(drive_folder_operations.rename_folder, name="rename-folder")
drive.add_command(drive_folder_operations.move_folder, name="move-folder")
drive.add_command(drive_folder_operations.delete_folder, name="delete-folder")


# Register completion command (top-level command)
main.add_command(completion_commands.completion)

# Register skill command group (top-level command group)
main.add_command(skill_commands.skill)


if __name__ == "__main__":
    main()
