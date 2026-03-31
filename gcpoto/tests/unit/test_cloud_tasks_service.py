"""Tests for Cloud Tasks service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.cloud_tasks import CloudTasksService
from gcpoto.models.cloud_tasks import TaskQueue, Task
from gcpoto.exceptions import ResourceNotFoundError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
QUEUE_NAME = "test-queue"
TASK_NAME = "test-task-123"

QUEUE_PATH = f"projects/{PROJECT_ID}/locations/{LOCATION}/queues/{QUEUE_NAME}"
TASK_PATH = f"{QUEUE_PATH}/tasks/{TASK_NAME}"
LOCATION_PATH = f"projects/{PROJECT_ID}/locations/{LOCATION}"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().locations().queues() chain
        mock_queues = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.queues.return_value = (
            mock_queues
        )

        # Set up projects().locations().queues().tasks() chain
        mock_tasks = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.queues.return_value.tasks.return_value = (
            mock_tasks
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a CloudTasksService with mocked client."""
    return CloudTasksService(project_id=PROJECT_ID)


@pytest.fixture
def sample_queue_response():
    """Sample Cloud Tasks queue API response."""
    return {
        "name": QUEUE_PATH,
        "state": "RUNNING",
        "rateLimits": {
            "maxDispatchesPerSecond": 500.0,
            "maxBurstSize": 100,
            "maxConcurrentDispatches": 1000,
        },
        "retryConfig": {
            "maxAttempts": 10,
            "maxRetryDuration": "3600s",
            "minBackoff": "0.100s",
            "maxBackoff": "3600s",
            "maxDoublings": 16,
        },
        "labels": {"env": "test", "team": "backend"},
    }


@pytest.fixture
def sample_task_response():
    """Sample Cloud Tasks task API response."""
    return {
        "name": TASK_PATH,
        "scheduleTime": "2026-03-31T12:00:00Z",
        "createTime": "2026-03-31T11:00:00Z",
        "dispatchDeadline": "600s",
        "dispatchCount": 3,
        "responseCount": 2,
        "firstAttempt": {
            "scheduleTime": "2026-03-31T11:00:00Z",
            "dispatchTime": "2026-03-31T11:00:01Z",
            "responseTime": "2026-03-31T11:00:02Z",
        },
        "lastAttempt": {
            "scheduleTime": "2026-03-31T11:30:00Z",
            "dispatchTime": "2026-03-31T11:30:01Z",
            "responseTime": "2026-03-31T11:30:02Z",
        },
        "httpRequest": {
            "url": "https://example.com/handler",
            "httpMethod": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": "eyJrZXkiOiAidmFsdWUifQ==",
        },
    }


@pytest.fixture
def mock_queues(mock_google_client):
    """Shortcut to mock queues resource."""
    return mock_google_client.projects.return_value.locations.return_value.queues.return_value


@pytest.fixture
def mock_tasks(mock_google_client):
    """Shortcut to mock tasks resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .queues.return_value.tasks.return_value
    )


class TestCloudTasksServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the CloudTasksService."""
        from googleapiclient.discovery import build

        svc = CloudTasksService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("cloudtasks", "v2", credentials=None)

    def test_init_with_credentials_file(self, mock_google_client):
        """Test initializing with a credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = CloudTasksService(
                project_id=PROJECT_ID, credentials_file="/path/to/creds.json"
            )
            assert svc.project_id == PROJECT_ID
            mock_creds.assert_called_once()


class TestListQueues:
    def test_list_queues(self, service, mock_queues, sample_queue_response):
        """Test listing Cloud Tasks queues."""
        mock_request = mock.MagicMock()
        mock_queues.list.return_value = mock_request
        mock_request.execute.return_value = {
            "queues": [sample_queue_response, sample_queue_response]
        }
        mock_queues.list_next.return_value = None

        queues = service.list_queues(LOCATION)

        mock_queues.list.assert_called_once_with(parent=LOCATION_PATH)
        assert len(queues) == 2
        assert isinstance(queues[0], TaskQueue)
        assert queues[0].name == QUEUE_NAME
        assert queues[0].project == PROJECT_ID
        assert queues[0].location == LOCATION
        assert queues[0].state == "RUNNING"

    def test_list_queues_empty(self, service, mock_queues):
        """Test listing queues when none exist."""
        mock_request = mock.MagicMock()
        mock_queues.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_queues.list_next.return_value = None

        queues = service.list_queues(LOCATION)

        assert len(queues) == 0

    def test_list_queues_pagination(self, service, mock_queues, sample_queue_response):
        """Test listing queues with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_queues.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "queues": [sample_queue_response]
        }

        mock_queues.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "queues": [sample_queue_response]
        }

        queues = service.list_queues(LOCATION)
        assert len(queues) == 2


