"""Google Tasks API client for CRUD operations on tasks and task lists.

This module provides a high-level interface to the Google Tasks API (v1),
handling task list discovery, task CRUD operations (create, read, update, delete),
and task status management (complete/uncomplete). Works with the default task list only.

Key Responsibilities:
- Automatic default task list discovery via _get_default_tasklist_id()
- Task listing with filtering: completion status, due date ranges, keyword search
- Task creation with title, notes, and due date
- Task updates (partial field updates supported)
- Task status changes (complete/uncomplete via status field)
- Task deletion
- Response processing via _process_task() for consistent field extraction

API Integration:
- Uses google.auth.credentials.Credentials for OAuth2 authentication
- Builds Google Tasks API v1 service via googleapiclient.discovery.build()
- Handles RFC 3339 timestamp format for due dates (midnight UTC)
- Client-side filtering for query parameter (title/notes search)

Design Patterns:
- Composition over inheritance (wraps Tasks API service)
- Consistent error propagation (exceptions bubble up to CLI layer)
- Type-safe with strict mypy checking
- Logging at INFO (operations) and DEBUG (API details) levels

Usage Example:
    ```python
    from google_gmail_tool.core.auth import get_credentials
    from google_gmail_tool.core.task_client import TaskClient

    credentials = get_credentials()
    client = TaskClient(credentials)

    # List incomplete tasks
    tasks = client.list_tasks(completed=False)

    # Create task
    task = client.create_task(
        title="Review PR",
        notes="Check tests",
        due=datetime(2025, 11, 20)
    )

    # Complete task
    client.complete_task(task["id"])
    ```

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from google.auth.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class TaskClient:
    """Client for Google Tasks API operations."""

    def __init__(self, credentials: Credentials) -> None:
        """Initialize Tasks API client.

        Args:
            credentials: Google OAuth credentials
        """
        logger.debug("Initializing Google Tasks API client")
        self.service = build("tasks", "v1", credentials=credentials)
        logger.debug("Tasks API client initialized successfully")

    def _get_default_tasklist_id(self) -> str:
        """Get the ID of the default task list.

        Returns:
            Default task list ID

        Raises:
            Exception: If API call fails
        """
        logger.debug("Fetching default task list")
        try:
            tasklists = self.service.tasklists().list(maxResults=1).execute()
            items = tasklists.get("items", [])
            if not items:
                raise ValueError("No task lists found")
            default_id: str = items[0]["id"]
            logger.debug(f"Default task list ID: {default_id}")
            return default_id
        except Exception as e:
            logger.error(f"Failed to get default task list: {type(e).__name__}: {e}")
            raise

    def list_tasks(
        self,
        completed: bool | None = None,
        due_min: datetime | None = None,
        due_max: datetime | None = None,
        query: str | None = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """List tasks with optional filtering.

        Args:
            completed: Filter by completion status
                (None = all, True = completed, False = incomplete)
            due_min: Only tasks due after this datetime (inclusive)
            due_max: Only tasks due before this datetime (exclusive)
            query: Search query for task title and notes (client-side filtering)
            max_results: Maximum number of tasks to return (default: 100)

        Returns:
            List of task dictionaries with processed fields

        Raises:
            Exception: If API call fails
        """
        logger.info("Listing tasks")
        logger.debug(
            f"Filters - completed: {completed}, due_min: {due_min}, "
            f"due_max: {due_max}, query: {query}, max_results: {max_results}"
        )

        tasklist_id = self._get_default_tasklist_id()

        # Build API request
        request_params: dict[str, Any] = {
            "tasklist": tasklist_id,
            "maxResults": max_results,
        }

        # Show completed or incomplete tasks
        if completed is True:
            request_params["showCompleted"] = True
            request_params["showHidden"] = True
        elif completed is False:
            request_params["showCompleted"] = False

        # Due date filters
        if due_min:
            request_params["dueMin"] = due_min.isoformat() + "Z"
        if due_max:
            request_params["dueMax"] = due_max.isoformat() + "Z"

        logger.debug(f"API request params: {request_params}")

        try:
            tasks_result = self.service.tasks().list(**request_params).execute()
            tasks = tasks_result.get("items", [])

            logger.info(f"Retrieved {len(tasks)} tasks from API")

            # Process tasks
            processed_tasks = []
            for task in tasks:
                processed = self._process_task(task)

                # Client-side query filtering (search in title and notes)
                if query:
                    query_lower = query.lower()
                    title = (processed.get("title") or "").lower()
                    notes = (processed.get("notes") or "").lower()

                    if query_lower not in title and query_lower not in notes:
                        continue

                processed_tasks.append(processed)

            logger.info(f"Returning {len(processed_tasks)} tasks after filtering")
            return processed_tasks

        except Exception as e:
            logger.error(f"Failed to list tasks: {type(e).__name__}: {e}")
            raise

    def get_task(self, task_id: str) -> dict[str, Any]:
        """Get single task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task dictionary with processed fields

        Raises:
            Exception: If API call fails or task not found
        """
        logger.info(f"Fetching task: {task_id}")

        tasklist_id = self._get_default_tasklist_id()

        try:
            task = self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
            logger.info("Task retrieved successfully")
            return self._process_task(task)

        except Exception as e:
            logger.error(f"Failed to get task: {type(e).__name__}: {e}")
            raise

    def create_task(
        self,
        title: str,
        notes: str | None = None,
        due: datetime | None = None,
    ) -> dict[str, Any]:
        """Create a new task.

        Args:
            title: Task title (required)
            notes: Task notes/description
            due: Due date (date only, time ignored)

        Returns:
            Created task dictionary with processed fields

        Raises:
            Exception: If API call fails
        """
        logger.info(f"Creating task: {title}")

        tasklist_id = self._get_default_tasklist_id()

        # Build task body
        task_body: dict[str, Any] = {"title": title}

        if notes:
            task_body["notes"] = notes

        if due:
            # Google Tasks API expects RFC 3339 timestamp (midnight UTC)
            task_body["due"] = due.strftime("%Y-%m-%dT00:00:00.000Z")

        logger.debug(f"Task body: {task_body}")

        try:
            created_task = (
                self.service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()
            )

            logger.info(f"Task created successfully: {created_task['id']}")
            return self._process_task(created_task)

        except Exception as e:
            logger.error(f"Failed to create task: {type(e).__name__}: {e}")
            raise

    def update_task(
        self,
        task_id: str,
        title: str | None = None,
        notes: str | None = None,
        due: datetime | None = None,
    ) -> dict[str, Any]:
        """Update an existing task.

        Args:
            task_id: Task ID to update
            title: Optional new title
            notes: Optional new notes
            due: Optional new due date

        Returns:
            Updated task dictionary with processed fields

        Raises:
            Exception: If API call fails or task not found
        """
        logger.info(f"Updating task: {task_id}")

        tasklist_id = self._get_default_tasklist_id()

        try:
            # Fetch existing task
            existing_task = self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()

            # Update fields
            if title is not None:
                existing_task["title"] = title

            if notes is not None:
                existing_task["notes"] = notes

            if due is not None:
                existing_task["due"] = due.strftime("%Y-%m-%dT00:00:00.000Z")

            # Update task
            updated_task = (
                self.service.tasks()
                .update(tasklist=tasklist_id, task=task_id, body=existing_task)
                .execute()
            )

            logger.info(f"Task updated successfully: {task_id}")
            return self._process_task(updated_task)

        except Exception as e:
            logger.error(f"Failed to update task: {type(e).__name__}: {e}")
            raise

    def complete_task(self, task_id: str) -> dict[str, Any]:
        """Mark task as completed.

        Args:
            task_id: Task ID to complete

        Returns:
            Updated task dictionary with processed fields

        Raises:
            Exception: If API call fails or task not found
        """
        logger.info(f"Completing task: {task_id}")

        tasklist_id = self._get_default_tasklist_id()

        try:
            # Fetch existing task
            existing_task = self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()

            # Mark as completed
            existing_task["status"] = "completed"
            existing_task["completed"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

            # Update task
            updated_task = (
                self.service.tasks()
                .update(tasklist=tasklist_id, task=task_id, body=existing_task)
                .execute()
            )

            logger.info(f"Task completed successfully: {task_id}")
            return self._process_task(updated_task)

        except Exception as e:
            logger.error(f"Failed to complete task: {type(e).__name__}: {e}")
            raise

    def uncomplete_task(self, task_id: str) -> dict[str, Any]:
        """Mark task as incomplete.

        Args:
            task_id: Task ID to uncomplete

        Returns:
            Updated task dictionary with processed fields

        Raises:
            Exception: If API call fails or task not found
        """
        logger.info(f"Uncompleting task: {task_id}")

        tasklist_id = self._get_default_tasklist_id()

        try:
            # Fetch existing task
            existing_task = self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()

            # Mark as incomplete
            existing_task["status"] = "needsAction"
            if "completed" in existing_task:
                del existing_task["completed"]

            # Update task
            updated_task = (
                self.service.tasks()
                .update(tasklist=tasklist_id, task=task_id, body=existing_task)
                .execute()
            )

            logger.info(f"Task marked incomplete successfully: {task_id}")
            return self._process_task(updated_task)

        except Exception as e:
            logger.error(f"Failed to uncomplete task: {type(e).__name__}: {e}")
            raise

    def delete_task(self, task_id: str) -> None:
        """Delete a task.

        Args:
            task_id: Task ID to delete

        Raises:
            Exception: If API call fails or task not found
        """
        logger.info(f"Deleting task: {task_id}")

        tasklist_id = self._get_default_tasklist_id()

        try:
            self.service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
            logger.info(f"Task deleted successfully: {task_id}")

        except Exception as e:
            logger.error(f"Failed to delete task: {type(e).__name__}: {e}")
            raise

    def _process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Process raw task to extract key fields.

        Args:
            task: Raw task from Google Tasks API

        Returns:
            Processed task with standardized fields
        """
        processed = {
            "id": task.get("id"),
            "title": task.get("title", "(No title)"),
            "notes": task.get("notes"),
            "due": task.get("due"),
            "status": task.get("status"),
            "completed": task.get("completed"),
            "updated": task.get("updated"),
        }

        return processed
