"""Export Google Tasks to Obsidian daily notes with smart merge.

This module handles exporting tasks from Google Tasks API to Obsidian daily notes
with intelligent merging that preserves user-checked items while updating task details.

Key Responsibilities:
- Export tasks to daily notes organized by due date sections
- Smart merge: preserve checked status of existing tasks
- Section management: Overdue, Today, Tomorrow, This Week, No Due Date
- Integration with calendar section (separate ## Tasks section)
- YAML frontmatter management for daily notes
- Markdown formatting with task metadata (due date, notes)

Smart Merge Logic:
- Parse existing ## Tasks section to identify checked items by task signature
- Task signature: "Task Title (due: YYYY-MM-DD)" for unique identification
- Preserve checked status when task title/due date match existing entry
- Add new tasks as unchecked items
- Remove tasks that no longer exist in Google Tasks
- Update task notes/metadata if changed

Section Organization:
- ### Overdue: Tasks past due date
- ### Today: Tasks due today
- ### Tomorrow: Tasks due tomorrow
- ### This Week: Tasks due within 7 days
- ### No Due Date: Tasks without due date

Output Format:
- Checklist items: - [ ] Task Title (due: YYYY-MM-DD)
- Task notes as indented content below checklist
- Separate from ## Calendar section
- Daily notes: $OBSIDIAN_ROOT/daily/YYYY/YYYY-MM/YYYY-MM-DD.md

Usage Example:
    ```python
    from google_gmail_tool.core.obsidian_task_exporter import ObsidianTaskExporter
    from datetime import datetime

    exporter = ObsidianTaskExporter("/path/to/obsidian/vault")

    tasks = [
        {
            "id": "task-1",
            "title": "Review PR #123",
            "due": "2025-11-20T00:00:00.000Z",
            "notes": "Check code quality",
            "status": "needsAction"
        }
    ]

    note_path = exporter.export_tasks_to_daily(tasks, datetime(2025, 11, 20))
    ```

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ObsidianTaskExporter:
    """Export Google Tasks to Obsidian daily notes with smart merge."""

    def __init__(self, obsidian_root: str) -> None:
        """Initialize Obsidian task exporter.

        Args:
            obsidian_root: Path to Obsidian vault root directory
        """
        self.obsidian_root = Path(obsidian_root)
        logger.debug(f"Initialized ObsidianTaskExporter with root: {self.obsidian_root}")

    def export_tasks_to_daily(
        self,
        tasks: list[dict[str, Any]],
        target_date: datetime,
    ) -> Path:
        """Export tasks to daily note with smart merge.

        Args:
            tasks: List of task dictionaries from TaskClient
            target_date: Date for the daily note

        Returns:
            Path to the created/updated daily note
        """
        logger.info(f"Exporting {len(tasks)} tasks to daily note: {target_date.date()}")

        # Create daily note path
        note_path = self._get_daily_note_path(target_date)
        note_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing note if it exists
        existing_content = ""
        if note_path.exists():
            existing_content = note_path.read_text()
            logger.debug(f"Read existing note: {len(existing_content)} characters")

        # Parse existing tasks section
        checked_items = self._parse_checked_items(existing_content)
        logger.debug(f"Found {len(checked_items)} checked items in existing note")

        # Categorize tasks by due date relative to target_date
        categorized = self._categorize_tasks(tasks, target_date)

        # Build new tasks section
        tasks_section = self._build_tasks_section(categorized, checked_items)

        # Merge with existing content
        new_content = self._merge_content(existing_content, tasks_section, target_date)

        # Write to file
        note_path.write_text(new_content)
        logger.info(f"Exported tasks to: {note_path}")

        return note_path

    def _get_daily_note_path(self, date: datetime) -> Path:
        """Get path to daily note for given date.

        Args:
            date: Date for the note

        Returns:
            Path to daily note file
        """
        year = date.strftime("%Y")
        year_month = date.strftime("%Y-%m")
        date_str = date.strftime("%Y-%m-%d")

        return self.obsidian_root / "daily" / year / year_month / f"{date_str}.md"

    def _parse_checked_items(self, content: str) -> dict[str, bool]:
        """Parse existing tasks section to find checked items.

        Args:
            content: Full note content

        Returns:
            Dictionary mapping task signature to checked status
        """
        checked_items: dict[str, bool] = {}

        # Find ## Tasks section
        tasks_match = re.search(r"^## Tasks\s*$", content, re.MULTILINE)
        if not tasks_match:
            return checked_items

        # Extract tasks section content (until next ## or end)
        start_pos = tasks_match.end()
        next_section = re.search(r"^## ", content[start_pos:], re.MULTILINE)
        if next_section:
            tasks_content = content[start_pos : start_pos + next_section.start()]
        else:
            tasks_content = content[start_pos:]

        # Parse checklist items
        checklist_pattern = r"^- \[([ x])\] (.+?)(?:\n|$)"
        for match in re.finditer(checklist_pattern, tasks_content, re.MULTILINE):
            check_mark = match.group(1)
            item_text = match.group(2)

            # Extract task signature (title + due date if present)
            signature = self._extract_task_signature(item_text)
            is_checked = check_mark == "x"

            checked_items[signature] = is_checked
            logger.debug(f"Parsed task: {signature} -> checked={is_checked}")

        return checked_items

    def _extract_task_signature(self, item_text: str) -> str:
        """Extract task signature from checklist item text.

        Task signature is used to identify the same task across exports.
        Format: "Task Title (due: YYYY-MM-DD)" or just "Task Title"

        Args:
            item_text: Full checklist item text

        Returns:
            Task signature for matching
        """
        # The signature is the full text including (due: ...) if present
        return item_text.strip()

    def _categorize_tasks(
        self, tasks: list[dict[str, Any]], target_date: datetime
    ) -> dict[str, list[dict[str, Any]]]:
        """Categorize tasks by due date relative to target date.

        Args:
            tasks: List of tasks
            target_date: Reference date for categorization

        Returns:
            Dictionary with categories: overdue, today, tomorrow, this_week, no_due
        """
        categorized: dict[str, list[dict[str, Any]]] = {
            "overdue": [],
            "today": [],
            "tomorrow": [],
            "this_week": [],
            "no_due": [],
        }

        target_date_str = target_date.strftime("%Y-%m-%d")
        tomorrow_date_str = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
        week_end_date = target_date + timedelta(days=7)

        for task in tasks:
            due_str = task.get("due")

            if not due_str:
                categorized["no_due"].append(task)
                continue

            # Extract date from ISO format (YYYY-MM-DDTHH:MM:SS.sssZ)
            task_due_date_str = due_str[:10]  # Get YYYY-MM-DD
            task_due_date = datetime.strptime(task_due_date_str, "%Y-%m-%d")

            if task_due_date < target_date.replace(hour=0, minute=0, second=0, microsecond=0):
                categorized["overdue"].append(task)
            elif task_due_date_str == target_date_str:
                categorized["today"].append(task)
            elif task_due_date_str == tomorrow_date_str:
                categorized["tomorrow"].append(task)
            elif task_due_date <= week_end_date:
                categorized["this_week"].append(task)
            else:
                # Future tasks beyond a week don't appear in today's note
                pass

        return categorized

    def _build_tasks_section(
        self, categorized: dict[str, list[dict[str, Any]]], checked_items: dict[str, bool]
    ) -> str:
        """Build ## Tasks section with categorized tasks.

        Args:
            categorized: Tasks organized by category
            checked_items: Previously checked task signatures

        Returns:
            Complete ## Tasks section markdown
        """
        lines = ["## Tasks", ""]

        # Add subsections in order
        sections = [
            ("### Overdue", "overdue"),
            ("### Today", "today"),
            ("### Tomorrow", "tomorrow"),
            ("### This Week", "this_week"),
            ("### No Due Date", "no_due"),
        ]

        for section_title, category_key in sections:
            tasks_in_category = categorized[category_key]

            if not tasks_in_category:
                continue  # Skip empty sections

            lines.append(section_title)

            for task in tasks_in_category:
                # Format task checklist item
                item_text = self._format_task_checklist(task)
                signature = self._extract_task_signature(item_text)

                # Preserve checked status
                check_mark = "x" if checked_items.get(signature, False) else " "

                lines.append(f"- [{check_mark}] {item_text}")

                # Add task notes as indented content
                notes = task.get("notes")
                if notes:
                    # Indent notes under the checklist item
                    for note_line in notes.split("\n"):
                        if note_line.strip():
                            lines.append(f"  {note_line}")

            lines.append("")  # Blank line after section

        return "\n".join(lines)

    def _format_task_checklist(self, task: dict[str, Any]) -> str:
        """Format task as checklist item text.

        Args:
            task: Task dictionary

        Returns:
            Formatted checklist item text (without - [ ])
        """
        title: str = task.get("title", "(No title)")
        due = task.get("due")

        if due:
            # Extract date (YYYY-MM-DD) from ISO format
            due_date_str = due[:10]
            return f"{title} (due: {due_date_str})"
        else:
            return title

    def _merge_content(
        self, existing_content: str, tasks_section: str, target_date: datetime
    ) -> str:
        """Merge new tasks section into existing note content.

        Args:
            existing_content: Current note content
            tasks_section: New ## Tasks section
            target_date: Date for the note

        Returns:
            Complete merged note content
        """
        # If note doesn't exist, create from template
        if not existing_content:
            return self._create_note_template(target_date, tasks_section)

        # Find and replace ## Tasks section
        tasks_pattern = r"(^## Tasks\s*$)(.*?)(?=^## |\Z)"
        tasks_match = re.search(tasks_pattern, existing_content, re.MULTILINE | re.DOTALL)

        if tasks_match:
            # Replace existing ## Tasks section
            new_content = existing_content[: tasks_match.start()] + tasks_section
            # Add remaining content after ## Tasks section
            if tasks_match.end() < len(existing_content):
                new_content += "\n" + existing_content[tasks_match.end() :].lstrip()
            return new_content
        else:
            # No ## Tasks section, append at end
            return existing_content.rstrip() + "\n\n" + tasks_section

    def _create_note_template(self, date: datetime, tasks_section: str) -> str:
        """Create new daily note from template.

        Args:
            date: Date for the note
            tasks_section: ## Tasks section content

        Returns:
            Complete note content with frontmatter
        """
        date_str = date.strftime("%Y-%m-%d")

        frontmatter = f"""---
date: {date_str}
type: daily
tags:
  - daily
---

# {date_str}

"""

        return frontmatter + tasks_section
