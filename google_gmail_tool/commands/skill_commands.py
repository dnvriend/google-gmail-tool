"""CLI-as-Skill commands for agent discovery and knowledge base management.

This module implements the CLI-as-Skill pattern by providing commands that enable
AI agents to discover tool capabilities through semantic search across all CLI tools.

Design Pattern: Tool Composition
This implementation delegates RAG operations to gemini-file-search-tool rather than
embedding RAG functionality directly. This keeps the CLI lean and follows the
composition-over-inheritance principle.

Architecture:
- skill query: Semantic search across agentic-toolchain-kb RAG store
- skill index: Index this tool's help documentation into the shared RAG

References:
- CLI-as-Skill Hybrid System: /obsidian/cli-as-skill-hybrid-system.md
- Tool Composition Pattern: Delegate to gemini-file-search-tool for RAG ops

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
import os
import subprocess  # nosec B404
import sys
import tempfile
from io import StringIO
from pathlib import Path
from typing import Any

import click

from google_gmail_tool.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Shared RAG store name for all CLI tools (Agentic Toolchain Knowledge Base)
AGENTIC_TOOLCHAIN_KB = "agentic-toolchain-kb"


@click.group()
def skill() -> None:
    """Skill commands for AI agent discovery and cross-tool semantic search.

    \b
    The skill commands implement the CLI-as-Skill pattern, enabling AI agents to:
        1. Discover tool capabilities through semantic search
        2. Query help across all indexed CLI tools
        3. Learn from execution traces and tool compositions

    This CLI delegates RAG operations to gemini-file-search-tool for efficiency.

    \b
    Architecture:
        google-gmail-tool (this CLI)
            ↓ (delegates RAG ops)
        gemini-file-search-tool (specialized RAG handler)
            ↓ (manages)
        agentic-toolchain-kb (shared knowledge base)

    \b
    Examples:
        \b
        # Query across all CLI tools
        google-gmail-tool skill query "upload file to cloud storage"

        \b
        # Index this tool's help
        google-gmail-tool skill index

    \b
    Prerequisites:
        - gemini-file-search-tool must be installed
        - GEMINI_API_KEY environment variable must be set

    \b
    See Also:
        gemini-file-search-tool --help  # RAG tool documentation
    """
    pass


@skill.command("query")
@click.argument("query_text")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (can be repeated: -v INFO, -vv DEBUG)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "text"]),
    default="json",
    help="Output format (json or text)",
)
@click.option(
    "--text",
    "use_text",
    is_flag=True,
    help="Shortcut for --format text",
)
def skill_query(query_text: str, verbose: int, output_format: str, use_text: bool) -> None:
    """Query the agentic toolchain knowledge base for relevant commands.

    This command provides semantic search across all CLI tools indexed in the
    shared agentic-toolchain-kb RAG store. It delegates to gemini-file-search-tool
    for RAG operations, keeping this CLI lean and focused.

    The query returns:
    - Relevant help documentation from all CLI tools
    - Real-world execution traces (if available)
    - Tool composition patterns
    - Grounding metadata with file:line references

    \b
    Examples:

        \b
        # Find authentication commands
        google-gmail-tool skill query "authenticate with OAuth"

        \b
        # Discover deployment workflows
        google-gmail-tool skill query "deploy to production"

        \b
        # Find file operations
        google-gmail-tool skill query "upload files recursively"

        \b
        # Text output for humans
        google-gmail-tool skill query "send email" --text

    \b
    Output Format:
        JSON with structure:
        {
            "response_text": "Relevant commands and documentation",
            "grounding_metadata": {
                "grounding_chunks": [
                    {"file_path": "...", "line_number": ...}
                ]
            }
        }

    \b
    Agent Usage Pattern:
        1. Agent queries: google-gmail-tool skill query "user intent"
        2. RAG returns: Relevant commands from all tools
        3. Agent reads: <tool> <command> --help for details
        4. Agent executes: Constructed command
        5. Agent records: Successful execution trace (optional)

    \b
    Prerequisites:
        - gemini-file-search-tool installed: pip install gemini-file-search-tool
        - GEMINI_API_KEY environment variable set
        - At least one CLI tool indexed (run: google-gmail-tool skill index)

    \b
    Exit Codes:
        0 - Success
        1 - Error (gemini-file-search-tool not found, API error, etc.)
        2 - No GEMINI_API_KEY set
    """
    setup_logging(verbose)
    logger.info(f"Querying agentic toolchain KB: '{query_text}'")

    # Use text format if --text flag is set
    if use_text:
        output_format = "text"

    # Check for GEMINI_API_KEY
    if not os.getenv("GEMINI_API_KEY"):
        click.echo(
            "Error: GEMINI_API_KEY environment variable not set.\n"
            "Please set it with: export GEMINI_API_KEY='your-api-key'",
            err=True,
        )
        sys.exit(2)

    try:
        # Delegate to gemini-file-search-tool for RAG query
        logger.debug(
            f"Calling gemini-file-search-tool query '{query_text}' --store {AGENTIC_TOOLCHAIN_KB}"
        )

        result = subprocess.run(  # nosec B603 B607
            [
                "gemini-file-search-tool",
                "query",
                query_text,
                "--store",
                AGENTIC_TOOLCHAIN_KB,
                "--query-grounding-metadata",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if output_format == "json":
            # Pass through JSON response
            print(result.stdout)
        else:
            # Format for human readability
            try:
                data = json.loads(result.stdout)
                _format_query_results_text(data, query_text)
            except json.JSONDecodeError:
                # Fallback: print raw output
                print(result.stdout)

        logger.info("Query completed successfully")

    except FileNotFoundError:
        click.echo(
            "Error: gemini-file-search-tool not found.\n\n"
            "Please install it with:\n"
            "  pip install gemini-file-search-tool\n\n"
            "Or see: https://pypi.org/project/gemini-file-search-tool/",
            err=True,
        )
        sys.exit(1)

    except subprocess.CalledProcessError as e:
        logger.error(f"gemini-file-search-tool query failed: {e.stderr}")
        click.echo(f"Error querying RAG store: {e.stderr}", err=True)
        sys.exit(1)


@skill.command("index")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (can be repeated: -v INFO, -vv DEBUG)",
)
def skill_index(verbose: int) -> None:
    """Index this tool's help documentation into the agentic toolchain knowledge base.

    This command extracts all help text from google-gmail-tool and indexes it into
    the shared agentic-toolchain-kb RAG store. This enables cross-tool semantic
    search and agent discovery.

    The indexing includes:
    - Root --help (tool overview)
    - Command --help (all command groups)
    - Subcommand --help (all commands within groups)
    - Examples and usage patterns
    - Output format specifications

    \b
    Indexing Strategy:
        - Hierarchical: Root → Command Group → Command
        - Preserves line structure for accurate grounding
        - Includes all inline examples and use cases
        - Maintains cross-references between commands

    \b
    Examples:

        \b
        # Basic indexing
        google-gmail-tool skill index

        \b
        # With verbose output
        google-gmail-tool skill index -v

        \b
        # With debug logging
        google-gmail-tool skill index -vv

    \b
    What Gets Indexed:
        - google-gmail-tool --help (root)
        - google-gmail-tool auth --help
        - google-gmail-tool mail --help
        - google-gmail-tool calendar --help
        - google-gmail-tool task --help
        - google-gmail-tool drive --help
        - All subcommands within each group

    \b
    When to Re-Index:
        - After tool updates
        - When new commands are added
        - When help documentation changes
        - Periodically (e.g., on install/upgrade)

    \b
    Storage Location:
        ~/.local/share/cli-skills/agentic-toolchain-kb

    \b
    Prerequisites:
        - gemini-file-search-tool installed
        - GEMINI_API_KEY environment variable set
        - Write access to ~/.local/share/cli-skills/

    \b
    Exit Codes:
        0 - Success (indexed successfully)
        1 - Error (gemini-file-search-tool not found, API error)
        2 - No GEMINI_API_KEY set
    """
    setup_logging(verbose)
    logger.info("Indexing google-gmail-tool help into agentic-toolchain-kb")

    # Check for GEMINI_API_KEY
    if not os.getenv("GEMINI_API_KEY"):
        click.echo(
            "Error: GEMINI_API_KEY environment variable not set.\n"
            "Please set it with: export GEMINI_API_KEY='your-api-key'",
            err=True,
        )
        sys.exit(2)

    try:
        # Capture all help text
        help_text = _capture_all_help_text()
        logger.debug(f"Captured {len(help_text)} characters of help text")

        # Write to temporary file for indexing
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, prefix="google-gmail-tool-help-"
        ) as f:
            f.write(help_text)
            temp_path = f.name

        logger.debug(f"Wrote help text to temporary file: {temp_path}")

        try:
            # Delegate to gemini-file-search-tool for indexing
            logger.debug(
                f"Calling gemini-file-search-tool upload {temp_path} --store {AGENTIC_TOOLCHAIN_KB}"
            )

            result = subprocess.run(  # nosec B603 B607
                [
                    "gemini-file-search-tool",
                    "upload",
                    temp_path,
                    "--store",
                    AGENTIC_TOOLCHAIN_KB,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            click.echo(f"✓ Indexed 'google-gmail-tool' help into {AGENTIC_TOOLCHAIN_KB}")
            if verbose:
                click.echo(result.stdout, err=True)

            logger.info("Indexing completed successfully")

        finally:
            # Clean up temporary file
            Path(temp_path).unlink(missing_ok=True)
            logger.debug(f"Removed temporary file: {temp_path}")

    except FileNotFoundError:
        click.echo(
            "Error: gemini-file-search-tool not found.\n\n"
            "Please install it with:\n"
            "  pip install gemini-file-search-tool\n\n"
            "Or see: https://pypi.org/project/gemini-file-search-tool/",
            err=True,
        )
        sys.exit(1)

    except subprocess.CalledProcessError as e:
        logger.error(f"gemini-file-search-tool index failed: {e.stderr}")
        click.echo(f"Error indexing help text: {e.stderr}", err=True)
        sys.exit(1)


def _capture_all_help_text() -> str:
    """Capture all help text from google-gmail-tool commands.

    Returns:
        String containing all help text formatted for indexing
    """
    help_buffer = StringIO()

    # Import main CLI
    from google_gmail_tool.cli import main

    # Get root help
    ctx = click.Context(main)
    help_buffer.write("# google-gmail-tool\n\n")
    help_buffer.write(main.get_help(ctx))
    help_buffer.write("\n\n")

    # Get help for each command group
    for group_name in ["auth", "completion", "mail", "calendar", "task", "drive"]:
        if group_name in main.commands:
            group = main.commands[group_name]
            group_ctx = click.Context(group, info_name=group_name, parent=ctx)

            help_buffer.write(f"# google-gmail-tool {group_name}\n\n")
            help_buffer.write(group.get_help(group_ctx))
            help_buffer.write("\n\n")

            # Get help for each command in the group
            if hasattr(group, "commands"):
                for cmd_name, cmd in group.commands.items():
                    cmd_ctx = click.Context(cmd, info_name=cmd_name, parent=group_ctx)

                    help_buffer.write(f"# google-gmail-tool {group_name} {cmd_name}\n\n")
                    help_buffer.write(cmd.get_help(cmd_ctx))
                    help_buffer.write("\n\n")

    return help_buffer.getvalue()


def _format_query_results_text(data: dict[str, Any], query: str) -> None:
    """Format query results for human-readable text output.

    Args:
        data: JSON response from gemini-file-search-tool
        query: Original query text
    """
    click.echo(f"Query: {query}\n")
    click.echo("=" * 80)

    # Main response text
    response_text = data.get("response_text", "")
    if response_text:
        click.echo(f"\n{response_text}\n")

    # Grounding metadata (if available)
    grounding = data.get("grounding_metadata", {})
    chunks = grounding.get("grounding_chunks", [])

    if chunks:
        click.echo("=" * 80)
        click.echo(f"\nSources ({len(chunks)} references):\n")

        for i, chunk in enumerate(chunks[:5], 1):  # Show top 5 references
            # Extract file path and line info
            file_path = chunk.get("file_path", "unknown")
            start_line = chunk.get("start_line", 0)
            end_line = chunk.get("end_line", 0)

            # Format source reference
            if start_line and end_line:
                click.echo(f"  {i}. {file_path}:{start_line}-{end_line}")
            else:
                click.echo(f"  {i}. {file_path}")

    click.echo()
