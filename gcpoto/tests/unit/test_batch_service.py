"""Tests for Batch service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.batch import BatchService
from gcpoto.models.batch import BatchJob, BatchTask
from gcpoto.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
JOB_NAME = "test-job"
TASK_GROUP = "group0"
TASK_NAME = "0"

LOCATION_PATH = f"projects/{PROJECT_ID}/locations/{LOCATION}"
JOB_PATH = f"{LOCATION_PATH}/jobs/{JOB_NAME}"
TASK_GROUP_PATH = f"{JOB_PATH}/taskGroups/{TASK_GROUP}"
TASK_PATH = f"{TASK_GROUP_PATH}/tasks/{TASK_NAME}"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().locations().jobs() chain
        mock_jobs = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.jobs.return_value = (
            mock_jobs
        )

        # Set up projects().locations().jobs().taskGroups().tasks() chain
        mock_tasks = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.jobs.return_value.taskGroups.return_value.tasks.return_value = (
            mock_tasks
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a BatchService with mocked client."""
    return BatchService(project_id=PROJECT_ID)


@pytest.fixture
def mock_jobs(mock_google_client):
    """Shortcut to mock jobs resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .jobs.return_value
    )


@pytest.fixture
def mock_tasks(mock_google_client):
    """Shortcut to mock tasks resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .jobs.return_value.taskGroups.return_value.tasks.return_value
    )


@pytest.fixture
def sample_job_response():
    """Sample Batch job API response."""
    return {
        "name": JOB_PATH,
        "status": {
            "state": "RUNNING",
            "statusEvents": [],
            "taskGroups": {
                "group0": {"counts": {"RUNNING": "2", "SUCCEEDED": "3"}},
            },
        },
        "taskGroups": [
            {
                "taskSpec": {
                    "runnables": [
                        {
                            "container": {
                                "imageUri": "gcr.io/test/worker:latest",
                                "commands": ["python", "run.py"],
                            },
                        },
                    ],
                    "computeResource": {
                        "cpuMilli": "2000",
                        "memoryMib": "4096",
                    },
                    "maxRunDuration": "3600s",
                },
                "taskCount": "10",
                "parallelism": "5",
            },
        ],
        "allocationPolicy": {
            "instances": [
                {
                    "policy": {
                        "machineType": "e2-standard-4",
                    },
                },
            ],
        },
        "schedulingPolicy": {"preemptible": True},
        "labels": {"env": "test", "team": "data"},
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T10:30:00Z",
    }


@pytest.fixture
def sample_task_response():
    """Sample Batch task API response."""
    return {
        "name": TASK_PATH,
        "status": {
            "state": "RUNNING",
            "statusEvents": [
                {"description": "Task started", "eventTime": "2026-03-31T10:01:00Z"},
            ],
        },
    }


class TestBatchServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the BatchService."""
        from googleapiclient.discovery import build

        svc = BatchService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("batch", "v1", credentials=None)

    def test_init_with_credentials_file(self, mock_google_client):
        """Test initializing with a credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = BatchService(
                project_id=PROJECT_ID, credentials_file="/path/to/creds.json"
            )
            assert svc.project_id == PROJECT_ID
            mock_creds.assert_called_once()


