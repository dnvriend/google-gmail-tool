"""Obsidian calendar exporter with smart merge logic.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ObsidianCalendarExporter:
    """Export calendar events to Obsidian daily notes with smart merge."""

    def __init__(self, obsidian_root: str) -> None:
        """Initialize Obsidian calendar exporter.

        Args:
            obsidian_root: Path to Obsidian vault root directory
        """
        self.obsidian_root = Path(obsidian_root).expanduser()
        self.daily_root = self.obsidian_root / "daily"
        logger.debug(f"Obsidian root: {self.obsidian_root}")
        logger.debug(f"Daily notes folder: {self.daily_root}")

    def export_events_to_daily(
        self,
        events: list[dict[str, Any]],
        target_date: datetime,
    ) -> Path:
        """Export calendar events to daily note with smart merge.

        Args:
            events: List of event dictionaries from Calendar API
            target_date: Date for the daily note

        Returns:
            Path to the created/updated daily note file

        Raises:
            Exception: If export fails
        """
        logger.info(f"Exporting {len(events)} events to daily note: {target_date.date()}")

        # Build daily note path: daily/YYYY/YYYY-MM/YYYY-MM-DD.md
        year = target_date.strftime("%Y")
        year_month = target_date.strftime("%Y-%m")
        date_str = target_date.strftime("%Y-%m-%d")

        note_dir = self.daily_root / year / year_month
        note_dir.mkdir(parents=True, exist_ok=True)

        note_file = note_dir / f"{date_str}.md"
        logger.debug(f"Daily note path: {note_file}")

        # Load existing note if present
        existing_content = ""
        existing_calendar_section = ""
        if note_file.exists():
            logger.info("Daily note exists, loading for smart merge")
            existing_content = note_file.read_text(encoding="utf-8")
            existing_calendar_section = self._extract_calendar_section(existing_content)

        # Parse existing checked items
        checked_items = self._parse_checked_items(existing_calendar_section)
        logger.debug(f"Found {len(checked_items)} checked items in existing note")

        # Build new calendar section with smart merge
        new_calendar_section = self._build_calendar_section(events, checked_items)

        # Build full note content
        if existing_content:
            # Replace calendar section in existing content
            full_content = self._replace_calendar_section(existing_content, new_calendar_section)
        else:
            # Create new daily note with frontmatter
            frontmatter = self._build_frontmatter(target_date)
            full_content = f"{frontmatter}\n\n# {date_str}\n\n{new_calendar_section}"

        # Write note
        note_file.write_text(full_content, encoding="utf-8")
        logger.info(f"Exported to: {note_file}")

        return note_file

    def _extract_calendar_section(self, content: str) -> str:
        """Extract ## Calendar section from note content.

        Args:
            content: Full note content

        Returns:
            Calendar section content (including ## Calendar header) or empty string
        """
        # Find ## Calendar section
        match = re.search(r"^## Calendar\s*$", content, re.MULTILINE)
        if not match:
            return ""

        start = match.start()

        # Find next ## heading or end of file
        next_match = re.search(r"^## ", content[match.end() :], re.MULTILINE)
        if next_match:
            end = match.end() + next_match.start()
        else:
            end = len(content)

        return content[start:end].strip()

    def _parse_checked_items(self, calendar_section: str) -> dict[str, bool]:
        """Parse checked items from calendar section.

        Args:
            calendar_section: Calendar section content

        Returns:
            Dict mapping event signature (time + title) to checked status
            Example: {"09:00-10:00 Team Standup": True}
        """
        checked_items = {}

        # Match checklist items: - [ ] or - [x]
        pattern = r"^- \[([ x])\] (.+)$"

        for line in calendar_section.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                is_checked = match.group(1) == "x"
                item_text = match.group(2).strip()

                # Extract time and title (before @ if location present)
                signature = item_text.split(" @ ")[0].strip()
                checked_items[signature] = is_checked

        return checked_items

    def _build_calendar_section(
        self,
        events: list[dict[str, Any]],
        checked_items: dict[str, bool],
    ) -> str:
        """Build calendar section with smart merge logic.

        Args:
            events: List of calendar events
            checked_items: Dict of previously checked items

        Returns:
            Formatted calendar section as markdown
        """
        lines = ["## Calendar"]

        if not events:
            lines.append("- No events scheduled")
            return "\n".join(lines)

        for event in events:
            # Format event as checklist item
            item_text = self._format_event_checklist(event)

            # Extract signature (time + title)
            signature = item_text.split(" @ ")[0].strip()

            # Check if this event was previously checked
            if checked_items.get(signature, False):
                check_mark = "x"
                logger.debug(f"Preserving checked status for: {signature}")
            else:
                check_mark = " "

            lines.append(f"- [{check_mark}] {item_text}")

        return "\n".join(lines)

    def _format_event_checklist(self, event: dict[str, Any]) -> str:
        """Format single event as checklist item text.

        Args:
            event: Event dictionary

        Returns:
            Checklist item text (without - [ ] prefix)
            Example: "09:00-10:00 Team Standup @ Zoom"
        """
        summary = event.get("summary", "(No title)")

        if event.get("is_all_day"):
            # All-day event
            item = f"All day: {summary}"
        else:
            # Timed event: extract HH:MM
            start = event.get("start", "")
            end = event.get("end", "")
            start_time = start[11:16] if len(start) > 16 else start
            end_time = end[11:16] if len(end) > 16 else end
            item = f"{start_time}-{end_time} {summary}"

        # Add location if present
        location = event.get("location")
        if location:
            item = f"{item} @ {location}"

        return item

    def _replace_calendar_section(self, content: str, new_calendar_section: str) -> str:
        """Replace ## Calendar section in existing content.

        Args:
            content: Full note content
            new_calendar_section: New calendar section to insert

        Returns:
            Updated note content
        """
        # Find ## Calendar section
        match = re.search(r"^## Calendar\s*$", content, re.MULTILINE)

        if not match:
            # No calendar section exists, append it
            logger.debug("No existing calendar section, appending")
            return content.rstrip() + "\n\n" + new_calendar_section + "\n"

        start = match.start()

        # Find next ## heading or end of file
        next_match = re.search(r"^## ", content[match.end() :], re.MULTILINE)
        if next_match:
            end = match.end() + next_match.start()
            # Replace section, preserve content after
            return content[:start] + new_calendar_section + "\n\n" + content[end:]
        else:
            # Calendar section is last section
            return content[:start] + new_calendar_section + "\n"

    def _build_frontmatter(self, date: datetime) -> str:
        """Build YAML frontmatter for new daily note.

        Args:
            date: Date for the note

        Returns:
            Frontmatter as YAML string
        """
        date_str = date.strftime("%Y-%m-%d")

        lines = [
            "---",
            f"date: {date_str}",
            "type: daily",
            "tags:",
            "  - daily",
            "---",
        ]

        return "\n".join(lines)