class TestGetQueue:
    def test_get_queue(self, service, mock_queues, sample_queue_response):
        """Test getting a specific queue."""
        mock_request = mock.MagicMock()
        mock_queues.get.return_value = mock_request
        mock_request.execute.return_value = sample_queue_response

        queue = service.get_queue(LOCATION, QUEUE_NAME)

        mock_queues.get.assert_called_once_with(name=QUEUE_PATH)
        assert isinstance(queue, TaskQueue)
        assert queue.name == QUEUE_NAME
        assert queue.state == "RUNNING"
        assert queue.rate_limits == sample_queue_response["rateLimits"]
        assert queue.retry_config == sample_queue_response["retryConfig"]

    def test_get_queue_not_found(self, service, mock_queues):
        """Test getting a queue that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_queues.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_queue(LOCATION, QUEUE_NAME)

    def test_get_queue_with_full_path(self, service, mock_queues, sample_queue_response):
        """Test getting a queue using a full resource path."""
        mock_request = mock.MagicMock()
        mock_queues.get.return_value = mock_request
        mock_request.execute.return_value = sample_queue_response

        service.get_queue(LOCATION, QUEUE_PATH)
        mock_queues.get.assert_called_once_with(name=QUEUE_PATH)


class TestCreateQueue:
    def test_create_queue(self, service, mock_queues, sample_queue_response):
        """Test creating a new queue."""
        mock_request = mock.MagicMock()
        mock_queues.create.return_value = mock_request
        mock_request.execute.return_value = sample_queue_response

        queue = service.create_queue(
            LOCATION,
            QUEUE_NAME,
            rate_limits={"maxDispatchesPerSecond": 500.0},
            retry_config={"maxAttempts": 10},
        )

        mock_queues.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={
                "name": QUEUE_PATH,
                "rateLimits": {"maxDispatchesPerSecond": 500.0},
                "retryConfig": {"maxAttempts": 10},
            },
        )
        assert isinstance(queue, TaskQueue)
        assert queue.name == QUEUE_NAME

    def test_create_queue_minimal(self, service, mock_queues, sample_queue_response):
        """Test creating a queue with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_queues.create.return_value = mock_request
        mock_request.execute.return_value = sample_queue_response

        queue = service.create_queue(LOCATION, QUEUE_NAME)

        mock_queues.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={"name": QUEUE_PATH},
        )
        assert isinstance(queue, TaskQueue)


class TestUpdateQueue:
    def test_update_queue(self, service, mock_queues, sample_queue_response):
        """Test updating a queue."""
        mock_request = mock.MagicMock()
        mock_queues.patch.return_value = mock_request
        mock_request.execute.return_value = sample_queue_response

        update_fields = {
            "rateLimits": {"maxDispatchesPerSecond": 1000.0},
        }
        queue = service.update_queue(LOCATION, QUEUE_NAME, update_fields)

        mock_queues.patch.assert_called_once_with(
            name=QUEUE_PATH,
            body={
                "name": QUEUE_PATH,
                "rateLimits": {"maxDispatchesPerSecond": 1000.0},
            },
            updateMask="rateLimits",
        )
        assert isinstance(queue, TaskQueue)

    def test_update_queue_not_found(self, service, mock_queues):
        """Test updating a queue that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_queues.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_queue(LOCATION, QUEUE_NAME, {"state": "PAUSED"})


class TestDeleteQueue:
    def test_delete_queue(self, service, mock_queues):
        """Test deleting a queue."""
        mock_request = mock.MagicMock()
        mock_queues.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_queue(LOCATION, QUEUE_NAME)

        mock_queues.delete.assert_called_once_with(name=QUEUE_PATH)
        assert result is True

    def test_delete_queue_not_found(self, service, mock_queues):
        """Test deleting a queue that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_queues.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_queue(LOCATION, QUEUE_NAME)