class TestListJobs:
    def test_list_jobs(self, service, mock_jobs, sample_job_response):
        """Test listing Batch jobs."""
        mock_request = mock.MagicMock()
        mock_jobs.list.return_value = mock_request
        mock_request.execute.return_value = {
            "jobs": [sample_job_response, sample_job_response]
        }
        mock_jobs.list_next.return_value = None

        jobs = service.list_jobs(LOCATION)

        mock_jobs.list.assert_called_once_with(parent=LOCATION_PATH)
        assert len(jobs) == 2
        assert isinstance(jobs[0], BatchJob)
        assert jobs[0].name == JOB_NAME
        assert jobs[0].project == PROJECT_ID
        assert jobs[0].location == LOCATION

    def test_list_jobs_empty(self, service, mock_jobs):
        """Test listing jobs when none exist."""
        mock_request = mock.MagicMock()
        mock_jobs.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_jobs.list_next.return_value = None

        jobs = service.list_jobs(LOCATION)
        assert len(jobs) == 0

    def test_list_jobs_pagination(self, service, mock_jobs, sample_job_response):
        """Test listing jobs with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_jobs.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "jobs": [sample_job_response]
        }

        mock_jobs.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "jobs": [sample_job_response]
        }

        jobs = service.list_jobs(LOCATION)
        assert len(jobs) == 2


class TestGetJob:
    def test_get_job(self, service, mock_jobs, sample_job_response):
        """Test getting a specific job."""
        mock_request = mock.MagicMock()
        mock_jobs.get.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        job = service.get_job(LOCATION, JOB_NAME)

        mock_jobs.get.assert_called_once_with(name=JOB_PATH)
        assert isinstance(job, BatchJob)
        assert job.name == JOB_NAME
        assert job.status["state"] == "RUNNING"
        assert len(job.task_groups) == 1
        assert job.allocation_policy is not None

    def test_get_job_not_found(self, service, mock_jobs):
        """Test getting a job that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_jobs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_job(LOCATION, JOB_NAME)

    def test_get_job_with_full_path(
        self, service, mock_jobs, sample_job_response
    ):
        """Test getting a job using a full resource path."""
        mock_request = mock.MagicMock()
        mock_jobs.get.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        service.get_job(LOCATION, JOB_PATH)
        mock_jobs.get.assert_called_once_with(name=JOB_PATH)


class TestCreateJob:
    def test_create_job(self, service, mock_jobs, sample_job_response):
        """Test creating a new job."""
        mock_request = mock.MagicMock()
        mock_jobs.create.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        task_groups = [
            {
                "taskSpec": {
                    "runnables": [
                        {"container": {"imageUri": "gcr.io/test/worker:latest"}},
                    ],
                },
                "taskCount": "10",
                "parallelism": "5",
            },
        ]
        allocation_policy = {
            "instances": [{"policy": {"machineType": "e2-standard-4"}}],
        }

        job = service.create_job(
            LOCATION,
            JOB_NAME,
            task_groups=task_groups,
            allocation_policy=allocation_policy,
            labels={"env": "test"},
        )

        mock_jobs.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={
                "taskGroups": task_groups,
                "allocationPolicy": allocation_policy,
                "labels": {"env": "test"},
            },
            jobId=JOB_NAME,
        )
        assert isinstance(job, BatchJob)
        assert job.name == JOB_NAME

    def test_create_job_minimal(self, service, mock_jobs, sample_job_response):
        """Test creating a job with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_jobs.create.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        task_groups = [
            {
                "taskSpec": {
                    "runnables": [
                        {"script": {"text": "echo Hello"}},
                    ],
                },
                "taskCount": "1",
            },
        ]

        job = service.create_job(LOCATION, JOB_NAME, task_groups=task_groups)

        mock_jobs.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={"taskGroups": task_groups},
            jobId=JOB_NAME,
        )
        assert isinstance(job, BatchJob)

    def test_create_job_already_exists(self, service, mock_jobs):
        """Test creating a job that already exists."""
        mock_request = mock.MagicMock()
        mock_jobs.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_job(
                LOCATION, JOB_NAME, task_groups=[{"taskSpec": {}}]
            )


class TestDeleteJob:
    def test_delete_job(self, service, mock_jobs):
        """Test deleting a job."""
        mock_request = mock.MagicMock()
        mock_jobs.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_job(LOCATION, JOB_NAME)

        mock_jobs.delete.assert_called_once_with(name=JOB_PATH)
        assert result is True

    def test_delete_job_not_found(self, service, mock_jobs):
        """Test deleting a job that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_jobs.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_job(LOCATION, JOB_NAME)


