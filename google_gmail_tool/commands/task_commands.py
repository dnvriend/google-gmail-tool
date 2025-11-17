"""Task CLI commands for Google Tasks API operations (list, get).

This module implements Click-based CLI commands for viewing and querying Google Tasks.
Provides list_cmd for filtered task listings and get for individual task retrieval.

Commands Implemented:
- list_cmd: List tasks with filtering by status, due date, and keyword search
- get: Retrieve single task details by ID

Key Features:
- Status filtering: --completed, --incomplete, --all (default: incomplete)
- Time range filtering: --today, --overdue, --this-week
- Keyword search: --query (searches title and notes)
- Output formats: JSON (default) or text table (--text flag)
- Agent-friendly: JSON to stdout, logs to stderr
- Self-documenting: Comprehensive --help with inline examples

Filtering Logic:
- Status filters are mutually exclusive (only one allowed)
- Time range filters are mutually exclusive (only one allowed)
- Query filter can be combined with status and time filters
- Default behavior: incomplete tasks, no time limit

Output Formats:
- JSON: Machine-readable, structured for piping (stdout)
- Text: Human-readable table with status, due date, and title

Error Handling:
- Exit code 0: Success
- Exit code 1: Authentication or API errors
- Exit code 2: Task not found (get command only)
- Clear error messages with actionable guidance

Integration Points:
- Uses TaskClient from core.task_client for API operations
- Uses get_credentials from core.auth for OAuth2
- Uses setup_logging from logging_config for verbosity control

Design Pattern:
- Command functions are thin wrappers around TaskClient
- CLI layer handles all formatting, error messages, and user interaction
- Core layer (TaskClient) is CLI-independent and importable

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any

import click

from google_gmail_tool.core.auth import AuthenticationError, get_credentials
from google_gmail_tool.core.task_client import TaskClient
from google_gmail_tool.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@click.command()
@click.option("--completed", is_flag=True, help="Show only completed tasks")
@click.option("--incomplete", is_flag=True, help="Show only incomplete tasks")
@click.option("--all", "show_all", is_flag=True, help="Show all tasks (completed and incomplete)")
@click.option("--today", is_flag=True, help="Tasks due today")
@click.option("--overdue", is_flag=True, help="Tasks past due date")
@click.option("--this-week", is_flag=True, help="Tasks due this week")
@click.option("--query", "-q", help="Search tasks by keyword in title/notes")
@click.option(
    "--max-results", "-n", type=int, default=100, help="Maximum number of results (default: 100)"
)
@click.option(
    "--format", "-f", type=click.Choice(["json", "text"]), default="json", help="Output format"
)
@click.option("--text", is_flag=True, help="Output in text format (shorthand for --format text)")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def list_cmd(
    completed: bool,
    incomplete: bool,
    show_all: bool,
    today: bool,
    overdue: bool,
    this_week: bool,
    query: str | None,
    max_results: int,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """List tasks with optional filtering.

    By default, lists incomplete tasks only in JSON format.
    Use status and time range flags to filter tasks.

    \b
    Examples:

    \b
        # List all incomplete tasks (default)
        google-gmail-tool task list

    \b
        # List completed tasks
        google-gmail-tool task list --completed

    \b
        # List all tasks
        google-gmail-tool task list --all

    \b
        # List tasks due today
        google-gmail-tool task list --today

    \b
        # List overdue tasks
        google-gmail-tool task list --overdue

    \b
        # List tasks due this week
        google-gmail-tool task list --this-week

    \b
        # Search for tasks containing keyword
        google-gmail-tool task list --query "project"

    \b
        # Combine filters (incomplete tasks due this week with "meeting")
        google-gmail-tool task list --incomplete --this-week --query "meeting"

    \b
        # Human-readable text output
        google-gmail-tool task list --text

    \b
    Output Format (JSON):
        Outputs array of task objects to stdout
        Logs to stderr (use -v, -vv for verbosity)

    \b
    Output Format (Text):
        Human-readable table format
        STATUS  DUE DATE    TASK TITLE
        [ ]     2025-11-20  Review PR #123
        [x]     2025-11-19  Update documentation

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting task list command")

    # Handle --text flag
    if text:
        format = "text"

    # Validate status flags
    status_flags = sum([completed, incomplete, show_all])
    if status_flags > 1:
        click.echo("Error: Only one status flag can be specified", err=True)
        sys.exit(1)

    # Validate time range flags
    time_flags = sum([today, overdue, this_week])
    if time_flags > 1:
        click.echo("Error: Only one time range flag can be specified", err=True)
        sys.exit(1)

    # Determine completion filter
    completed_filter: bool | None = None
    if completed:
        completed_filter = True
    elif incomplete:
        completed_filter = False
    elif not show_all:
        # Default: incomplete only
        completed_filter = False

    # Determine time range
    due_min: datetime | None = None
    due_max: datetime | None = None
    now = datetime.utcnow()

    if today:
        due_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
        due_max = due_min + timedelta(days=1)
        logger.debug(f"Time range: today ({due_min} to {due_max})")
    elif overdue:
        due_max = now.replace(hour=0, minute=0, second=0, microsecond=0)
        logger.debug(f"Time range: overdue (before {due_max})")
    elif this_week:
        # Monday to Sunday of current week
        weekday = now.weekday()
        monday = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
        due_min = monday
        due_max = monday + timedelta(days=7)
        logger.debug(f"Time range: this week ({due_min} to {due_max})")

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

    # List tasks
    try:
        tasks = client.list_tasks(
            completed=completed_filter,
            due_min=due_min,
            due_max=due_max,
            query=query,
            max_results=max_results,
        )

        logger.info(f"Retrieved {len(tasks)} tasks")

        # Output results
        if format == "json":
            click.echo(json.dumps(tasks, indent=2))
        else:
            _output_text_table(tasks)

        logger.info("Task list completed successfully")

    except Exception as e:
        logger.error(f"Failed to list tasks: {type(e).__name__}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _output_text_table(tasks: list[dict[str, Any]]) -> None:
    """Output tasks as human-readable text table.

    Args:
        tasks: List of task dictionaries
    """
    if not tasks:
        click.echo("No tasks found.")
        return

    # Table header
    header = f"{'STATUS':<8} {'DUE DATE':<12} {'TASK TITLE':<50}"
    click.echo(header)
    click.echo("=" * len(header))

    # Table rows
    for task in tasks:
        # Status
        status = task.get("status", "needsAction")
        status_mark = "[x]" if status == "completed" else "[ ]"

        # Due date
        due = task.get("due", "")
        due_str = due[:10] if due else ""  # Extract YYYY-MM-DD

        # Title
        title = task.get("title", "(No title)")[:50]

        row = f"{status_mark:<8} {due_str:<12} {title:<50}"
        click.echo(row)

    # Summary
    click.echo()
    click.echo(f"Total: {len(tasks)} tasks")


@click.command()
@click.argument("task_id")
@click.option(
    "--format", "-f", type=click.Choice(["json", "text"]), default="json", help="Output format"
)
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def get(task_id: str, format: str, verbose: int) -> None:
    """Get a single task by ID.

    Retrieves detailed information about a specific task including
    title, notes, due date, status, and timestamps.

    \b
    Finding Task IDs:
        Use 'task list' to get task IDs:
        google-gmail-tool task list

    \b
    Examples:

    \b
        # Get task details (JSON format, default)
        google-gmail-tool task get abc123xyz

    \b
        # Get task in human-readable text format
        google-gmail-tool task get abc123xyz --format text

    \b
        # Get task with verbose logging
        google-gmail-tool task get abc123xyz -vv

    \b
        # Combine with list to get first incomplete task details
        TASK_ID=$(google-gmail-tool task list --incomplete -n 1 | jq -r '.[0].id')
        google-gmail-tool task get "$TASK_ID" --format text

    \b
    Output Format (JSON):
        Returns complete task object with all fields:
        - id, title, notes
        - due, status, completed
        - updated

    \b
    Output Format (Text):
        Human-readable task details:
        Task ID:     abc123xyz
        Title:       Review PR #123
        Notes:       Check code quality and tests
        Due:         2025-11-20T00:00:00.000Z
        Status:      needsAction
        Completed:   None
        Updated:     2025-11-17T10:30:00.000Z

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Task not found
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting task get command")

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

    # Get task
    try:
        task = client.get_task(task_id)

        # Output result
        if format == "json":
            click.echo(json.dumps(task, indent=2))
        else:
            _output_task_text(task)

        logger.info("Task get completed successfully")

    except Exception as e:
        logger.error(f"Failed to get task: {type(e).__name__}: {e}")

        # Check if it's a 404 not found error
        error_str = str(e)
        if "404" in error_str or "not found" in error_str.lower():
            click.echo(f"Error: Task not found: {task_id}", err=True)
            sys.exit(2)
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


def _output_task_text(task: dict[str, Any]) -> None:
    """Output single task in human-readable text format.

    Args:
        task: Task dictionary
    """
    click.echo(f"Task ID:     {task['id']}")
    click.echo(f"Title:       {task.get('title', '(No title)')}")

    if task.get("notes"):
        click.echo(f"Notes:       {task['notes']}")

    click.echo(f"Due:         {task.get('due', 'No due date')}")
    click.echo(f"Status:      {task.get('status', 'unknown')}")
    click.echo(f"Completed:   {task.get('completed', 'None')}")
    click.echo(f"Updated:     {task.get('updated', 'unknown')}")


@click.command()
@click.option("--today", is_flag=True, help="Export today's tasks")
@click.option("--this-week", is_flag=True, help="Export this week's tasks (7 daily notes)")
@click.option("--date", help="Export tasks for specific date (YYYY-MM-DD)")
@click.option("--range-start", help="Custom range start (YYYY-MM-DD)")
@click.option("--range-end", help="Custom range end (YYYY-MM-DD)")
@click.option("--query", "-q", help="Filter tasks by keyword in title/notes")
@click.option("--completed", is_flag=True, help="Include completed tasks")
@click.option(
    "--obsidian-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    envvar="OBSIDIAN_ROOT",
    help="Path to Obsidian vault root (or set OBSIDIAN_ROOT env var)",
)
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def export_obsidian(
    today: bool,
    this_week: bool,
    date: str | None,
    range_start: str | None,
    range_end: str | None,
    query: str | None,
    completed: bool,
    obsidian_root: str | None,
    verbose: int,
) -> None:
    """Export tasks to Obsidian daily notes.

    Exports tasks as checklist items organized by due date sections.
    Uses smart merge logic to preserve checked-off items.

    \b
    Examples:

    \b
        # Export tasks to today's note
        google-gmail-tool task export-obsidian --today

    \b
        # Export to this week's notes (7 files)
        google-gmail-tool task export-obsidian --this-week

    \b
        # Export for specific date
        google-gmail-tool task export-obsidian --date 2025-11-20

    \b
        # Export custom range
        google-gmail-tool task export-obsidian \\
            --range-start "2025-11-20" \\
            --range-end "2025-11-25"

    \b
        # Filter by keyword
        google-gmail-tool task export-obsidian --today --query "project"

    \b
        # Include completed tasks
        google-gmail-tool task export-obsidian --today --completed

    \b
    Output Structure:
        Daily notes: $OBSIDIAN_ROOT/daily/YYYY/YYYY-MM/YYYY-MM-DD.md

        ## Tasks

        ### Overdue
        - [ ] Task 1 (due: 2025-11-15)
          Task notes here

        ### Today
        - [x] Task 2 (due: 2025-11-20)

        ### Tomorrow
        - [ ] Task 3 (due: 2025-11-21)

        ### This Week
        - [ ] Task 4 (due: 2025-11-22)

        ### No Due Date
        - [ ] Task 5

    \b
    Smart Merge Logic:
        - Preserves checked items (tasks you marked as done)
        - Updates task details if changed in Google Tasks
        - Adds new tasks as unchecked items
        - Organizes by due date sections

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Missing OBSIDIAN_ROOT or invalid configuration
    """
    from google_gmail_tool.core.obsidian_task_exporter import ObsidianTaskExporter

    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting task export-obsidian command")

    # Validate time range flag
    flags_set = sum([today, this_week, date is not None, range_start is not None])
    if flags_set == 0:
        click.echo(
            "Error: Must specify --today, --this-week, --date, or --range-start/--range-end",
            err=True,
        )
        sys.exit(2)
    if flags_set > 1:
        click.echo("Error: Only one time range flag can be specified", err=True)
        sys.exit(2)

    # Validate range-start and range-end must be together
    if (range_start is not None) != (range_end is not None):
        click.echo("Error: Must specify both --range-start and --range-end together", err=True)
        sys.exit(2)

    # Check OBSIDIAN_ROOT
    if not obsidian_root:
        obsidian_root = os.environ.get("OBSIDIAN_ROOT")

    if not obsidian_root:
        logger.error("OBSIDIAN_ROOT not set")
        click.echo(
            "Error: OBSIDIAN_ROOT environment variable not set and --obsidian-root not provided",
            err=True,
        )
        click.echo("Set with: export OBSIDIAN_ROOT=/path/to/obsidian/vault", err=True)
        sys.exit(2)

    logger.info(f"Obsidian vault: {obsidian_root}")

    # Parse target dates
    target_dates = []
    if today:
        target_dates.append(datetime.utcnow())
    elif this_week:
        # Monday to Sunday of current week
        now = datetime.utcnow()
        weekday = now.weekday()
        monday = now - timedelta(days=weekday)
        for i in range(7):
            target_dates.append(monday + timedelta(days=i))
    elif date:
        try:
            target_dates.append(datetime.strptime(date, "%Y-%m-%d"))
        except ValueError:
            click.echo(f"Error: Invalid date format: {date}. Expected YYYY-MM-DD", err=True)
            sys.exit(2)
    elif range_start and range_end:
        # Parse custom range and generate list of dates
        try:
            # Parse dates (YYYY-MM-DD format only for tasks)
            start_dt = datetime.strptime(range_start, "%Y-%m-%d")
            end_dt = datetime.strptime(range_end, "%Y-%m-%d")

            logger.debug(f"Custom range: {start_dt} to {end_dt}")

            # Generate list of dates in range (one note per day)
            current_dt = start_dt
            while current_dt <= end_dt:
                target_dates.append(current_dt)
                current_dt += timedelta(days=1)

        except ValueError as e:
            click.echo(f"Error: Invalid date format: {e}", err=True)
            click.echo("Expected: YYYY-MM-DD", err=True)
            sys.exit(2)

    logger.info(f"Exporting tasks for {len(target_dates)} date(s)")

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

    # Initialize Obsidian exporter
    try:
        logger.info("Initializing Obsidian exporter")
        exporter = ObsidianTaskExporter(obsidian_root)
    except Exception as e:
        logger.error(f"Failed to initialize Obsidian exporter: {type(e).__name__}")
        click.echo(f"Error initializing Obsidian exporter: {e}", err=True)
        sys.exit(2)

    # Fetch all tasks
    try:
        logger.info("Fetching tasks from Google Tasks")
        completed_filter = None if completed else False

        tasks = client.list_tasks(completed=completed_filter, query=query, max_results=100)

        logger.info(f"Retrieved {len(tasks)} tasks")

    except Exception as e:
        logger.error(f"Failed to fetch tasks: {type(e).__name__}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Export to each target date
    exported_notes = []
    total_tasks_exported = 0

    try:
        for target_date in target_dates:
            logger.debug(f"Exporting tasks to {target_date.date()}")

            note_path = exporter.export_tasks_to_daily(tasks, target_date)

            exported_notes.append(str(note_path))
            logger.info(f"Exported to: {note_path}")

        total_tasks_exported = len(tasks)

        # Output summary
        click.echo(f"✅ Exported {total_tasks_exported} tasks to {len(exported_notes)} notes")
        click.echo()
        click.echo("Notes created/updated:")
        for note in exported_notes:
            click.echo(f"  {note}")

        logger.info("Task export completed successfully")

    except Exception as e:
        logger.error(f"Failed to export tasks: {type(e).__name__}: {e}")
        click.echo(f"Error during export: {e}", err=True)
        sys.exit(1)