class TestPauseQueue:
    def test_pause_queue(self, service, mock_queues, sample_queue_response):
        """Test pausing a queue."""
        paused_response = {**sample_queue_response, "state": "PAUSED"}
        mock_request = mock.MagicMock()
        mock_queues.pause.return_value = mock_request
        mock_request.execute.return_value = paused_response

        queue = service.pause_queue(LOCATION, QUEUE_NAME)

        mock_queues.pause.assert_called_once_with(name=QUEUE_PATH, body={})
        assert isinstance(queue, TaskQueue)
        assert queue.state == "PAUSED"

    def test_pause_queue_not_found(self, service, mock_queues):
        """Test pausing a queue that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_queues.pause.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.pause_queue(LOCATION, QUEUE_NAME)


class TestResumeQueue:
    def test_resume_queue(self, service, mock_queues, sample_queue_response):
        """Test resuming a paused queue."""
        mock_request = mock.MagicMock()
        mock_queues.resume.return_value = mock_request
        mock_request.execute.return_value = sample_queue_response

        queue = service.resume_queue(LOCATION, QUEUE_NAME)

        mock_queues.resume.assert_called_once_with(name=QUEUE_PATH, body={})
        assert isinstance(queue, TaskQueue)
        assert queue.state == "RUNNING"

    def test_resume_queue_not_found(self, service, mock_queues):
        """Test resuming a queue that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_queues.resume.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.resume_queue(LOCATION, QUEUE_NAME)


class TestPurgeQueue:
    def test_purge_queue(self, service, mock_queues, sample_queue_response):
        """Test purging a queue."""
        purged_response = {
            **sample_queue_response,
            "purgeTime": "2026-03-31T12:00:00Z",
        }
        mock_request = mock.MagicMock()
        mock_queues.purge.return_value = mock_request
        mock_request.execute.return_value = purged_response

        queue = service.purge_queue(LOCATION, QUEUE_NAME)

        mock_queues.purge.assert_called_once_with(name=QUEUE_PATH, body={})
        assert isinstance(queue, TaskQueue)

    def test_purge_queue_not_found(self, service, mock_queues):
        """Test purging a queue that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_queues.purge.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.purge_queue(LOCATION, QUEUE_NAME)


class TestListTasks:
    def test_list_tasks(self, service, mock_tasks, sample_task_response):
        """Test listing tasks in a queue."""
        mock_request = mock.MagicMock()
        mock_tasks.list.return_value = mock_request
        mock_request.execute.return_value = {
            "tasks": [sample_task_response, sample_task_response]
        }
        mock_tasks.list_next.return_value = None

        tasks = service.list_tasks(LOCATION, QUEUE_NAME)

        mock_tasks.list.assert_called_once_with(parent=QUEUE_PATH)
        assert len(tasks) == 2
        assert isinstance(tasks[0], Task)
        assert tasks[0].name == TASK_NAME
        assert tasks[0].queue_name == QUEUE_NAME
        assert tasks[0].location == LOCATION

    def test_list_tasks_empty(self, service, mock_tasks):
        """Test listing tasks when none exist."""
        mock_request = mock.MagicMock()
        mock_tasks.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_tasks.list_next.return_value = None

        tasks = service.list_tasks(LOCATION, QUEUE_NAME)
        assert len(tasks) == 0

    def test_list_tasks_pagination(self, service, mock_tasks, sample_task_response):
        """Test listing tasks with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_tasks.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "tasks": [sample_task_response]
        }

        mock_tasks.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "tasks": [sample_task_response]
        }

        tasks = service.list_tasks(LOCATION, QUEUE_NAME)
        assert len(tasks) == 2


