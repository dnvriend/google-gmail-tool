"""Calendar create, update, and delete commands.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
import sys
from datetime import datetime

import click

from google_gmail_tool.core.auth import AuthenticationError, get_credentials
from google_gmail_tool.core.calendar_client import CalendarClient
from google_gmail_tool.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@click.command()
@click.option("--title", "-t", required=True, help="Event title/summary")
@click.option("--start", help="Start datetime (YYYY-MM-DD HH:MM or YYYY-MM-DD)")
@click.option("--end", help="End datetime (YYYY-MM-DD HH:MM or YYYY-MM-DD)")
@click.option("--date", help="Date for all-day event (YYYY-MM-DD)")
@click.option("--all-day", is_flag=True, help="Create all-day event (requires --date)")
@click.option("--location", "-l", help="Event location")
@click.option("--description", "-d", help="Event description")
@click.option("--attendees", "-a", help="Comma-separated list of attendee emails")
@click.option("--add-meet", is_flag=True, help="Add Google Meet video conferencing")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def create(
    title: str,
    start: str,
    end: str | None,
    date: str | None,
    all_day: bool,
    location: str | None,
    description: str | None,
    attendees: str | None,
    add_meet: bool,
    verbose: int,
) -> None:
    """Create a new calendar event.

    Creates a calendar event with specified title, time, and optional details.
    Uses system's local timezone for event times.

    \b
    Event Types:
        Regular event: Requires --title, --start, --end
        All-day event: Requires --title, --date, --all-day

    \b
    Examples:

    \b
        # Create basic event
        google-gmail-tool calendar create \\
            --title "Team Standup" \\
            --start "2025-11-20 09:00" \\
            --end "2025-11-20 09:30"

    \b
        # Event with location and description
        google-gmail-tool calendar create \\
            --title "Client Meeting" \\
            --start "2025-11-20 14:00" \\
            --end "2025-11-20 15:00" \\
            --location "Conference Room A" \\
            --description "Q4 review discussion"

    \b
        # Event with attendees
        google-gmail-tool calendar create \\
            --title "Project Sync" \\
            --start "2025-11-20 10:00" \\
            --end "2025-11-20 10:30" \\
            --attendees "john@example.com,jane@example.com"

    \b
        # Event with Google Meet
        google-gmail-tool calendar create \\
            --title "Remote Standup" \\
            --start "2025-11-20 09:00" \\
            --end "2025-11-20 09:30" \\
            --add-meet

    \b
        # All-day event
        google-gmail-tool calendar create \\
            --title "Holiday" \\
            --date "2025-12-25" \\
            --all-day

    \b
    Output Format (JSON):
        Returns created event object with:
        - id, summary, description, location
        - start, end, is_all_day
        - attendees, html_link
        - created, updated, status

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Invalid parameters
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting calendar create command")

    # Validate parameters
    if all_day:
        if not date:
            click.echo("Error: --all-day requires --date", err=True)
            sys.exit(2)
        if start or end:
            click.echo("Error: --all-day cannot be used with --start or --end", err=True)
            sys.exit(2)
    else:
        if not start or not end:
            click.echo("Error: Regular event requires --start and --end", err=True)
            sys.exit(2)
        if date:
            click.echo("Error: --date is only for all-day events", err=True)
            sys.exit(2)

    # Parse datetimes
    try:
        if all_day:
            # All-day event
            if not date:
                raise ValueError("date is required for all-day events")
            start_dt = datetime.strptime(date, "%Y-%m-%d")
            # End date is next day for all-day events
            end_dt = datetime.strptime(date, "%Y-%m-%d")
            # Google expects end date to be exclusive (next day)
            from datetime import timedelta

            end_dt = end_dt + timedelta(days=1)
        else:
            # Regular event
            if not start or not end:
                raise ValueError("start and end are required for regular events")
            # Try with time first
            try:
                start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
            except ValueError:
                # Try date only (default to midnight)
                start_dt = datetime.strptime(start, "%Y-%m-%d")
                end_dt = datetime.strptime(end, "%Y-%m-%d")

    except ValueError as e:
        click.echo(f"Error: Invalid date/time format: {e}", err=True)
        click.echo("Expected: YYYY-MM-DD HH:MM or YYYY-MM-DD", err=True)
        sys.exit(2)

    # Parse attendees
    attendee_list = None
    if attendees:
        attendee_list = [email.strip() for email in attendees.split(",")]

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

    # Create event
    try:
        event = client.create_event(
            title=title,
            start=start_dt,
            end=end_dt,
            location=location,
            description=description,
            attendees=attendee_list,
            add_meet=add_meet,
            is_all_day=all_day,
        )

        logger.info(f"Event created: {event['id']}")
        click.echo(json.dumps(event, indent=2))

    except Exception as e:
        logger.error(f"Failed to create event: {type(e).__name__}: {e}")
        logger.debug("Full traceback:", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("event_id")
@click.option("--title", "-t", help="New event title")
@click.option("--start", help="New start datetime (YYYY-MM-DD HH:MM)")
@click.option("--end", help="New end datetime (YYYY-MM-DD HH:MM)")
@click.option("--location", "-l", help="New location")
@click.option("--description", "-d", help="New description")
@click.option("--attendees", "-a", help="New comma-separated list of attendee emails")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def update(
    event_id: str,
    title: str | None,
    start: str | None,
    end: str | None,
    location: str | None,
    description: str | None,
    attendees: str | None,
    verbose: int,
) -> None:
    """Update an existing calendar event.

    Updates specified fields of an existing event. Only provided fields are updated.
    Use 'calendar list' or 'calendar get' to find event IDs.

    \b
    Examples:

    \b
        # Update event title
        google-gmail-tool calendar update abc123xyz --title "New Meeting Title"

    \b
        # Update event time
        google-gmail-tool calendar update abc123xyz \\
            --start "2025-11-20 15:00" \\
            --end "2025-11-20 16:00"

    \b
        # Update multiple fields
        google-gmail-tool calendar update abc123xyz \\
            --title "Updated Meeting" \\
            --location "New Conference Room" \\
            --description "Updated agenda"

    \b
        # Update attendees
        google-gmail-tool calendar update abc123xyz \\
            --attendees "new@example.com,another@example.com"

    \b
        # Combine with list to update first event
        EVENT_ID=$(google-gmail-tool calendar list --today -n 1 | jq -r '.[0].id')
        google-gmail-tool calendar update "$EVENT_ID" --title "Updated Title"

    \b
    Output Format (JSON):
        Returns updated event object with all fields

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Event not found or invalid parameters
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting calendar update command")

    # Validate at least one field is provided
    if not any([title, start, end, location, description, attendees]):
        click.echo("Error: Must specify at least one field to update", err=True)
        click.echo(
            "Use --title, --start, --end, --location, --description, or --attendees", err=True
        )
        sys.exit(2)

    # Parse datetimes
    start_dt = None
    end_dt = None
    if start:
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
        except ValueError as e:
            click.echo(f"Error: Invalid start datetime: {e}", err=True)
            click.echo("Expected: YYYY-MM-DD HH:MM", err=True)
            sys.exit(2)

    if end:
        try:
            end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
        except ValueError as e:
            click.echo(f"Error: Invalid end datetime: {e}", err=True)
            click.echo("Expected: YYYY-MM-DD HH:MM", err=True)
            sys.exit(2)

    # Parse attendees
    attendee_list = None
    if attendees:
        attendee_list = [email.strip() for email in attendees.split(",")]

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

    # Update event
    try:
        event = client.update_event(
            event_id=event_id,
            title=title,
            start=start_dt,
            end=end_dt,
            location=location,
            description=description,
            attendees=attendee_list,
        )

        logger.info(f"Event updated: {event_id}")
        click.echo(json.dumps(event, indent=2))

    except Exception as e:
        logger.error(f"Failed to update event: {type(e).__name__}: {e}")
        logger.debug("Full traceback:", exc_info=True)

        # Check if it's a 404 not found error
        error_str = str(e)
        if "404" in error_str or "not found" in error_str.lower():
            click.echo(f"Error: Event not found: {event_id}", err=True)
            sys.exit(2)
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@click.command()
@click.argument("event_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v INFO, -vv DEBUG)")
def delete(event_id: str, force: bool, verbose: int) -> None:
    """Delete a calendar event.

    Permanently deletes a calendar event by ID.
    Use 'calendar list' or 'calendar get' to find event IDs.

    \b
    Examples:

    \b
        # Delete event with confirmation
        google-gmail-tool calendar delete abc123xyz

    \b
        # Delete without confirmation (force)
        google-gmail-tool calendar delete abc123xyz --force

    \b
        # Combine with list to delete first event
        EVENT_ID=$(google-gmail-tool calendar list --today -n 1 | jq -r '.[0].id')
        google-gmail-tool calendar delete "$EVENT_ID" --force

    \b
        # Get event details before deleting
        google-gmail-tool calendar get abc123xyz --format text
        google-gmail-tool calendar delete abc123xyz

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Event not found or deletion cancelled
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting calendar delete command")

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

    # Fetch event details for confirmation
    if not force:
        try:
            event = client.get_event(event_id)
            click.echo(f"Event: {event['summary']}", err=True)
            click.echo(f"Start: {event['start']}", err=True)
            click.echo(f"End:   {event['end']}", err=True)
            if not click.confirm("\nAre you sure you want to delete this event?", err=True):
                click.echo("Deletion cancelled.", err=True)
                sys.exit(2)
        except Exception as e:
            logger.error(f"Failed to fetch event: {type(e).__name__}: {e}")
            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                click.echo(f"Error: Event not found: {event_id}", err=True)
                sys.exit(2)
            else:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

    # Delete event
    try:
        client.delete_event(event_id)
        logger.info(f"Event deleted: {event_id}")
        click.echo(json.dumps({"status": "deleted", "event_id": event_id}, indent=2))

    except Exception as e:
        logger.error(f"Failed to delete event: {type(e).__name__}: {e}")
        logger.debug("Full traceback:", exc_info=True)

        # Check if it's a 404 not found error
        error_str = str(e)
        if "404" in error_str or "not found" in error_str.lower():
            click.echo(f"Error: Event not found: {event_id}", err=True)
            sys.exit(2)
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
