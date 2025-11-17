"""CLI entry point for google-gmail-tool.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import click

from google_gmail_tool.utils import get_greeting


@click.command()
@click.version_option(version="0.1.0")
def main() -> None:
    """A CLI that provides access to google services like mail, calendar, drive"""
    click.echo(get_greeting())


if __name__ == "__main__":
    main()