class TestGetTask:
    def test_get_task(self, service, mock_tasks, sample_task_response):
        """Test getting a specific task."""
        mock_request = mock.MagicMock()
        mock_tasks.get.return_value = mock_request
        mock_request.execute.return_value = sample_task_response

        task = service.get_task(LOCATION, QUEUE_NAME, TASK_NAME)

        mock_tasks.get.assert_called_once_with(name=TASK_PATH)
        assert isinstance(task, Task)
        assert task.name == TASK_NAME
        assert task.queue_name == QUEUE_NAME
        assert task.dispatch_count == 3
        assert task.response_count == 2
        assert task.http_request == sample_task_response["httpRequest"]

    def test_get_task_not_found(self, service, mock_tasks):
        """Test getting a task that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_tasks.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_task(LOCATION, QUEUE_NAME, TASK_NAME)

    def test_get_task_with_full_path(self, service, mock_tasks, sample_task_response):
        """Test getting a task using a full resource path."""
        mock_request = mock.MagicMock()
        mock_tasks.get.return_value = mock_request
        mock_request.execute.return_value = sample_task_response

        service.get_task(LOCATION, QUEUE_NAME, TASK_PATH)
        mock_tasks.get.assert_called_once_with(name=TASK_PATH)


class TestCreateTask:
    def test_create_task_with_http_request(
        self, service, mock_tasks, sample_task_response
    ):
        """Test creating a task with an HTTP request."""
        mock_request = mock.MagicMock()
        mock_tasks.create.return_value = mock_request
        mock_request.execute.return_value = sample_task_response

        http_req = {
            "url": "https://example.com/handler",
            "httpMethod": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": "eyJrZXkiOiAidmFsdWUifQ==",
        }

        task = service.create_task(
            LOCATION, QUEUE_NAME, http_request=http_req
        )

        mock_tasks.create.assert_called_once_with(
            parent=QUEUE_PATH,
            body={"task": {"httpRequest": http_req}},
        )
        assert isinstance(task, Task)
        assert task.name == TASK_NAME

    def test_create_task_with_schedule_time(
        self, service, mock_tasks, sample_task_response
    ):
        """Test creating a task with a schedule time."""
        mock_request = mock.MagicMock()
        mock_tasks.create.return_value = mock_request
        mock_request.execute.return_value = sample_task_response

        schedule = "2026-03-31T15:00:00Z"
        task = service.create_task(
            LOCATION, QUEUE_NAME, schedule_time=schedule
        )

        mock_tasks.create.assert_called_once_with(
            parent=QUEUE_PATH,
            body={"task": {"scheduleTime": schedule}},
        )
        assert isinstance(task, Task)

    def test_create_task_minimal(self, service, mock_tasks, sample_task_response):
        """Test creating a task with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_tasks.create.return_value = mock_request
        mock_request.execute.return_value = sample_task_response

        task = service.create_task(LOCATION, QUEUE_NAME)

        mock_tasks.create.assert_called_once_with(
            parent=QUEUE_PATH,
            body={"task": {}},
        )
        assert isinstance(task, Task)

    def test_create_task_with_all_options(
        self, service, mock_tasks, sample_task_response
    ):
        """Test creating a task with both http_request and schedule_time."""
        mock_request = mock.MagicMock()
        mock_tasks.create.return_value = mock_request
        mock_request.execute.return_value = sample_task_response

        http_req = {"url": "https://example.com/handler", "httpMethod": "POST"}
        schedule = "2026-03-31T15:00:00Z"

        task = service.create_task(
            LOCATION,
            QUEUE_NAME,
            http_request=http_req,
            schedule_time=schedule,
        )

        mock_tasks.create.assert_called_once_with(
            parent=QUEUE_PATH,
            body={
                "task": {
                    "httpRequest": http_req,
                    "scheduleTime": schedule,
                }
            },
        )
        assert isinstance(task, Task)


class TestDeleteTask:
    def test_delete_task(self, service, mock_tasks):
        """Test deleting a task."""
        mock_request = mock.MagicMock()
        mock_tasks.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_task(LOCATION, QUEUE_NAME, TASK_NAME)

        mock_tasks.delete.assert_called_once_with(name=TASK_PATH)
        assert result is True

    def test_delete_task_not_found(self, service, mock_tasks):
        """Test deleting a task that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_tasks.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_task(LOCATION, QUEUE_NAME, TASK_NAME)


class TestRunTask:
    def test_run_task(self, service, mock_tasks, sample_task_response):
        """Test force running a task."""
        mock_request = mock.MagicMock()
        mock_tasks.run.return_value = mock_request
        mock_request.execute.return_value = sample_task_response

        task = service.run_task(LOCATION, QUEUE_NAME, TASK_NAME)

        mock_tasks.run.assert_called_once_with(name=TASK_PATH, body={})
        assert isinstance(task, Task)
        assert task.name == TASK_NAME

    def test_run_task_not_found(self, service, mock_tasks):
        """Test running a task that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_tasks.run.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.run_task(LOCATION, QUEUE_NAME, TASK_NAME)


