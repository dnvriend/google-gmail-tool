"""Gmail API client for reading and sending messages.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import base64
import logging
from email.mime.text import MIMEText
from typing import Any

import html2text
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class GmailClient:
    """Client for interacting with Gmail API."""

    def __init__(self, credentials: Credentials) -> None:
        """Initialize Gmail client.

        Args:
            credentials: OAuth2 credentials for Gmail API access
        """
        self.credentials = credentials
        self.service = build("gmail", "v1", credentials=credentials)
        logger.debug("Gmail API service initialized")

    def list_threads(
        self,
        query: str | None = None,
        max_results: int = 50,
        label_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List Gmail threads with optional filtering.

        Args:
            query: Gmail search query (e.g., "is:unread after:2025/01/01")
            max_results: Maximum number of threads to return (max 500)
            label_ids: Filter by label IDs (e.g., ["INBOX", "UNREAD"])

        Returns:
            List of thread dictionaries with full metadata

        Raises:
            Exception: If Gmail API call fails

        Example:
            >>> client = GmailClient(credentials)
            >>> threads = client.list_threads(query="is:unread", max_results=10)
            >>> for thread in threads:
            ...     print(thread["subject"], thread["from"])
        """
        logger.info(f"Listing threads: query={query}, max_results={max_results}")

        # Validate max_results
        if max_results > 500:
            logger.warning(f"max_results {max_results} exceeds Gmail API limit, capping at 500")
            max_results = 500

        # Build request parameters
        params: dict[str, Any] = {
            "userId": "me",
            "maxResults": max_results,
        }
        if query:
            params["q"] = query
            logger.debug(f"Using Gmail query: {query}")
        if label_ids:
            params["labelIds"] = label_ids
            logger.debug(f"Filtering by labels: {label_ids}")

        try:
            # List threads (IDs only)
            logger.debug("Calling Gmail API: threads().list()")
            response = self.service.users().threads().list(**params).execute()
            thread_list = response.get("threads", [])
            logger.info(f"Found {len(thread_list)} threads")

            if not thread_list:
                logger.info("No threads found matching query")
                return []

            # Fetch full thread details
            threads = []
            for i, thread_stub in enumerate(thread_list, 1):
                thread_id = thread_stub["id"]
                logger.debug(f"Fetching thread {i}/{len(thread_list)}: {thread_id}")

                thread_data = self._get_thread(thread_id)
                threads.append(thread_data)

            logger.info(f"Successfully fetched {len(threads)} threads")
            return threads

        except Exception as e:
            logger.error(f"Failed to list threads: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.debug("Full traceback:", exc_info=True)
            raise

    def list_messages(
        self,
        query: str | None = None,
        max_results: int = 50,
        label_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List Gmail messages (not grouped by thread).

        Args:
            query: Gmail search query
            max_results: Maximum number of messages to return (max 500)
            label_ids: Filter by label IDs

        Returns:
            List of message dictionaries with full metadata

        Raises:
            Exception: If Gmail API call fails
        """
        logger.info(f"Listing messages: query={query}, max_results={max_results}")

        # Validate max_results
        if max_results > 500:
            logger.warning(f"max_results {max_results} exceeds Gmail API limit, capping at 500")
            max_results = 500

        # Build request parameters
        params: dict[str, Any] = {
            "userId": "me",
            "maxResults": max_results,
        }
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids

        try:
            # List messages (IDs only)
            logger.debug("Calling Gmail API: messages().list()")
            response = self.service.users().messages().list(**params).execute()
            message_list = response.get("messages", [])
            logger.info(f"Found {len(message_list)} messages")

            if not message_list:
                logger.info("No messages found matching query")
                return []

            # Fetch full message details
            messages = []
            for i, msg_stub in enumerate(message_list, 1):
                msg_id = msg_stub["id"]
                logger.debug(f"Fetching message {i}/{len(message_list)}: {msg_id}")

                msg_data = self._get_message(msg_id)
                messages.append(msg_data)

            logger.info(f"Successfully fetched {len(messages)} messages")
            return messages

        except Exception as e:
            logger.error(f"Failed to list messages: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.debug("Full traceback:", exc_info=True)
            raise

    def _get_thread(self, thread_id: str) -> dict[str, Any]:
        """Get full thread details.

        Args:
            thread_id: Thread ID to fetch

        Returns:
            Thread dictionary with parsed metadata
        """
        logger.debug(f"Fetching thread details: {thread_id}")
        thread = self.service.users().threads().get(userId="me", id=thread_id).execute()

        # Parse thread metadata from first message
        messages = thread.get("messages", [])
        if not messages:
            logger.warning(f"Thread {thread_id} has no messages")
            return {
                "id": thread_id,
                "type": "thread",
                "subject": "",
                "from": "",
                "date": "",
                "snippet": thread.get("snippet", ""),
                "labels": [],
                "message_count": 0,
                "message_ids": [],
            }

        first_msg = messages[0]
        headers = {h["name"].lower(): h["value"] for h in first_msg["payload"]["headers"]}

        # Extract metadata
        subject = headers.get("subject", "(No Subject)")
        from_addr = headers.get("from", "")
        date_str = headers.get("date", "")
        labels = first_msg.get("labelIds", [])

        # Parse date to ISO format
        date_iso = self._parse_date(date_str) if date_str else ""

        # Collect all message IDs
        message_ids = [msg["id"] for msg in messages]

        logger.debug(f"Thread {thread_id}: subject='{subject}', messages={len(messages)}")

        return {
            "id": thread_id,
            "type": "thread",
            "subject": subject,
            "from": from_addr,
            "date": date_iso,
            "snippet": thread.get("snippet", ""),
            "labels": labels,
            "message_count": len(messages),
            "message_ids": message_ids,
        }

    def _get_message(self, message_id: str) -> dict[str, Any]:
        """Get full message details.

        Args:
            message_id: Message ID to fetch

        Returns:
            Message dictionary with parsed metadata
        """
        logger.debug(f"Fetching message details: {message_id}")
        message = self.service.users().messages().get(userId="me", id=message_id).execute()

        # Parse headers
        headers = {h["name"].lower(): h["value"] for h in message["payload"]["headers"]}

        # Extract metadata
        subject = headers.get("subject", "(No Subject)")
        from_addr = headers.get("from", "")
        to_addr = headers.get("to", "")
        date_str = headers.get("date", "")
        labels = message.get("labelIds", [])

        # Parse date
        date_iso = self._parse_date(date_str) if date_str else ""

        # Get thread ID
        thread_id = message.get("threadId", "")

        logger.debug(f"Message {message_id}: subject='{subject}'")

        return {
            "id": message_id,
            "type": "message",
            "thread_id": thread_id,
            "subject": subject,
            "from": from_addr,
            "to": to_addr,
            "date": date_iso,
            "snippet": message.get("snippet", ""),
            "labels": labels,
            "size_estimate": message.get("sizeEstimate", 0),
        }

    def _parse_date(self, date_str: str) -> str:
        """Parse email date string to ISO format.

        Args:
            date_str: Email date header value

        Returns:
            ISO formatted date string (YYYY-MM-DDTHH:MM:SSZ)
        """
        try:
            # Email dates are in RFC 2822 format
            # Example: "Mon, 15 Jan 2025 10:30:00 +0000"
            from email.utils import parsedate_to_datetime

            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return date_str

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_addr: str | None = None,
        cc: str | None = None,
        bcc: str | None = None,
        html: bool = False,
    ) -> dict[str, Any]:
        """Send an email message.

        Args:
            to: Recipient email address(es) (comma-separated for multiple)
            subject: Email subject line
            body: Email body content
            from_addr: Sender email address (defaults to authenticated user)
            cc: CC email address(es) (comma-separated for multiple)
            bcc: BCC email address(es) (comma-separated for multiple)
            html: If True, send as HTML email; if False, send as plain text

        Returns:
            Dictionary with sent message metadata (id, threadId, labelIds)

        Raises:
            Exception: If Gmail API call fails

        Example:
            >>> client = GmailClient(credentials)
            >>> result = client.send_email(
            ...     to="recipient@example.com",
            ...     subject="Test Email",
            ...     body="This is a test message"
            ... )
            >>> print(f"Sent message ID: {result['id']}")
        """
        logger.info(f"Sending email to: {to}")
        logger.debug(f"Subject: {subject}")

        try:
            # Create MIME message
            if html:
                message = MIMEText(body, "html")
            else:
                message = MIMEText(body, "plain")

            message["To"] = to
            message["Subject"] = subject

            if from_addr:
                message["From"] = from_addr
                logger.debug(f"From: {from_addr}")

            if cc:
                message["Cc"] = cc
                logger.debug(f"Cc: {cc}")

            if bcc:
                message["Bcc"] = bcc
                logger.debug(f"Bcc: {bcc}")

            # Encode message to base64url format
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            # Send via Gmail API
            logger.debug("Calling Gmail API: messages().send()")
            send_result = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            message_id = send_result.get("id", "")
            thread_id = send_result.get("threadId", "")
            labels = send_result.get("labelIds", [])

            logger.info(f"Email sent successfully: message_id={message_id}")
            logger.debug(f"Thread ID: {thread_id}")

            return {
                "id": message_id,
                "thread_id": thread_id,
                "labels": labels,
                "to": to,
                "subject": subject,
            }

        except Exception as e:
            logger.error(f"Failed to send email: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.debug("Full traceback:", exc_info=True)
            raise

    def get_message_full(self, message_id: str) -> dict[str, Any]:
        """Get full message details including body and attachments.

        Args:
            message_id: Message ID to fetch

        Returns:
            Dictionary with complete message data including:
            - All headers and metadata
            - Body content (plain text and/or HTML)
            - Attachment metadata (filename, mime type, size, attachment_id)

        Raises:
            Exception: If Gmail API call fails
        """
        logger.debug(f"Fetching full message: {message_id}")
        message = (
            self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
        )

        # Parse headers
        headers = {h["name"].lower(): h["value"] for h in message["payload"]["headers"]}

        # Extract body parts
        body_plain = ""
        body_html = ""
        attachments: list[dict[str, Any]] = []

        body_plain_list: list[str] = []
        body_html_list: list[str] = []
        self._extract_message_parts(
            message["payload"], body_plain_list, body_html_list, attachments
        )

        body_plain = "".join(body_plain_list)
        body_html = "".join(body_html_list)

        # Convert HTML to markdown if no plain text available
        body_markdown = ""
        if body_html:
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.ignore_emphasis = False
            h.body_width = 0  # Don't wrap text
            body_markdown = h.handle(body_html)
        elif body_plain:
            body_markdown = body_plain

        logger.debug(
            f"Message {message_id}: body_plain={len(body_plain)} chars, "
            f"body_html={len(body_html)} chars, attachments={len(attachments)}"
        )

        return {
            "id": message_id,
            "thread_id": message.get("threadId", ""),
            "subject": headers.get("subject", "(No Subject)"),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "cc": headers.get("cc", ""),
            "bcc": headers.get("bcc", ""),
            "date": headers.get("date", ""),
            "date_iso": self._parse_date(headers.get("date", "")) if headers.get("date") else "",
            "in_reply_to": headers.get("in-reply-to", ""),
            "references": headers.get("references", ""),
            "labels": message.get("labelIds", []),
            "snippet": message.get("snippet", ""),
            "body_plain": body_plain,
            "body_html": body_html,
            "body_markdown": body_markdown,
            "attachments": attachments,
            "size_estimate": message.get("sizeEstimate", 0),
        }

    def _extract_message_parts(
        self,
        payload: dict[str, Any],
        body_plain_list: list[str],
        body_html_list: list[str],
        attachments: list[dict[str, Any]],
    ) -> None:
        """Recursively extract body parts and attachments from message payload.

        Args:
            payload: Message payload from Gmail API
            body_plain_list: Accumulator for plain text body parts
            body_html_list: Accumulator for HTML body parts
            attachments: Accumulator for attachment metadata
        """
        mime_type = payload.get("mimeType", "")
        filename = payload.get("filename", "")

        # Handle attachments
        if filename:
            body = payload.get("body", {})
            attachment_id = body.get("attachmentId")
            size = body.get("size", 0)

            attachments.append(
                {
                    "filename": filename,
                    "mime_type": mime_type,
                    "size": size,
                    "attachment_id": attachment_id,
                }
            )
            logger.debug(f"Found attachment: {filename} ({mime_type}, {size} bytes)")
            return

        # Extract body content
        if mime_type == "text/plain":
            body = payload.get("body", {})
            data = body.get("data")
            if data:
                try:
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    body_plain_list.append(decoded)
                    logger.debug(f"Extracted plain text: {len(decoded)} chars")
                except Exception as e:
                    logger.warning(f"Failed to decode plain text part: {e}")

        elif mime_type == "text/html":
            body = payload.get("body", {})
            data = body.get("data")
            if data:
                try:
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    body_html_list.append(decoded)
                    logger.debug(f"Extracted HTML: {len(decoded)} chars")
                except Exception as e:
                    logger.warning(f"Failed to decode HTML part: {e}")

        # Recurse into multipart messages
        parts = payload.get("parts", [])
        for part in parts:
            self._extract_message_parts(part, body_plain_list, body_html_list, attachments)

    def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download an email attachment.

        Args:
            message_id: Message ID containing the attachment
            attachment_id: Attachment ID to download

        Returns:
            Raw attachment data as bytes

        Raises:
            Exception: If Gmail API call fails
        """
        logger.debug(f"Downloading attachment: {attachment_id} from message {message_id}")

        try:
            attachment = (
                self.service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=attachment_id)
                .execute()
            )

            data = attachment.get("data")
            if not data:
                raise ValueError(f"No data in attachment {attachment_id}")

            # Decode from base64url
            file_data = base64.urlsafe_b64decode(data)
            logger.debug(f"Downloaded {len(file_data)} bytes")

            return file_data

        except Exception as e:
            logger.error(f"Failed to download attachment: {type(e).__name__}")
            logger.error(f"Error: {str(e)}")
            logger.debug("Full traceback:", exc_info=True)
            raise
