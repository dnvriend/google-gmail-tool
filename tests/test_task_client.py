"""Tests for TaskClient structure and method signatures.

These are structural tests that verify the TaskClient API surface
without making actual Google API calls. Full integration tests would
require mocked credentials and API responses.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from google_gmail_tool.core.task_client import TaskClient


@pytest.fixture
def mock_credentials() -> Mock:
    """Create mock Google credentials."""
    credentials = Mock()
    credentials.valid = True
    credentials.expired = False
    return credentials


@pytest.fixture
def mock_service() -> Mock:
    """Create mock Google Tasks service."""
    service = Mock()
    service.tasklists.return_value.list.return_value.execute.return_value = {
        "items": [{"id": "default-list-id", "title": "My Tasks"}]
    }
    return service


@pytest.fixture
def task_client(mock_credentials: Mock, mock_service: Mock) -> TaskClient:
    """Create TaskClient with mocked service."""
    with patch("google_gmail_tool.core.task_client.build", return_value=mock_service):
        client = TaskClient(mock_credentials)
    return client


def test_task_client_initialization(mock_credentials: Mock, mock_service: Mock) -> None:
    """Test TaskClient initializes with credentials."""
    with patch("google_gmail_tool.core.task_client.build", return_value=mock_service):
        client = TaskClient(mock_credentials)
        assert client.service == mock_service


def test_get_default_tasklist_id(task_client: TaskClient, mock_service: Mock) -> None:
    """Test _get_default_tasklist_id returns first task list ID."""
    tasklist_id = task_client._get_default_tasklist_id()
    assert tasklist_id == "default-list-id"
    mock_service.tasklists.return_value.list.assert_called_with(maxResults=1)


def test_get_default_tasklist_id_no_lists(task_client: TaskClient, mock_service: Mock) -> None:
    """Test _get_default_tasklist_id raises when no task lists exist."""
    mock_service.tasklists.return_value.list.return_value.execute.return_value = {"items": []}

    with pytest.raises(ValueError, match="No task lists found"):
        task_client._get_default_tasklist_id()


def test_list_tasks_calls_api(task_client: TaskClient, mock_service: Mock) -> None:
    """Test list_tasks calls Tasks API with correct parameters."""
    mock_service.tasks.return_value.list.return_value.execute.return_value = {"items": []}

    tasks = task_client.list_tasks(completed=False, max_results=50)

    assert tasks == []
    mock_service.tasks.return_value.list.assert_called_once()
    call_kwargs = mock_service.tasks.return_value.list.call_args.kwargs
    assert call_kwargs["tasklist"] == "default-list-id"
    assert call_kwargs["maxResults"] == 50
    assert call_kwargs["showCompleted"] is False


def test_create_task_builds_request(task_client: TaskClient, mock_service: Mock) -> None:
    """Test create_task builds correct API request."""
    mock_service.tasks.return_value.insert.return_value.execute.return_value = {
        "id": "task-123",
        "title": "Test Task",
        "status": "needsAction",
    }

    due_date = datetime(2025, 11, 20)
    task = task_client.create_task(title="Test Task", notes="Test notes", due=due_date)

    assert task["id"] == "task-123"
    assert task["title"] == "Test Task"
    mock_service.tasks.return_value.insert.assert_called_once()
    call_kwargs = mock_service.tasks.return_value.insert.call_args.kwargs
    assert call_kwargs["tasklist"] == "default-list-id"
    assert call_kwargs["body"]["title"] == "Test Task"
    assert call_kwargs["body"]["notes"] == "Test notes"
    assert "due" in call_kwargs["body"]


def test_process_task_extracts_fields() -> None:
    """Test _process_task extracts standard fields."""
    # Create a mock client without patching (just for method access)
    mock_creds = Mock()
    mock_service = Mock()
    mock_service.tasklists.return_value.list.return_value.execute.return_value = {
        "items": [{"id": "test-list"}]
    }

    with patch("google_gmail_tool.core.task_client.build", return_value=mock_service):
        client = TaskClient(mock_creds)

    raw_task = {
        "id": "task-123",
        "title": "Test Task",
        "notes": "Test notes",
        "due": "2025-11-20T00:00:00.000Z",
        "status": "needsAction",
        "updated": "2025-11-17T10:00:00.000Z",
    }

    processed = client._process_task(raw_task)

    assert processed["id"] == "task-123"
    assert processed["title"] == "Test Task"
    assert processed["notes"] == "Test notes"
    assert processed["due"] == "2025-11-20T00:00:00.000Z"
    assert processed["status"] == "needsAction"
    assert processed["updated"] == "2025-11-17T10:00:00.000Z"
    assert processed["completed"] is None


def test_complete_task_sets_status(task_client: TaskClient, mock_service: Mock) -> None:
    """Test complete_task sets status to completed."""
    mock_service.tasks.return_value.get.return_value.execute.return_value = {
        "id": "task-123",
        "title": "Test",
        "status": "needsAction",
    }
    mock_service.tasks.return_value.update.return_value.execute.return_value = {
        "id": "task-123",
        "title": "Test",
        "status": "completed",
        "completed": "2025-11-17T10:00:00.000Z",
    }

    task = task_client.complete_task("task-123")

    assert task["status"] == "completed"
    assert task["completed"] is not None
    mock_service.tasks.return_value.update.assert_called_once()
    update_body = mock_service.tasks.return_value.update.call_args.kwargs["body"]
    assert update_body["status"] == "completed"


def test_delete_task_calls_api(task_client: TaskClient, mock_service: Mock) -> None:
    """Test delete_task calls API with correct parameters."""
    task_client.delete_task("task-123")

    mock_service.tasks.return_value.delete.assert_called_once()
    call_kwargs = mock_service.tasks.return_value.delete.call_args.kwargs
    assert call_kwargs["tasklist"] == "default-list-id"
    assert call_kwargs["task"] == "task-123"
