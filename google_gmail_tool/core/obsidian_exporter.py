"""Obsidian note exporter for Gmail messages.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import logging
from pathlib import Path
from typing import Any

from dateutil import parser as dateutil_parser
from slugify import slugify

logger = logging.getLogger(__name__)


class ObsidianExporter:
    """Export Gmail messages to Obsidian markdown notes."""

    def __init__(self, obsidian_root: str) -> None:
        """Initialize Obsidian exporter.

        Args:
            obsidian_root: Path to Obsidian vault root directory
        """
        self.obsidian_root = Path(obsidian_root).expanduser()
        self.emails_root = self.obsidian_root / "emails"
        logger.debug(f"Obsidian root: {self.obsidian_root}")
        logger.debug(f"Emails folder: {self.emails_root}")

    def export_thread(
        self,
        messages: list[dict[str, Any]],
        attachments_data: dict[str, dict[str, bytes]],
    ) -> Path:
        """Export a thread of messages to Obsidian.

        Args:
            messages: List of message dictionaries with full content
            attachments_data: Dict mapping message_id -> {filename -> bytes}

        Returns:
            Path to the created/updated note file

        Raises:
            Exception: If export fails
        """
        if not messages:
            raise ValueError("No messages to export")

        # Use first message for folder/file naming
        first_msg = messages[0]
        thread_id = first_msg["thread_id"]

        # Parse email date to create static timestamp
        # Use date_iso from email headers (e.g., "2025-11-17T04:32:27+00:00")
        date_iso = first_msg.get("date_iso", "")
        if date_iso:
            # Parse ISO datetime and format as YYYY-MM-DD-HHMM
            try:
                dt = dateutil_parser.parse(date_iso)
                timestamp = dt.strftime("%Y-%m-%d-%H%M")
            except Exception as e:
                logger.warning(f"Failed to parse date '{date_iso}': {e}, using thread_id")
                timestamp = thread_id[:16]  # Fallback to thread ID prefix
        else:
            logger.warning("No date_iso in message, using thread_id")
            timestamp = thread_id[:16]  # Fallback to thread ID prefix

        sender = self._extract_email_address(first_msg["from"])
        subject = first_msg["subject"]

        folder_name = f"{timestamp}-{slugify(sender)}-{slugify(subject)}"
        thread_folder = self.emails_root / folder_name

        logger.info(f"Exporting thread {thread_id} to {thread_folder}")

        # Create folder if it doesn't exist
        thread_folder.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created folder: {thread_folder}")

        # Note filename
        note_file = thread_folder / f"{folder_name}.md"

        # Check if note exists (append mode)
        existing_content = ""
        existing_message_ids = set()
        if note_file.exists():
            logger.info(f"Note exists, loading for append: {note_file}")
            existing_content = note_file.read_text(encoding="utf-8")
            existing_message_ids = self._extract_message_ids_from_note(existing_content)
            logger.debug(f"Found {len(existing_message_ids)} existing messages in note")

        # Download attachments and save to folder
        all_attachments = []
        for msg in messages:
            msg_id = msg["id"]
            if msg_id in existing_message_ids:
                logger.debug(f"Skipping existing message: {msg_id}")
                continue

            for attachment in msg.get("attachments", []):
                filename = attachment["filename"]
                attachment_id = attachment.get("attachment_id")

                if attachment_id and msg_id in attachments_data:
                    if filename in attachments_data[msg_id]:
                        # Save attachment to thread folder
                        attachment_path = thread_folder / filename
                        attachment_path.write_bytes(attachments_data[msg_id][filename])
                        logger.info(f"Saved attachment: {filename}")
                        all_attachments.append(attachment)

        # Build frontmatter (only update if new note or new messages added)
        if not existing_content or len(existing_message_ids) < len(messages):
            frontmatter = self._build_frontmatter(messages, all_attachments)

            # Build message content (only new messages)
            messages_content = []
            for i, msg in enumerate(messages, 1):
                if msg["id"] not in existing_message_ids:
                    messages_content.append(self._format_message(msg, i, len(messages)))

            # Combine: frontmatter + existing content + new messages
            if existing_content:
                # Strip old frontmatter
                content_without_frontmatter = self._strip_frontmatter(existing_content)
                full_content = (
                    frontmatter
                    + "\n\n"
                    + content_without_frontmatter
                    + "\n\n"
                    + "\n\n---\n\n".join(messages_content)
                )
            else:
                # New note
                full_content = frontmatter + "\n\n" + "\n\n---\n\n".join(messages_content)

            # Write note
            note_file.write_text(full_content, encoding="utf-8")
            logger.info(f"Wrote note: {note_file}")
        else:
            logger.info("No new messages to add to existing note")

        return note_file

    def _extract_email_address(self, from_field: str) -> str:
        """Extract email address from 'From' field.

        Args:
            from_field: From header (e.g., 'Name <email@example.com>')

        Returns:
            Email address part only
        """
        import re

        match = re.search(r"<(.+?)>", from_field)
        if match:
            return match.group(1)
        return from_field.split()[0] if from_field else "unknown"

    def _extract_message_ids_from_note(self, content: str) -> set[str]:
        """Extract message IDs from existing note content.

        Args:
            content: Existing note content

        Returns:
            Set of message IDs found in the note
        """
        import re

        # Look for message_id in frontmatter and message sections
        ids = set(re.findall(r"message_id:\s*(\S+)", content))
        ids.update(re.findall(r"Message ID:\s*`(\S+)`", content))
        return ids

    def _strip_frontmatter(self, content: str) -> str:
        """Remove frontmatter from existing content.

        Args:
            content: Note content with frontmatter

        Returns:
            Content without frontmatter
        """
        lines = content.split("\n")
        if lines and lines[0] == "---":
            # Find end of frontmatter
            for i, line in enumerate(lines[1:], 1):
                if line == "---":
                    return "\n".join(lines[i + 1 :]).lstrip()
        return content

    def _build_frontmatter(
        self, messages: list[dict[str, Any]], attachments: list[dict[str, Any]]
    ) -> str:
        """Build YAML frontmatter for Obsidian note.

        Args:
            messages: List of message dictionaries
            attachments: List of attachment metadata

        Returns:
            Frontmatter as YAML string
        """
        first_msg = messages[0]

        # Extract Gmail labels as tags
        all_labels = set()
        for msg in messages:
            all_labels.update(msg.get("labels", []))

        # Convert labels to Obsidian-friendly tags
        tags = ["email"]
        for label in sorted(all_labels):
            tag = label.lower().replace("_", "-")
            if tag not in ["unread", "inbox", "sent", "category-promotions", "category-updates"]:
                tags.append(f"gmail/{tag}")

        # Build frontmatter
        fm_lines = ["---"]
        fm_lines.append(f'subject: "{self._escape_yaml(first_msg["subject"])}"')
        fm_lines.append(f'from: "{self._escape_yaml(first_msg["from"])}"')
        fm_lines.append(f'to: "{self._escape_yaml(first_msg["to"])}"')

        if first_msg.get("cc"):
            fm_lines.append(f'cc: "{self._escape_yaml(first_msg["cc"])}"')
        if first_msg.get("bcc"):
            fm_lines.append(f'bcc: "{self._escape_yaml(first_msg["bcc"])}"')

        fm_lines.append(f'date: "{first_msg["date_iso"]}"')
        fm_lines.append(f'thread_id: "{first_msg["thread_id"]}"')
        fm_lines.append(f"message_count: {len(messages)}")

        # Message IDs
        fm_lines.append("message_ids:")
        for msg in messages:
            fm_lines.append(f'  - "{msg["id"]}"')

        # Tags
        fm_lines.append("tags:")
        for tag in tags:
            fm_lines.append(f"  - {tag}")

        # Attachments
        if attachments:
            fm_lines.append("attachments:")
            for att in attachments:
                fm_lines.append(f'  - filename: "{att["filename"]}"')
                fm_lines.append(f"    size: {att['size']}")
                fm_lines.append(f'    mime_type: "{att["mime_type"]}"')

        fm_lines.append("---")

        return "\n".join(fm_lines)

    def _format_message(self, msg: dict[str, Any], index: int, total: int) -> str:
        """Format a single message as markdown.

        Args:
            msg: Message dictionary
            index: Message number in thread
            total: Total messages in thread

        Returns:
            Formatted message content
        """
        lines = []

        # Header
        lines.append(f"# Message {index}/{total}")
        lines.append("")
        lines.append(f"**From:** {msg['from']}")
        lines.append(f"**To:** {msg['to']}")

        if msg.get("cc"):
            lines.append(f"**CC:** {msg['cc']}")

        lines.append(f"**Date:** {msg['date_iso']}")
        lines.append(f"**Message ID:** `{msg['id']}`")

        if msg.get("in_reply_to"):
            lines.append(f"**In-Reply-To:** `{msg['in_reply_to']}`")

        # Attachments
        if msg.get("attachments"):
            lines.append("")
            lines.append("**Attachments:**")
            for att in msg["attachments"]:
                size_kb = att["size"] / 1024
                lines.append(f"- [[{att['filename']}]] ({size_kb:.1f} KB, {att['mime_type']})")

        # Body
        lines.append("")
        lines.append("## Message Body")
        lines.append("")
        lines.append(msg.get("body_markdown", msg.get("body_plain", "(No content)")))

        return "\n".join(lines)

    def _escape_yaml(self, text: str) -> str:
        """Escape special characters for YAML.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for YAML values
        """
        return text.replace('"', '\\"').replace("\n", " ").replace("\r", "")