class TestListTasks:
    def test_list_tasks(self, service, mock_tasks, sample_task_response):
        """Test listing tasks in a job."""
        mock_request = mock.MagicMock()
        mock_tasks.list.return_value = mock_request
        mock_request.execute.return_value = {
            "tasks": [sample_task_response, sample_task_response]
        }
        mock_tasks.list_next.return_value = None

        tasks = service.list_tasks(LOCATION, JOB_NAME)

        mock_tasks.list.assert_called_once_with(parent=TASK_GROUP_PATH)
        assert len(tasks) == 2
        assert isinstance(tasks[0], BatchTask)
        assert tasks[0].name == TASK_NAME
        assert tasks[0].job_name == JOB_NAME
        assert tasks[0].task_group == TASK_GROUP

    def test_list_tasks_empty(self, service, mock_tasks):
        """Test listing tasks when none exist."""
        mock_request = mock.MagicMock()
        mock_tasks.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_tasks.list_next.return_value = None

        tasks = service.list_tasks(LOCATION, JOB_NAME)
        assert len(tasks) == 0

    def test_list_tasks_custom_group(self, service, mock_tasks, sample_task_response):
        """Test listing tasks with a custom task group."""
        mock_request = mock.MagicMock()
        mock_tasks.list.return_value = mock_request
        mock_request.execute.return_value = {
            "tasks": [sample_task_response]
        }
        mock_tasks.list_next.return_value = None

        custom_group_path = f"{JOB_PATH}/taskGroups/group1"
        tasks = service.list_tasks(LOCATION, JOB_NAME, task_group="group1")

        mock_tasks.list.assert_called_once_with(parent=custom_group_path)
        assert len(tasks) == 1

    def test_list_tasks_pagination(
        self, service, mock_tasks, sample_task_response
    ):
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

        tasks = service.list_tasks(LOCATION, JOB_NAME)
        assert len(tasks) == 2


class TestBatchJobModel:
    def test_from_api_response(self, sample_job_response):
        """Test creating a BatchJob from API response."""
        job = BatchJob.from_api_response(sample_job_response)

        assert job.name == JOB_NAME
        assert job.project == PROJECT_ID
        assert job.location == LOCATION
        assert job.status["state"] == "RUNNING"
        assert len(job.task_groups) == 1
        assert job.allocation_policy is not None
        assert job.scheduling_policy == {"preemptible": True}
        assert job.id == JOB_PATH
        assert job.type == "batch.job"

    def test_from_api_response_minimal(self):
        """Test creating a BatchJob from minimal API response."""
        response = {"name": JOB_PATH}
        job = BatchJob.from_api_response(response)

        assert job.name == JOB_NAME
        assert job.status == {}
        assert job.task_groups == []
        assert job.allocation_policy is None
        assert job.scheduling_policy is None

    def test_get_tag(self, sample_job_response):
        """Test getting tags from a BatchJob."""
        job = BatchJob.from_api_response(sample_job_response)

        assert job.get_tag("env") == "test"
        assert job.get_tag("team") == "data"
        assert job.get_tag("missing") == ""
        assert job.get_tag("missing", "default") == "default"


class TestBatchTaskModel:
    def test_from_api_response(self, sample_task_response):
        """Test creating a BatchTask from API response."""
        task = BatchTask.from_api_response(sample_task_response)

        assert task.name == TASK_NAME
        assert task.project == PROJECT_ID
        assert task.job_name == JOB_NAME
        assert task.task_group == TASK_GROUP
        assert task.status["state"] == "RUNNING"
        assert task.id == TASK_PATH
        assert task.type == "batch.task"

    def test_from_api_response_minimal(self):
        """Test creating a BatchTask from minimal API response."""
        response = {"name": TASK_PATH}
        task = BatchTask.from_api_response(response)

        assert task.name == TASK_NAME
        assert task.status == {}
        assert task.job_name == JOB_NAME
        assert task.task_group == TASK_GROUP


class TestPathFormatting:
    def test_format_location_path(self, service):
        """Test location path formatting."""
        assert service._format_location_path(LOCATION) == LOCATION_PATH

    def test_format_job_path(self, service):
        """Test job path formatting."""
        assert service._format_job_path(LOCATION, JOB_NAME) == JOB_PATH

    def test_format_job_path_already_formatted(self, service):
        """Test that already-formatted job paths are returned as-is."""
        assert service._format_job_path(LOCATION, JOB_PATH) == JOB_PATH

    def test_format_task_group_path(self, service):
        """Test task group path formatting."""
        assert (
            service._format_task_group_path(LOCATION, JOB_NAME, TASK_GROUP)
            == TASK_GROUP_PATH
        )
