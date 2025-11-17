"""Calendar CLI commands.

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
from google_gmail_tool.core.calendar_client import CalendarClient
from google_gmail_tool.core.obsidian_calendar_exporter import ObsidianCalendarExporter
from google_gmail_tool.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


def _parse_date_range(
    today: bool,
    tomorrow: bool,
    this_week: bool,
    next_week: bool,
    days: int | None,
    date: str | None,
    range_start: str | None,
    range_end: str | None,
) -> tuple[datetime, datetime]:
    """Parse time range flags into start/end datetimes.

    Args:
        today: Today's events flag
        tomorrow: Tomorrow's events flag
        this_week: This week's events flag
        next_week: Next week's events flag
        days: Number of days from now
        date: Specific date (YYYY-MM-DD)
        range_start: Custom range start (YYYY-MM-DD or YYYY-MM-DD HH:MM)
        range_end: Custom range end (YYYY-MM-DD or YYYY-MM-DD HH:MM)

    Returns:
        Tuple of (start_datetime, end_datetime) in UTC

    Raises:
        click.UsageError: If invalid combination or format
    """
    # Count how many time flags are set
    flags_set = sum([
        today,
        tomorrow,
        this_week,
        next_week,
        days is not None,
        date is not None,
        range_start is not None,
    ])

    # If no flags, default to --this-week
    if flags_set == 0:
        logger.debug("No time range specified, defaulting to --this-week")
        this_week = True
        flags_set = 1

    if flags_set > 1:
        raise click.UsageError("Only one time range flag can be specified")

    now = datetime.utcnow()

    if today:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        logger.debug(f"Time range: today ({start} to {end})")

    elif tomorrow:
        start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        logger.debug(f"Time range: tomorrow ({start} to {end})")

    elif this_week:
        # Monday to Sunday of current week
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        start = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        logger.debug(f"Time range: this week ({start} to {end})")

    elif next_week:
        # Monday to Sunday of next week
        weekday = now.weekday()
        start = (now - timedelta(days=weekday) + timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)
        logger.debug(f"Time range: next week ({start} to {end})")

    elif days is not None:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=days)
        logger.debug(f"Time range: next {days} days ({start} to {end})")

    elif date is not None:
        try:
            start = datetime.strptime(date, "%Y-%m-%d")
            end = start + timedelta(days=1)
            logger.debug(f"Time range: specific date ({start} to {end})")
        except ValueError as e:
            raise click.UsageError(f"Invalid date format: {e}. Expected YYYY-MM-DD")

    elif range_start is not None and range_end is not None:
        try:
            # Try parsing with time first (YYYY-MM-DD HH:MM)
            try:
                start = datetime.strptime(range_start, "%Y-%m-%d %H:%M")
            except ValueError:
                # Fall back to date only (YYYY-MM-DD)
                start = datetime.strptime(range_start, "%Y-%m-%d")

            try:
                end = datetime.strptime(range_end, "%Y-%m-%d %H:%M")
            except ValueError:
                end = datetime.strptime(range_end, "%Y-%m-%d")

            logger.debug(f"Time range: custom ({start} to {end})")

        except ValueError as e:
            raise click.UsageError(
                f"Invalid date format: {e}. Expected YYYY-MM-DD or YYYY-MM-DD HH:MM"
            )

    else:
        raise click.UsageError("Must specify --range-start and --range-end together")

    return start, end


@click.command()
@click.option("--today", is_flag=True, help="Show today's events")
@click.option("--tomorrow", is_flag=True, help="Show tomorrow's events")
@click.option("--this-week", is_flag=True, help="Show this week's events (Monday-Sunday)")
@click.option("--next-week", is_flag=True, help="Show next week's events (Monday-Sunday)")
@click.option("--days", "-d", type=int, help="Show events for next N days")
@click.option("--date", help="Show events for specific date (YYYY-MM-DD)")
@click.option("--range-start", help="Custom range start (YYYY-MM-DD or YYYY-MM-DD HH:MM)")
@click.option("--range-end", help="Custom range end (YYYY-MM-DD or YYYY-MM-DD HH:MM)")
@click.option("--query", "-q", help="Search events by keyword in title/description")
@click.option(
    "--max-results", "-n", type=int, default=100, help="Maximum number of results (default: 100)"
)
@click.option(
    "--format", "-f", type=click.Choice(["json", "text"]), default="json", help="Output format"
)
@click.option("--text", is_flag=True, help="Output in text format (shorthand for --format text)")
@click.option(
    "-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)"
)
def list_cmd(
    today: bool,
    tomorrow: bool,
    this_week: bool,
    next_week: bool,
    days: int | None,
    date: str | None,
    range_start: str | None,
    range_end: str | None,
    query: str | None,
    max_results: int,
    format: str,
    text: bool,
    verbose: int,
) -> None:
    """List calendar events with optional filtering.

    By default, lists this week's events (Monday-Sunday) in JSON format.
    Use time range flags to specify different periods.

    \b
    Free-Text Search (--query):
        Searches event title, description, location, and attendee names/emails.
        Case-insensitive substring matching. No advanced operators (no AND/OR/NOT).

    \b
    Examples:

    \b
        # List this week's events (default)
        google-gmail-tool calendar list

    \b
        # List today's events
        google-gmail-tool calendar list --today

    \b
        # List next 7 days
        google-gmail-tool calendar list --days 7

    \b
        # List events for specific date
        google-gmail-tool calendar list --date "2025-11-20"

    \b
        # Search for standup meetings (matches title/description/location)
        google-gmail-tool calendar list --this-week --query "standup"

    \b
        # Find meetings with specific person (matches attendees)
        google-gmail-tool calendar list --today --query "john@example.com"

    \b
        # Find team meetings (free-text search)
        google-gmail-tool calendar list --this-week --query "team meeting"

    \b
        # Case-insensitive search (both work the same)
        google-gmail-tool calendar list --today --query "STANDUP"
        google-gmail-tool calendar list --today --query "standup"

    \b
        # Custom date range
        google-gmail-tool calendar list --range-start 2025-11-20 --range-end 2025-11-30

    \b
        # Human-readable text output
        google-gmail-tool calendar list --today --text

    \b
    Output Format (JSON):
        Outputs array of event objects to stdout
        Logs to stderr (use -v, -vv, -vvv for verbosity)

    \b
    Output Format (Text):
        Human-readable table format
        TIME         EVENT                LOCATION
        09:00-10:00  Team Standup        Zoom
        14:00-15:00  Client Meeting      Conference Room A

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting calendar list command")

    # Handle --text flag
    if text:
        format = "text"

    # Parse time range
    try:
        time_min, time_max = _parse_date_range(
            today, tomorrow, this_week, next_week, days, date, range_start, range_end
        )
    except click.UsageError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Load credentials
    try:
        logger.info("Loading Google credentials")
        credentials = get_credentials()
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Calendar client
    try:
        logger.info("Initializing Calendar API client")
        client = CalendarClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Calendar client: {type(e).__name__}")
        click.echo(f"Error initializing Calendar API: {e}", err=True)
        sys.exit(1)

    # List events
    try:
        events = client.list_events(
            time_min=time_min,
            time_max=time_max,
            query=query,
            max_results=max_results,
        )

        logger.info(f"Retrieved {len(events)} events")

        # Output results
        if format == "json":
            click.echo(json.dumps(events, indent=2))
        else:
            _output_text_table(events)

        logger.info("Calendar list completed successfully")

    except Exception as e:
        logger.error(f"Failed to list calendar events: {type(e).__name__}: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _output_text_table(events: list[dict[str, Any]]) -> None:
    """Output events as human-readable text table.

    Args:
        events: List of event dictionaries
    """
    if not events:
        click.echo("No events found.")
        return

    # Table header
    header = f"{'TIME':<20} {'EVENT':<40} {'LOCATION':<30}"
    click.echo(header)
    click.echo("=" * len(header))

    # Table rows
    for event in events:
        # Format time
        start = event.get("start") or ""
        end = event.get("end") or ""

        if event.get("is_all_day"):
            time_str = start[:10] if start else "(No date)"  # Just the date for all-day events
        else:
            # Extract HH:MM from ISO datetime
            start_time = start[11:16] if start and len(start) > 16 else start
            end_time = end[11:16] if end and len(end) > 16 else end
            time_str = f"{start_time}-{end_time}" if start_time and end_time else "(No time)"

        summary = (event.get("summary") or "(No title)").replace("\n", " ")[:40]
        location = (event.get("location") or "")[:30]

        row = f"{time_str:<20} {summary:<40} {location:<30}"
        click.echo(row)

    # Summary
    click.echo()
    click.echo(f"Total: {len(events)} events")


@click.command()
@click.argument("event_id")
@click.option(
    "--format", "-f", type=click.Choice(["json", "text"]), default="json", help="Output format"
)
@click.option(
    "-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)"
)
def get(event_id: str, format: str, verbose: int) -> None:
    """Get a single calendar event by ID.

    Retrieves detailed information about a specific calendar event including
    title, description, location, start/end times, attendees, and status.

    \b
    Finding Event IDs:
        Use 'calendar list' to get event IDs:
        google-gmail-tool calendar list --today

    \b
    Examples:

    \b
        # Get event details (JSON format, default)
        google-gmail-tool calendar get abc123xyz

    \b
        # Get event in human-readable text format
        google-gmail-tool calendar get abc123xyz --format text

    \b
        # Get event with verbose logging
        google-gmail-tool calendar get abc123xyz -vv

    \b
        # Combine with list to get today's first event details
        EVENT_ID=$(google-gmail-tool calendar list --today -n 1 | jq -r '.[0].id')
        google-gmail-tool calendar get "$EVENT_ID" --format text

    \b
    Output Format (JSON):
        Returns complete event object with all fields:
        - id, summary, description, location
        - start, end, is_all_day
        - attendees (email, response_status, optional)
        - status, html_link, created, updated

    \b
    Output Format (Text):
        Human-readable event details:
        Event ID:    abc123xyz
        Summary:     Team Standup
        Location:    Zoom
        Start:       2025-11-20T09:00:00Z
        End:         2025-11-20T09:30:00Z
        Attendees:
          - john@example.com [accepted]
          - jane@example.com [needsAction] (optional)

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Event not found
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting calendar get command")

    # Load credentials
    try:
        logger.info("Loading Google credentials")
        credentials = get_credentials()
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Calendar client
    try:
        logger.info("Initializing Calendar API client")
        client = CalendarClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Calendar client: {type(e).__name__}")
        click.echo(f"Error initializing Calendar API: {e}", err=True)
        sys.exit(1)

    # Get event
    try:
        event = client.get_event(event_id)

        # Output result
        if format == "json":
            click.echo(json.dumps(event, indent=2))
        else:
            _output_event_text(event)

        logger.info("Calendar get completed successfully")

    except Exception as e:
        logger.error(f"Failed to get calendar event: {type(e).__name__}: {e}")

        # Check if it's a 404 not found error
        error_str = str(e)
        if "404" in error_str or "not found" in error_str.lower():
            click.echo(f"Error: Event not found: {event_id}", err=True)
            sys.exit(2)
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


def _output_event_text(event: dict[str, Any]) -> None:
    """Output single event in human-readable text format.

    Args:
        event: Event dictionary
    """
    click.echo(f"Event ID:    {event['id']}")
    click.echo(f"Summary:     {event.get('summary', '(No title)')}")

    if event.get("description"):
        click.echo(f"Description: {event['description']}")

    if event.get("location"):
        click.echo(f"Location:    {event['location']}")

    # Start/end times
    if event.get("is_all_day"):
        click.echo(f"Date:        {event['start']} (All day)")
    else:
        click.echo(f"Start:       {event['start']}")
        click.echo(f"End:         {event['end']}")

    # Attendees
    attendees = event.get("attendees", [])
    if attendees:
        click.echo(f"\nAttendees ({len(attendees)}):")
        for att in attendees:
            status = att.get("response_status", "needsAction")
            optional = " (optional)" if att.get("optional") else ""
            click.echo(f"  - {att['email']} [{status}]{optional}")

    click.echo(f"\nStatus:      {event.get('status', 'unknown')}")
    click.echo(f"Link:        {event.get('html_link', 'N/A')}")


@click.command()
@click.option("--today", is_flag=True, help="Export today's events")
@click.option(
    "--this-week", is_flag=True, help="Export this week's events (separate notes per day)"
)
@click.option("--date", help="Export events for specific date (YYYY-MM-DD)")
@click.option("--range-start", help="Custom range start (YYYY-MM-DD or YYYY-MM-DD HH:MM)")
@click.option("--range-end", help="Custom range end (YYYY-MM-DD or YYYY-MM-DD HH:MM)")
@click.option(
    "--query", "-q", help="Filter events by free-text search (title/description/location)"
)
@click.option(
    "--obsidian-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    envvar="OBSIDIAN_ROOT",
    help="Path to Obsidian vault root (or set OBSIDIAN_ROOT env var)",
)
@click.option(
    "-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)"
)
def export_obsidian(
    today: bool,
    this_week: bool,
    date: str | None,
    range_start: str | None,
    range_end: str | None,
    query: str | None,
    obsidian_root: str | None,
    verbose: int,
) -> None:
    """Export calendar events to Obsidian daily notes.

    Exports calendar events as checklist items to daily notes in your Obsidian vault.
    Uses smart merge logic to preserve checked-off items while updating the schedule.

    \b
    Free-Text Search (--query):
        Searches event title, description, location, and attendee names/emails.
        Case-insensitive substring matching. No advanced operators.

    \b
    Examples:

    \b
        # Export today's events
        google-gmail-tool calendar export-obsidian --today

    \b
        # Export this week's events (creates/updates 7 daily notes)
        google-gmail-tool calendar export-obsidian --this-week

    \b
        # Export specific date
        google-gmail-tool calendar export-obsidian --date 2025-11-20

    \b
        # Export only standup meetings from today
        google-gmail-tool calendar export-obsidian --today --query "standup"

    \b
        # Export meetings with specific person this week
        google-gmail-tool calendar export-obsidian --this-week --query "john@example.com"

    \b
        # Export team meetings only
        google-gmail-tool calendar export-obsidian --today --query "team meeting"

    \b
        # Export custom date range
        google-gmail-tool calendar export-obsidian \\
            --range-start "2025-11-20" \\
            --range-end "2025-11-25"

    \b
        # Export custom date range with specific times
        google-gmail-tool calendar export-obsidian \\
            --range-start "2025-11-20 09:00" \\
            --range-end "2025-11-25 18:00"

    \b
    Smart Merge Logic:
        - Preserves checked items (events you marked as done)
        - Updates event times/titles if changed in calendar
        - Adds new events as unchecked items
        - Removes events no longer in calendar

    \b
    Output Structure:
        Daily notes: $OBSIDIAN_ROOT/daily/YYYY/YYYY-MM/YYYY-MM-DD.md

        ---
        date: 2025-11-20
        type: daily
        tags:
          - daily
        ---

        # 2025-11-20

        ## Calendar
        - [x] 09:00-10:00 Team Standup @ Zoom
        - [ ] 14:00-15:00 Client Meeting @ Conference Room A
        - [ ] 16:30-17:00 1:1 with Manager

    \b
    Required Environment Variables:
        OBSIDIAN_ROOT - Path to Obsidian vault root directory

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Missing OBSIDIAN_ROOT or invalid configuration
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting calendar export-obsidian command")

    # Validate time range flag
    flags_set = sum([today, this_week, date is not None, range_start is not None])
    if flags_set == 0:
        click.echo(
            "Error: Must specify --today, --this-week, --date, or --range-start/--range-end",
            err=True,
        )
        click.echo("Example: google-gmail-tool calendar export-obsidian --today", err=True)
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
            # Try parsing with time first (YYYY-MM-DD HH:MM)
            try:
                start_dt = datetime.strptime(range_start, "%Y-%m-%d %H:%M")
            except ValueError:
                # Fall back to date only (YYYY-MM-DD)
                start_dt = datetime.strptime(range_start, "%Y-%m-%d")

            try:
                end_dt = datetime.strptime(range_end, "%Y-%m-%d %H:%M")
            except ValueError:
                end_dt = datetime.strptime(range_end, "%Y-%m-%d")

            logger.debug(f"Custom range: {start_dt} to {end_dt}")

            # Generate list of dates in range (one note per day)
            current_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)

            while current_dt <= end_date:
                target_dates.append(current_dt)
                current_dt += timedelta(days=1)

        except ValueError as e:
            click.echo(f"Error: Invalid date format: {e}", err=True)
            click.echo("Expected: YYYY-MM-DD or YYYY-MM-DD HH:MM", err=True)
            sys.exit(2)

    logger.info(f"Exporting events for {len(target_dates)} date(s)")

    # Load credentials
    try:
        logger.info("Loading Google credentials")
        credentials = get_credentials()
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Calendar client
    try:
        logger.info("Initializing Calendar API client")
        client = CalendarClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Calendar client: {type(e).__name__}")
        click.echo(f"Error initializing Calendar API: {e}", err=True)
        sys.exit(1)

    # Initialize Obsidian exporter
    try:
        logger.info("Initializing Obsidian exporter")
        exporter = ObsidianCalendarExporter(obsidian_root)
    except Exception as e:
        logger.error(f"Failed to initialize Obsidian exporter: {type(e).__name__}")
        click.echo(f"Error initializing Obsidian exporter: {e}", err=True)
        sys.exit(2)

    # Process each date
    exported_notes = []
    total_events = 0

    try:
        for target_date in target_dates:
            logger.info(f"Processing date: {target_date.date()}")

            # Fetch events for this day
            time_min = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            time_max = time_min + timedelta(days=1)

            events = client.list_events(
                time_min=time_min, time_max=time_max, query=query, max_results=100
            )

            logger.info(f"Found {len(events)} events for {target_date.date()}")
            total_events += len(events)

            # Export to Obsidian
            note_path = exporter.export_events_to_daily(events, target_date)
            exported_notes.append(str(note_path))
            logger.info(f"Exported to: {note_path}")

        # Output results
        results = {
            "exported_dates": len(exported_notes),
            "total_events": total_events,
            "notes": exported_notes,
        }

        click.echo(json.dumps(results, indent=2))
        logger.info(f"Export complete: {len(exported_notes)} daily notes updated")

    except Exception as e:
        logger.error(f"Failed to export calendar: {type(e).__name__}: {e}")
        logger.debug("Full traceback:", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