class TestTaskQueueModel:
    def test_from_api_response(self, sample_queue_response):
        """Test creating a TaskQueue from API response."""
        queue = TaskQueue.from_api_response(sample_queue_response)

        assert queue.name == QUEUE_NAME
        assert queue.project == PROJECT_ID
        assert queue.location == LOCATION
        assert queue.state == "RUNNING"
        assert queue.rate_limits == sample_queue_response["rateLimits"]
        assert queue.retry_config == sample_queue_response["retryConfig"]
        assert queue.id == QUEUE_PATH
        assert queue.type == "cloudtasks.queue"

    def test_from_api_response_minimal(self):
        """Test creating a TaskQueue from minimal API response."""
        response = {"name": QUEUE_PATH}
        queue = TaskQueue.from_api_response(response)

        assert queue.name == QUEUE_NAME
        assert queue.state == "RUNNING"
        assert queue.rate_limits is None
        assert queue.retry_config is None

    def test_get_tag(self, sample_queue_response):
        """Test getting tags from a TaskQueue."""
        queue = TaskQueue.from_api_response(sample_queue_response)

        assert queue.get_tag("env") == "test"
        assert queue.get_tag("team") == "backend"
        assert queue.get_tag("missing") == ""
        assert queue.get_tag("missing", "default") == "default"


class TestTaskModel:
    def test_from_api_response(self, sample_task_response):
        """Test creating a Task from API response."""
        task = Task.from_api_response(sample_task_response)

        assert task.name == TASK_NAME
        assert task.project == PROJECT_ID
        assert task.location == LOCATION
        assert task.queue_name == QUEUE_NAME
        assert task.dispatch_count == 3
        assert task.response_count == 2
        assert task.dispatch_deadline == "600s"
        assert task.http_request == sample_task_response["httpRequest"]
        assert task.first_attempt == sample_task_response["firstAttempt"]
        assert task.last_attempt == sample_task_response["lastAttempt"]
        assert task.id == TASK_PATH
        assert task.type == "cloudtasks.task"

    def test_from_api_response_minimal(self):
        """Test creating a Task from minimal API response."""
        response = {"name": TASK_PATH}
        task = Task.from_api_response(response)

        assert task.name == TASK_NAME
        assert task.dispatch_count == 0
        assert task.response_count == 0
        assert task.http_request is None
        assert task.app_engine_http_request is None

    def test_from_api_response_with_app_engine_request(self):
        """Test creating a Task with App Engine HTTP request."""
        response = {
            "name": TASK_PATH,
            "appEngineHttpRequest": {
                "httpMethod": "POST",
                "relativeUri": "/handler",
                "appEngineRouting": {"service": "worker"},
            },
        }
        task = Task.from_api_response(response)

        assert task.app_engine_http_request is not None
        assert task.app_engine_http_request["httpMethod"] == "POST"
        assert task.http_request is None


class TestPathFormatting:
    def test_format_queue_path(self, service):
        """Test queue path formatting."""
        assert service._format_queue_path(LOCATION, QUEUE_NAME) == QUEUE_PATH

    def test_format_queue_path_already_formatted(self, service):
        """Test that already-formatted queue paths are returned as-is."""
        assert service._format_queue_path(LOCATION, QUEUE_PATH) == QUEUE_PATH

    def test_format_task_path(self, service):
        """Test task path formatting."""
        assert (
            service._format_task_path(LOCATION, QUEUE_NAME, TASK_NAME)
            == TASK_PATH
        )

    def test_format_task_path_already_formatted(self, service):
        """Test that already-formatted task paths are returned as-is."""
        assert (
            service._format_task_path(LOCATION, QUEUE_NAME, TASK_PATH)
            == TASK_PATH
        )

    def test_format_location_path(self, service):
        """Test location path formatting."""
        assert service._format_location_path(LOCATION) == LOCATION_PATH
