"""Google Calendar API client.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import logging
from datetime import datetime
from typing import Any

from google.auth.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class CalendarClient:
    """Client for Google Calendar API operations."""

    def __init__(self, credentials: Credentials) -> None:
        """Initialize Calendar API client.

        Args:
            credentials: Google OAuth credentials
        """
        logger.debug("Initializing Google Calendar API client")
        self.service = build("calendar", "v3", credentials=credentials)
        logger.debug("Calendar API client initialized successfully")

    def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
        query: str | None = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """List calendar events in time range.

        Args:
            time_min: Start of time range (inclusive)
            time_max: End of time range (exclusive)
            query: Optional search query for event title/description
            max_results: Maximum number of events to return (default: 100)

        Returns:
            List of event dictionaries with processed fields

        Raises:
            Exception: If API call fails
        """
        logger.info(f"Listing events from {time_min} to {time_max}")
        logger.debug(f"Query: {query}, max_results: {max_results}")

        # Convert datetime to RFC3339 format
        time_min_rfc = time_min.isoformat() + "Z"
        time_max_rfc = time_max.isoformat() + "Z"

        # Build API request
        request_params: dict[str, Any] = {
            "calendarId": "primary",
            "timeMin": time_min_rfc,
            "timeMax": time_max_rfc,
            "maxResults": max_results,
            "singleEvents": True,  # Expand recurring events
            "orderBy": "startTime",
        }

        if query:
            request_params["q"] = query

        logger.debug(f"API request params: {request_params}")

        try:
            events_result = self.service.events().list(**request_params).execute()
            events = events_result.get("items", [])

            logger.info(f"Retrieved {len(events)} events")

            # Process events to extract key fields
            processed_events = []
            for event in events:
                processed = self._process_event(event)
                processed_events.append(processed)

            return processed_events

        except Exception as e:
            logger.error(f"Failed to list events: {type(e).__name__}: {e}")
            raise

    def get_event(self, event_id: str) -> dict[str, Any]:
        """Get single calendar event by ID.

        Args:
            event_id: Calendar event ID

        Returns:
            Event dictionary with processed fields

        Raises:
            Exception: If API call fails or event not found
        """
        logger.info(f"Fetching event: {event_id}")

        try:
            event = self.service.events().get(calendarId="primary", eventId=event_id).execute()
            logger.info("Event retrieved successfully")
            return self._process_event(event)

        except Exception as e:
            logger.error(f"Failed to get event: {type(e).__name__}: {e}")
            raise

    def _process_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Process raw event to extract key fields.

        Args:
            event: Raw event from Google Calendar API

        Returns:
            Processed event with standardized fields
        """
        # Extract start/end times
        start = event.get("start", {})
        end = event.get("end", {})

        # Handle all-day events vs timed events
        start_datetime = start.get("dateTime")
        start_date = start.get("date")
        end_datetime = end.get("dateTime")
        end_date = end.get("date")

        is_all_day = start_date is not None

        # Extract attendees
        attendees = []
        for attendee in event.get("attendees", []):
            attendees.append(
                {
                    "email": attendee.get("email"),
                    "response_status": attendee.get("responseStatus"),
                    "optional": attendee.get("optional", False),
                }
            )

        processed = {
            "id": event.get("id"),
            "summary": event.get("summary", "(No title)"),
            "description": event.get("description"),
            "location": event.get("location"),
            "start": start_datetime or start_date,
            "end": end_datetime or end_date,
            "is_all_day": is_all_day,
            "attendees": attendees,
            "created": event.get("created"),
            "updated": event.get("updated"),
            "status": event.get("status"),
            "html_link": event.get("htmlLink"),
        }

        return processed

    def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        location: str | None = None,
        description: str | None = None,
        attendees: list[str] | None = None,
        add_meet: bool = False,
        is_all_day: bool = False,
    ) -> dict[str, Any]:
        """Create a new calendar event.

        Args:
            title: Event title/summary
            start: Event start datetime (local timezone)
            end: Event end datetime (local timezone)
            location: Optional location
            description: Optional description
            attendees: Optional list of attendee email addresses
            add_meet: Whether to add Google Meet video conferencing
            is_all_day: Whether this is an all-day event

        Returns:
            Created event dictionary with processed fields

        Raises:
            Exception: If API call fails
        """
        logger.info(f"Creating event: {title}")

        # Build event body
        event_body: dict[str, Any] = {"summary": title}

        # Handle all-day vs timed events
        if is_all_day:
            # All-day events use 'date' field (YYYY-MM-DD)
            event_body["start"] = {"date": start.strftime("%Y-%m-%d")}
            event_body["end"] = {"date": end.strftime("%Y-%m-%d")}
        else:
            # Timed events use 'dateTime' field (ISO 8601)
            event_body["start"] = {"dateTime": start.isoformat(), "timeZone": "UTC"}
            event_body["end"] = {"dateTime": end.isoformat(), "timeZone": "UTC"}

        if location:
            event_body["location"] = location

        if description:
            event_body["description"] = description

        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        if add_meet:
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": f"meet-{start.isoformat()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }

        logger.debug(f"Event body: {event_body}")

        try:
            # Create event
            created_event = (
                self.service.events()
                .insert(
                    calendarId="primary",
                    body=event_body,
                    conferenceDataVersion=1 if add_meet else 0,
                )
                .execute()
            )

            logger.info(f"Event created successfully: {created_event['id']}")
            return self._process_event(created_event)

        except Exception as e:
            logger.error(f"Failed to create event: {type(e).__name__}: {e}")
            raise

    def update_event(
        self,
        event_id: str,
        title: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        location: str | None = None,
        description: str | None = None,
        attendees: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update an existing calendar event.

        Args:
            event_id: Event ID to update
            title: Optional new title
            start: Optional new start datetime
            end: Optional new end datetime
            location: Optional new location
            description: Optional new description
            attendees: Optional new list of attendees

        Returns:
            Updated event dictionary with processed fields

        Raises:
            Exception: If API call fails or event not found
        """
        logger.info(f"Updating event: {event_id}")

        try:
            # Fetch existing event
            existing_event = (
                self.service.events().get(calendarId="primary", eventId=event_id).execute()
            )

            # Update fields
            if title is not None:
                existing_event["summary"] = title

            if start is not None:
                if "date" in existing_event["start"]:
                    # All-day event
                    existing_event["start"]["date"] = start.strftime("%Y-%m-%d")
                else:
                    # Timed event
                    existing_event["start"]["dateTime"] = start.isoformat()

            if end is not None:
                if "date" in existing_event["end"]:
                    # All-day event
                    existing_event["end"]["date"] = end.strftime("%Y-%m-%d")
                else:
                    # Timed event
                    existing_event["end"]["dateTime"] = end.isoformat()

            if location is not None:
                existing_event["location"] = location

            if description is not None:
                existing_event["description"] = description

            if attendees is not None:
                existing_event["attendees"] = [{"email": email} for email in attendees]

            # Update event
            updated_event = (
                self.service.events()
                .update(calendarId="primary", eventId=event_id, body=existing_event)
                .execute()
            )

            logger.info(f"Event updated successfully: {event_id}")
            return self._process_event(updated_event)

        except Exception as e:
            logger.error(f"Failed to update event: {type(e).__name__}: {e}")
            raise

    def delete_event(self, event_id: str) -> None:
        """Delete a calendar event.

        Args:
            event_id: Event ID to delete

        Raises:
            Exception: If API call fails or event not found
        """
        logger.info(f"Deleting event: {event_id}")

        try:
            self.service.events().delete(calendarId="primary", eventId=event_id).execute()
            logger.info(f"Event deleted successfully: {event_id}")

        except Exception as e:
            logger.error(f"Failed to delete event: {type(e).__name__}: {e}")
            raise
