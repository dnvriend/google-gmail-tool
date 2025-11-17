"""Mail (Gmail) CLI commands.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
import os
import sys
from typing import Any

import click

from google_gmail_tool.core.auth import AuthenticationError, get_credentials
from google_gmail_tool.core.gmail_client import GmailClient
from google_gmail_tool.core.obsidian_exporter import ObsidianExporter
from google_gmail_tool.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@click.command()
@click.option(
    "--query",
    "-q",
    default=None,
    help="Gmail search query (e.g., 'is:unread after:2025/01/01')",
)
@click.option(
    "--today",
    is_flag=True,
    help="Filter emails from today only (equivalent to newer_than:1d)",
)
@click.option(
    "--max-results",
    "-n",
    type=int,
    default=50,
    help="Maximum number of results (default: 50, max: 500)",
)
@click.option(
    "--format",
    "-f",
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
    "--message-mode",
    is_flag=True,
    help="List individual messages instead of threads (default: thread-mode)",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)",
)
def list_cmd(
    query: str | None,
    today: bool,
    max_results: int,
    format: str,
    text: bool,
    message_mode: bool,
    verbose: int,
) -> None:
    """List Gmail messages or threads with optional filtering.

    By default, lists threads (conversations) in JSON format. Use --message-mode
    to list individual messages. Use --text or --format text for human-readable output.

    Supports full Gmail search syntax via --query option.

    \b
    Gmail Search Operators:
        is:unread, is:read, is:starred        Message status
        has:attachment, filename:pdf           Attachments
        from:email@example.com                 Sender
        to:email@example.com                   Recipient
        subject:keyword                        Subject line
        after:YYYY/MM/DD, before:YYYY/MM/DD   Date range
        older_than:2d, newer_than:1m          Relative dates
        label:important, in:inbox              Labels

    \b
    Examples:

    \b
        # List 50 most recent threads (default)
        google-gmail-tool mail list

    \b
        # List emails from today only
        google-gmail-tool mail list --today

    \b
        # Find unread emails from today
        google-gmail-tool mail list --today --query "is:unread"

    \b
        # Find unread emails (any date)
        google-gmail-tool mail list --query "is:unread"

    \b
        # Emails with attachments after specific date
        google-gmail-tool mail list -q "has:attachment after:2025/01/01" -n 100

    \b
        # From specific sender
        google-gmail-tool mail list -q "from:boss@work.com"

    \b
        # Combine multiple operators
        google-gmail-tool mail list -q "is:unread has:attachment newer_than:7d"

    \b
        # Text output for human viewing (two ways)
        google-gmail-tool mail list -q "is:starred" --text

    \b
        # Text output using --format flag
        google-gmail-tool mail list -q "is:starred" --format text

    \b
        # List individual messages instead of threads
        google-gmail-tool mail list --message-mode -n 20

    \b
        # Debug mode to see API calls
        google-gmail-tool mail list -q "subject:invoice" -vv

    \b
    Output Format (JSON):
        Outputs array of thread/message objects to stdout
        Logs to stderr (use -v, -vv, -vvv for verbosity)

    \b
    Output Format (Text):
        Human-readable table format
        ID            SUBJECT                FROM              DATE
        18abc123...   Project Update        sender@...        2025-01-15 10:30

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting mail list command")
    logger.debug(
        f"Parameters: query={query}, today={today}, max_results={max_results}, "
        f"format={format}, text={text}, message_mode={message_mode}"
    )

    # Handle --text flag (shorthand for --format text)
    if text:
        format = "text"
        logger.debug("Using text format from --text flag")

    # Handle --today flag
    if today:
        today_query = "newer_than:1d"
        if query:
            # Combine with existing query
            query = f"{query} {today_query}"
            logger.debug(f"Combined query with --today: {query}")
        else:
            query = today_query
            logger.debug(f"Using --today query: {query}")

    # Load credentials
    try:
        logger.info("Loading Gmail credentials")
        credentials = get_credentials()
        logger.debug("Credentials loaded successfully")
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        logger.debug("Credential error:", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Gmail client
    try:
        logger.info("Initializing Gmail API client")
        client = GmailClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Gmail client: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.debug("Initialization error:", exc_info=True)
        click.echo(f"Error initializing Gmail API: {e}", err=True)
        sys.exit(1)

    # List threads or messages
    try:
        if message_mode:
            logger.info("Listing messages (message-mode)")
            results = client.list_messages(query=query, max_results=max_results)
        else:
            logger.info("Listing threads (thread-mode)")
            results = client.list_threads(query=query, max_results=max_results)

        logger.info(f"Retrieved {len(results)} {'messages' if message_mode else 'threads'}")

        # Output results
        if format == "json":
            # JSON to stdout
            logger.debug("Outputting JSON to stdout")
            click.echo(json.dumps(results, indent=2))
        else:
            # Text table to stdout
            logger.debug("Outputting text table to stdout")
            _output_text_table(results, message_mode)

        logger.info("Mail list completed successfully")

    except Exception as e:
        logger.error(f"Failed to list mail: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.debug("Full traceback:", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _output_text_table(results: list[dict[str, Any]], message_mode: bool) -> None:
    """Output results as human-readable text table.

    Args:
        results: List of thread/message dictionaries
        message_mode: Whether results are messages (vs threads)
    """
    if not results:
        click.echo("No results found.")
        return

    # Table header
    if message_mode:
        header = f"{'ID':<20} {'SUBJECT':<40} {'FROM':<30} {'DATE':<20}"
    else:
        header = f"{'THREAD_ID':<20} {'SUBJECT':<40} {'FROM':<30} {'DATE':<20} {'MSGS':<5}"

    click.echo(header)
    click.echo("=" * len(header))

    # Table rows
    for item in results:
        # Truncate long fields
        item_id = item["id"][:20]
        subject = item.get("subject", "(No Subject)")[:40]
        from_addr = item.get("from", "")[:30]
        date = item.get("date", "")[:20]

        if message_mode:
            row = f"{item_id:<20} {subject:<40} {from_addr:<30} {date:<20}"
        else:
            msg_count = item.get("message_count", 0)
            row = f"{item_id:<20} {subject:<40} {from_addr:<30} {date:<20} {msg_count:<5}"

        click.echo(row)

    # Summary
    click.echo()
    click.echo(f"Total: {len(results)} {'messages' if message_mode else 'threads'}")


@click.command()
@click.option(
    "--to",
    "-t",
    required=True,
    help="Recipient email address(es) (comma-separated for multiple)",
)
@click.option(
    "--subject",
    "-s",
    required=True,
    help="Email subject line",
)
@click.option(
    "--body",
    "-b",
    required=True,
    help="Email body content (use @filename to read from file)",
)
@click.option(
    "--from",
    "from_addr",
    default=None,
    help="Sender email address (defaults to authenticated user)",
)
@click.option(
    "--cc",
    default=None,
    help="CC email address(es) (comma-separated for multiple)",
)
@click.option(
    "--bcc",
    default=None,
    help="BCC email address(es) (comma-separated for multiple)",
)
@click.option(
    "--html",
    is_flag=True,
    help="Send as HTML email (default: plain text)",
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    default=False,
    help="Preview email without sending",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)",
)
def send(
    to: str,
    subject: str,
    body: str,
    from_addr: str | None,
    cc: str | None,
    bcc: str | None,
    html: bool,
    dry_run: bool,
    verbose: int,
) -> None:
    """Send an email message via Gmail.

    Sends emails using the Gmail API with support for HTML, CC, BCC, and attachments.

    \b
    Examples:

    \b
        # Send simple plain text email
        google-gmail-tool mail send \\
            --to recipient@example.com \\
            --subject "Hello" \\
            --body "This is a test message"

    \b
        # Send to yourself
        google-gmail-tool mail send \\
            -t dnvriend@gmail.com \\
            -s "Test Email" \\
            -b "Testing the send command"

    \b
        # Send with CC and BCC
        google-gmail-tool mail send \\
            -t primary@example.com \\
            --cc colleague@work.com \\
            --bcc archive@example.com \\
            -s "Team Update" \\
            -b "Latest project status"

    \b
        # Send HTML email
        google-gmail-tool mail send \\
            -t recipient@example.com \\
            -s "HTML Test" \\
            -b "<h1>Hello</h1><p>This is <strong>HTML</strong></p>" \\
            --html

    \b
        # Read body from file
        google-gmail-tool mail send \\
            -t recipient@example.com \\
            -s "Report" \\
            -b @report.txt

    \b
        # Preview without sending (dry-run)
        google-gmail-tool mail send \\
            -t recipient@example.com \\
            -s "Test" \\
            -b "Preview this" \\
            --dry-run

    \b
        # Debug mode
        google-gmail-tool mail send \\
            -t recipient@example.com \\
            -s "Debug Test" \\
            -b "Testing with verbose logging" \\
            -vv

    \b
    Output Format:
        Returns JSON with sent message metadata:
        {
          "id": "message_id",
          "thread_id": "thread_id",
          "labels": ["SENT"],
          "to": "recipient@example.com",
          "subject": "Email subject"
        }

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Invalid email address or parameters
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting mail send command")
    logger.debug(f"Parameters: to={to}, subject={subject}, dry_run={dry_run}")

    # Handle file body (@filename syntax)
    if body.startswith("@"):
        filename = body[1:]
        logger.debug(f"Reading body from file: {filename}")
        try:
            with open(filename) as f:
                body = f.read()
            logger.debug(f"Loaded {len(body)} characters from file")
        except FileNotFoundError:
            logger.error(f"Body file not found: {filename}")
            click.echo(f"Error: File not found: {filename}", err=True)
            sys.exit(2)
        except Exception as e:
            logger.error(f"Failed to read body file: {type(e).__name__}")
            logger.error(f"Error: {str(e)}")
            click.echo(f"Error reading file: {e}", err=True)
            sys.exit(2)

    # Validate email addresses
    import re

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    def validate_emails(email_str: str, field_name: str) -> None:
        """Validate comma-separated email addresses."""
        emails = [e.strip() for e in email_str.split(",")]
        for email in emails:
            if not re.match(email_pattern, email):
                logger.error(f"Invalid email in {field_name}: {email}")
                click.echo(f"Error: Invalid email address in {field_name}: {email}", err=True)
                click.echo("Expected format: user@domain.com", err=True)
                sys.exit(2)

    validate_emails(to, "--to")
    if cc:
        validate_emails(cc, "--cc")
    if bcc:
        validate_emails(bcc, "--bcc")
    if from_addr:
        validate_emails(from_addr, "--from")

    # Dry-run preview
    if dry_run:
        logger.info("Dry-run mode: previewing email without sending")
        preview = {
            "to": to,
            "from": from_addr or "(authenticated user)",
            "cc": cc or None,
            "bcc": bcc or None,
            "subject": subject,
            "body_length": len(body),
            "body_preview": body[:200] + ("..." if len(body) > 200 else ""),
            "html": html,
        }
        click.echo("DRY-RUN: Email preview (not sent)")
        click.echo(json.dumps(preview, indent=2))
        sys.exit(0)

    # Load credentials
    try:
        logger.info("Loading Gmail credentials")
        credentials = get_credentials()
        logger.debug("Credentials loaded successfully")
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        logger.debug("Credential error:", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Gmail client
    try:
        logger.info("Initializing Gmail API client")
        client = GmailClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Gmail client: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.debug("Initialization error:", exc_info=True)
        click.echo(f"Error initializing Gmail API: {e}", err=True)
        sys.exit(1)

    # Send email
    try:
        result = client.send_email(
            to=to,
            subject=subject,
            body=body,
            from_addr=from_addr,
            cc=cc,
            bcc=bcc,
            html=html,
        )

        logger.info("Email sent successfully")
        logger.debug(f"Message ID: {result['id']}")

        # Output result as JSON
        click.echo(json.dumps(result, indent=2))

    except Exception as e:
        logger.error(f"Failed to send email: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.debug("Full traceback:", exc_info=True)
        click.echo(f"Error sending email: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("message_id")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "text"], case_sensitive=False),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--include-body",
    is_flag=True,
    help="Include full message body in output",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)",
)
def get(
    message_id: str,
    format: str,
    include_body: bool,
    verbose: int,
) -> None:
    """Get a single email message by ID.

    Retrieves detailed information about a specific Gmail message using its message ID.
    By default returns metadata only. Use --include-body to get full message content.

    \b
    Examples:

    \b
        # Get message metadata (default)
        google-gmail-tool mail get 19a90f13e3c7af52

    \b
        # Get message with full body content
        google-gmail-tool mail get 19a90f13e3c7af52 --include-body

    \b
        # Get message in text format
        google-gmail-tool mail get 19a90f13e3c7af52 --format text

    \b
        # Get full message with verbose logging
        google-gmail-tool mail get 19a90f13e3c7af52 --include-body -vv

    \b
    Output Format (JSON):
        Returns message object with metadata
        With --include-body: includes body_plain, body_html, body_markdown fields

    \b
    Output Format (Text):
        Human-readable message display
        Shows: From, To, Subject, Date, Labels
        With --include-body: includes message body

    \b
    Exit Codes:
        0    Success
        1    Authentication failed or API error
        2    Message not found
    """
    # Setup logging
    setup_logging(verbose)
    logger.debug("Starting mail get command")
    logger.debug(f"Parameters: message_id={message_id}, include_body={include_body}")

    # Load credentials
    try:
        logger.info("Loading Gmail credentials")
        credentials = get_credentials()
        logger.debug("Credentials loaded successfully")
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        logger.debug("Credential error:", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Gmail client
    try:
        logger.info("Initializing Gmail API client")
        client = GmailClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Gmail client: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.debug("Initialization error:", exc_info=True)
        click.echo(f"Error initializing Gmail API: {e}", err=True)
        sys.exit(1)

    # Get message
    try:
        logger.info(f"Fetching message: {message_id}")

        if include_body:
            # Get full message with body content
            message = client.get_message_full(message_id)
            logger.info("Retrieved message with full body")
        else:
            # Get metadata only
            message = client._get_message(message_id)
            logger.info("Retrieved message metadata")

        # Output results
        if format == "json":
            # JSON to stdout
            logger.debug("Outputting JSON to stdout")
            click.echo(json.dumps(message, indent=2))
        else:
            # Text output
            logger.debug("Outputting text to stdout")
            _output_message_text(message, include_body)

        logger.info("Mail get completed successfully")

    except Exception as e:
        logger.error(f"Failed to get message: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.debug("Full traceback:", exc_info=True)

        # Check if it's a 404 not found error
        error_str = str(e)
        if "404" in error_str or "not found" in error_str.lower():
            click.echo(f"Error: Message not found: {message_id}", err=True)
            sys.exit(2)
        else:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


def _output_message_text(message: dict[str, Any], include_body: bool) -> None:
    """Output message in human-readable text format.

    Args:
        message: Message dictionary
        include_body: Whether to include message body
    """
    click.echo(f"Message ID: {message['id']}")
    click.echo(f"Thread ID:  {message.get('thread_id', 'N/A')}")
    click.echo(f"From:       {message.get('from', 'N/A')}")
    click.echo(f"To:         {message.get('to', 'N/A')}")

    if message.get("cc"):
        click.echo(f"CC:         {message['cc']}")

    click.echo(f"Subject:    {message.get('subject', '(No Subject)')}")
    click.echo(f"Date:       {message.get('date_iso', message.get('date', 'N/A'))}")

    labels = message.get("labels", [])
    if labels:
        click.echo(f"Labels:     {', '.join(labels)}")

    # Attachments
    attachments = message.get("attachments", [])
    if attachments:
        click.echo(f"\nAttachments ({len(attachments)}):")
        for att in attachments:
            size_kb = att["size"] / 1024
            click.echo(f"  - {att['filename']} ({size_kb:.1f} KB, {att['mime_type']})")

    # Body content
    if include_body:
        click.echo("\n" + "=" * 80)
        click.echo("MESSAGE BODY")
        click.echo("=" * 80 + "\n")

        body = message.get("body_markdown") or message.get("body_plain") or "(No content)"
        click.echo(body)


@click.command()
@click.option(
    "--query",
    "-q",
    help="Gmail search query to filter emails (e.g., 'is:unread')",
)
@click.option(
    "--today",
    is_flag=True,
    help="Export emails from today only (equivalent to newer_than:1d)",
)
@click.option(
    "--max-results",
    "-n",
    type=int,
    default=50,
    help="Maximum number of threads to export (default: 50, max: 500)",
)
@click.option(
    "--obsidian-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    envvar="OBSIDIAN_ROOT",
    help="Path to Obsidian vault root (or set OBSIDIAN_ROOT env var)",
)
@click.option(
    "--download-attachments",
    is_flag=True,
    default=True,
    help="Download and save attachments (default: enabled)",
)
@click.option(
    "--no-download-attachments",
    is_flag=True,
    help="Skip downloading attachments",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)",
)
def export_obsidian(
    query: str | None,
    today: bool,
    max_results: int,
    obsidian_root: str | None,
    download_attachments: bool,
    no_download_attachments: bool,
    verbose: int,
) -> None:
    """Export Gmail threads to Obsidian markdown notes.

    Fetches Gmail threads matching the query and exports them to Obsidian with:
    - Proper frontmatter (subject, from, to, cc, bcc, date, tags, etc.)
    - Markdown-formatted email bodies (HTML converted to markdown)
    - Downloaded attachments saved in thread folder
    - Thread-based organization (one folder per thread)

    Thread folders are organized as:
    $OBSIDIAN_ROOT/emails/<timestamp>-<sender>-<subject>/

    \b
    Examples:

    \b
        # Export all emails from today
        google-gmail-tool mail export-obsidian --today

    \b
        # Export unread emails from today
        google-gmail-tool mail export-obsidian --today --query "is:unread"

    \b
        # Export unread emails (any date)
        google-gmail-tool mail export-obsidian --query "is:unread"

    \b
        # Export emails from specific sender
        google-gmail-tool mail export-obsidian \\
            -q "from:boss@work.com" \\
            -n 10

    \b
        # Export important emails with attachments
        google-gmail-tool mail export-obsidian \\
            -q "is:important has:attachment" \\
            -n 20

    \b
        # Export to specific Obsidian vault
        google-gmail-tool mail export-obsidian \\
            -q "subject:invoice after:2025/01/01" \\
            --obsidian-root /path/to/vault

    \b
        # Skip downloading attachments
        google-gmail-tool mail export-obsidian \\
            -q "is:starred" \\
            --no-download-attachments

    \b
        # Debug mode with verbose logging
        google-gmail-tool mail export-obsidian \\
            -q "from:client@example.com" \\
            -vv

    \b
    Output Format:
        Returns JSON with export results:
        {
          "exported_threads": 5,
          "exported_messages": 12,
          "downloaded_attachments": 8,
          "notes": ["path/to/note1.md", "path/to/note2.md"]
        }

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
    logger.debug("Starting mail export-obsidian command")
    logger.debug(f"Parameters: query={query}, today={today}, max_results={max_results}")

    # Handle --today flag
    if today:
        today_query = "newer_than:1d"
        if query:
            # Combine with existing query
            query = f"{query} {today_query}"
            logger.debug(f"Combined query with --today: {query}")
        else:
            query = today_query
            logger.debug(f"Using --today query: {query}")

    # Validate that we have a query (either from --query or --today)
    if not query:
        logger.error("No query specified")
        click.echo(
            "Error: Must specify either --query or --today to filter emails",
            err=True,
        )
        click.echo("Example: google-gmail-tool mail export-obsidian --today", err=True)
        sys.exit(2)

    # Handle attachment download flag
    if no_download_attachments:
        download_attachments = False

    logger.debug(f"Download attachments: {download_attachments}")

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

    # Load credentials
    try:
        logger.info("Loading Gmail credentials")
        credentials = get_credentials()
        logger.debug("Credentials loaded successfully")
    except AuthenticationError as e:
        logger.error("Failed to load credentials")
        logger.debug("Credential error:", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Initialize Gmail client
    try:
        logger.info("Initializing Gmail API client")
        client = GmailClient(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Gmail client: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.debug("Initialization error:", exc_info=True)
        click.echo(f"Error initializing Gmail API: {e}", err=True)
        sys.exit(1)

    # Initialize Obsidian exporter
    try:
        logger.info("Initializing Obsidian exporter")
        exporter = ObsidianExporter(obsidian_root)
    except Exception as e:
        logger.error(f"Failed to initialize Obsidian exporter: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        click.echo(f"Error initializing Obsidian exporter: {e}", err=True)
        sys.exit(2)

    # Fetch threads
    try:
        logger.info(f"Fetching threads with query: {query}")
        threads = client.list_threads(query=query, max_results=max_results)
        logger.info(f"Found {len(threads)} threads to export")

        if not threads:
            click.echo("No threads found matching query.")
            sys.exit(0)

        exported_notes = []
        total_messages = 0
        total_attachments = 0

        # Process each thread
        for i, thread in enumerate(threads, 1):
            thread_id = thread["id"]
            logger.info(f"Processing thread {i}/{len(threads)}: {thread_id}")

            # Fetch full message content for all messages in thread
            message_ids = thread.get("message_ids", [thread_id])
            messages = []

            for msg_id in message_ids:
                logger.debug(f"Fetching full message: {msg_id}")
                msg_full = client.get_message_full(msg_id)
                messages.append(msg_full)
                total_messages += 1

            # Download attachments if enabled
            attachments_data: dict[str, dict[str, bytes]] = {}
            if download_attachments:
                for msg in messages:
                    msg_id = msg["id"]
                    attachments_data[msg_id] = {}

                    for attachment in msg.get("attachments", []):
                        attachment_id = attachment.get("attachment_id")
                        filename = attachment["filename"]

                        if attachment_id:
                            logger.info(f"Downloading attachment: {filename}")
                            try:
                                data = client.download_attachment(msg_id, attachment_id)
                                attachments_data[msg_id][filename] = data
                                total_attachments += 1
                            except Exception as e:
                                logger.warning(f"Failed to download {filename}: {e}")

            # Export to Obsidian
            try:
                note_path = exporter.export_thread(messages, attachments_data)
                exported_notes.append(str(note_path))
                logger.info(f"Exported thread to: {note_path}")
            except Exception as e:
                logger.error(f"Failed to export thread {thread_id}: {e}")
                logger.debug("Export error:", exc_info=True)

        # Output results
        results = {
            "exported_threads": len(exported_notes),
            "exported_messages": total_messages,
            "downloaded_attachments": total_attachments,
            "notes": exported_notes,
        }

        click.echo(json.dumps(results, indent=2))
        logger.info(f"Export complete: {len(exported_notes)} threads exported")

    except Exception as e:
        logger.error(f"Failed to export emails: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.debug("Full traceback:", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
