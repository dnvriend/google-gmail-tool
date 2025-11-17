"""Task CLI commands for modification operations (create, update, delete, complete, uncomplete).

This module implements Click-based CLI commands for modifying Google Tasks.
Provides CRUD operations beyond read: create, update, delete, complete, and uncomplete.

Commands Implemented:
- create: Create new tasks with title, notes, and due date
- update: Update existing task fields (partial updates supported)
- complete: Mark one or more tasks as completed
- uncomplete: Mark one or more tasks as incomplete (reopen)
- delete: Delete tasks with optional confirmation

Key Features:
- Minimal required inputs: Only title required for create
- Partial updates: Only specify fields to change in update
- Batch operations: complete/uncomplete support multiple task IDs
- Confirmation prompts: delete command asks for confirmation (skip with --force)
- Date parsing: Handles YYYY-MM-DD format for due dates
- JSON output: All commands return structured JSON to stdout

Command Patterns:
- create: --title (required), --notes, --due (all optional except title)
- update: task_id (positional), --title, --notes, --due (all optional)
- complete/uncomplete: task_ids... (variadic positional arguments)
- delete: task_id (positional), --force (optional flag)

Error Handling:
- Exit code 0: Success
- Exit code 1: Authentication or API errors
- Exit code 2: Task not found, invalid parameters, or user cancellation
- Multi-task operations: Report failures per task, exit 2 if any fail

Validation:
- create: Due date format validation (YYYY-MM-DD)
- update: At least one field must be specified
- complete/uncomplete: At least one task ID required
- delete: Confirmation prompt shows task details unless --force

Design Philosophy:
- Composable: Commands designed for piping and scripting
- Safe by default: Confirmation prompts for destructive operations
- Clear feedback: JSON output includes operation status and affected IDs
- Fail fast: Input validation before API calls

Integration Points:
- Uses TaskClient from core.task_client for API operations
- Uses get_credentials from core.auth for OAuth2
- Uses setup_logging from logging_config for verbosity control
- Uses click.confirm for interactive prompts

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
import sys
from datetime import datetime

import click

from google_gmail_tool.core.auth import AuthenticationError, get_credentials
from google_gmail_tool.core.task_client import TaskClient
from google_gmail_tool.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@click.command()
@click.option("--title", "-t", required=True, help="Task title")
@click.option("--notes", "-n", help="Task notes/description")
@click.option("--due", "-d", help="Due date (YYYY-MM-DD)")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def create(title: str, notes: str | None, due: str | None, verbose: int) -> None:
    """Create a new task.

    Creates a task with specified title and optional notes and due date.
    Only title is required, all other fields are optional.

    \b
    Examples:

    \b
        # Create minimal task (only title)
        google-gmail-tool task create --title "Review PR #123"

    \b
        # Create task with due date
        google-gmail-tool task create \\
            --title "Review PR #123" \\
            --due "2025-11-20"

    \b
        # Create task with notes and due date
        google-gmail-tool task create \\
            --title "Review PR #123" \\
            --notes "Check code quality and tests" \\
            --due "2025-11-20"

    \b
        # Short form
        google-gmail-tool task create -t "Team meeting" -d "2025-11-20"

    \b
    Output Format (JSON):
        Returns created task object with:
        - id, title, notes
        - due, status, completed
        - updated

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Invalid parameters
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting task create command")

    # Parse due date
    due_dt = None
    if due:
        try:
            due_dt = datetime.strptime(due, "%Y-%m-%d")
        except ValueError as e:
            click.echo(f"Error: Invalid due date format: {e}", err=True)
            click.echo("Expected: YYYY-MM-DD", err=True)
            sys.exit(2)

    # Load credentials
    try:
        logger.info("Loading Google credentials")
        credentials = get_credentials()
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Task client
    try:
        logger.info("Initializing Tasks API client")
        client = TaskClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Task client: {type(e).__name__}")
        click.echo(f"Error initializing Tasks API: {e}", err=True)
        sys.exit(1)

    # Create task
    try:
        task = client.create_task(title=title, notes=notes, due=due_dt)

        logger.info(f"Task created: {task['id']}")
        click.echo(json.dumps(task, indent=2))

    except Exception as e:
        logger.error(f"Failed to create task: {type(e).__name__}: {e}")
        logger.debug("Full traceback:", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("task_id")
@click.option("--title", "-t", help="New task title")
@click.option("--notes", "-n", help="New task notes")
@click.option("--due", "-d", help="New due date (YYYY-MM-DD)")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def update(
    task_id: str, title: str | None, notes: str | None, due: str | None, verbose: int
) -> None:
    """Update an existing task.

    Updates specified fields of an existing task. Only provided fields are updated.
    Use 'task list' or 'task get' to find task IDs.

    \b
    Examples:

    \b
        # Update task title
        google-gmail-tool task update abc123xyz --title "New Task Title"

    \b
        # Update task due date
        google-gmail-tool task update abc123xyz --due "2025-11-21"

    \b
        # Update multiple fields
        google-gmail-tool task update abc123xyz \\
            --title "Updated Task" \\
            --notes "New notes" \\
            --due "2025-11-21"

    \b
        # Combine with list to update first incomplete task
        TASK_ID=$(google-gmail-tool task list --incomplete -n 1 | jq -r '.[0].id')
        google-gmail-tool task update "$TASK_ID" --title "Updated Title"

    \b
    Output Format (JSON):
        Returns updated task object with all fields

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Task not found or invalid parameters
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting task update command")

    # Validate at least one field is provided
    if not any([title, notes, due]):
        click.echo("Error: Must specify at least one field to update", err=True)
        click.echo("Use --title, --notes, or --due", err=True)
        sys.exit(2)

    # Parse due date
    due_dt = None
    if due:
        try:
            due_dt = datetime.strptime(due, "%Y-%m-%d")
        except ValueError as e:
            click.echo(f"Error: Invalid due date format: {e}", err=True)
            click.echo("Expected: YYYY-MM-DD", err=True)
            sys.exit(2)

    # Load credentials
    try:
        logger.info("Loading Google credentials")
        credentials = get_credentials()
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Task client
    try:
        logger.info("Initializing Tasks API client")
        client = TaskClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Task client: {type(e).__name__}")
        click.echo(f"Error initializing Tasks API: {e}", err=True)
        sys.exit(1)

    # Update task
    try:
        task = client.update_task(task_id=task_id, title=title, notes=notes, due=due_dt)

        logger.info(f"Task updated: {task_id}")
        click.echo(json.dumps(task, indent=2))

    except Exception as e:
        logger.error(f"Failed to update task: {type(e).__name__}: {e}")
        logger.debug("Full traceback:", exc_info=True)

        # Check if it's a 404 not found error
        error_str = str(e)
        if "404" in error_str or "not found" in error_str.lower():
            click.echo(f"Error: Task not found: {task_id}", err=True)
            sys.exit(2)
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@click.command()
@click.argument("task_ids", nargs=-1, required=True)
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def complete(task_ids: tuple[str, ...], verbose: int) -> None:
    """Mark task(s) as completed.

    Marks one or more tasks as completed by task ID.
    Use 'task list' to find task IDs.

    \b
    Examples:

    \b
        # Complete single task
        google-gmail-tool task complete abc123xyz

    \b
        # Complete multiple tasks
        google-gmail-tool task complete abc123 def456 ghi789

    \b
        # Combine with list to complete first incomplete task
        TASK_ID=$(google-gmail-tool task list --incomplete -n 1 | jq -r '.[0].id')
        google-gmail-tool task complete "$TASK_ID"

    \b
    Output Format (JSON):
        Returns array of completed task objects

    \b
    Exit Codes:
        0    Success (all tasks completed)
        1    Authentication failed or API error
        2    Task not found
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting task complete command")

    # Load credentials
    try:
        logger.info("Loading Google credentials")
        credentials = get_credentials()
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Task client
    try:
        logger.info("Initializing Tasks API client")
        client = TaskClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Task client: {type(e).__name__}")
        click.echo(f"Error initializing Tasks API: {e}", err=True)
        sys.exit(1)

    # Complete tasks
    completed_tasks = []
    failed_count = 0

    for task_id in task_ids:
        try:
            task = client.complete_task(task_id)
            logger.info(f"Task completed: {task_id}")
            completed_tasks.append(task)

        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {type(e).__name__}: {e}")
            logger.debug("Full traceback:", exc_info=True)

            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                click.echo(f"Error: Task not found: {task_id}", err=True)
            else:
                click.echo(f"Error completing {task_id}: {e}", err=True)

            failed_count += 1

    # Output results
    click.echo(json.dumps(completed_tasks, indent=2))

    if failed_count > 0:
        logger.error(f"{failed_count} task(s) failed to complete")
        sys.exit(2)


@click.command()
@click.argument("task_ids", nargs=-1, required=True)
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def uncomplete(task_ids: tuple[str, ...], verbose: int) -> None:
    """Mark task(s) as incomplete.

    Marks one or more tasks as incomplete by task ID.
    Use 'task list --completed' to find completed task IDs.

    \b
    Examples:

    \b
        # Uncomplete single task
        google-gmail-tool task uncomplete abc123xyz

    \b
        # Uncomplete multiple tasks
        google-gmail-tool task uncomplete abc123 def456 ghi789

    \b
        # Combine with list to uncomplete first completed task
        TASK_ID=$(google-gmail-tool task list --completed -n 1 | jq -r '.[0].id')
        google-gmail-tool task uncomplete "$TASK_ID"

    \b
    Output Format (JSON):
        Returns array of uncompleted task objects

    \b
    Exit Codes:
        0    Success (all tasks uncompleted)
        1    Authentication failed or API error
        2    Task not found
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting task uncomplete command")

    # Load credentials
    try:
        logger.info("Loading Google credentials")
        credentials = get_credentials()
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Task client
    try:
        logger.info("Initializing Tasks API client")
        client = TaskClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Task client: {type(e).__name__}")
        click.echo(f"Error initializing Tasks API: {e}", err=True)
        sys.exit(1)

    # Uncomplete tasks
    uncompleted_tasks = []
    failed_count = 0

    for task_id in task_ids:
        try:
            task = client.uncomplete_task(task_id)
            logger.info(f"Task marked incomplete: {task_id}")
            uncompleted_tasks.append(task)

        except Exception as e:
            logger.error(f"Failed to uncomplete task {task_id}: {type(e).__name__}: {e}")
            logger.debug("Full traceback:", exc_info=True)

            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                click.echo(f"Error: Task not found: {task_id}", err=True)
            else:
                click.echo(f"Error uncompleting {task_id}: {e}", err=True)

            failed_count += 1

    # Output results
    click.echo(json.dumps(uncompleted_tasks, indent=2))

    if failed_count > 0:
        logger.error(f"{failed_count} task(s) failed to uncomplete")
        sys.exit(2)


@click.command()
@click.argument("task_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def delete(task_id: str, force: bool, verbose: int) -> None:
    """Delete a task.

    Permanently deletes a task by ID.
    Use 'task list' or 'task get' to find task IDs.

    \b
    Examples:

    \b
        # Delete task with confirmation
        google-gmail-tool task delete abc123xyz

    \b
        # Delete without confirmation (force)
        google-gmail-tool task delete abc123xyz --force

    \b
        # Combine with list to delete first completed task
        TASK_ID=$(google-gmail-tool task list --completed -n 1 | jq -r '.[0].id')
        google-gmail-tool task delete "$TASK_ID" --force

    \b
        # Get task details before deleting
        google-gmail-tool task get abc123xyz --format text
        google-gmail-tool task delete abc123xyz

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Task not found or deletion cancelled
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting task delete command")

    # Load credentials
    try:
        logger.info("Loading Google credentials")
        credentials = get_credentials()
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Task client
    try:
        logger.info("Initializing Tasks API client")
        client = TaskClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Task client: {type(e).__name__}")
        click.echo(f"Error initializing Tasks API: {e}", err=True)
        sys.exit(1)

    # Fetch task details for confirmation
    if not force:
        try:
            task = client.get_task(task_id)
            click.echo(f"Task: {task['title']}", err=True)
            if task.get("due"):
                click.echo(f"Due:  {task['due']}", err=True)
            if not click.confirm("\nAre you sure you want to delete this task?", err=True):
                click.echo("Deletion cancelled.", err=True)
                sys.exit(2)
        except Exception as e:
            logger.error(f"Failed to fetch task: {type(e).__name__}: {e}")
            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                click.echo(f"Error: Task not found: {task_id}", err=True)
                sys.exit(2)
            else:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

    # Delete task
    try:
        client.delete_task(task_id)
        logger.info(f"Task deleted: {task_id}")
        click.echo(json.dumps({"status": "deleted", "task_id": task_id}, indent=2))

    except Exception as e:
        logger.error(f"Failed to delete task: {type(e).__name__}: {e}")
        logger.debug("Full traceback:", exc_info=True)

        # Check if it's a 404 not found error
        error_str = str(e)
        if "404" in error_str or "not found" in error_str.lower():
            click.echo(f"Error: Task not found: {task_id}", err=True)
            sys.exit(2)
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
