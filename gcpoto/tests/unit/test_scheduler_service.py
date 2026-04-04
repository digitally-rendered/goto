"""Tests for Cloud Scheduler service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.scheduler import SchedulerService
from gcpoto.models.scheduler import SchedulerJob
from gcpoto.exceptions import ResourceNotFoundError, APIError


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

        yield mock_service


@pytest.fixture
def sample_job_response():
    """Sample Cloud Scheduler job API response."""
    return {
        "name": "projects/test-project/locations/us-central1/jobs/test-job",
        "description": "A test scheduler job",
        "schedule": "*/5 * * * *",
        "timeZone": "America/New_York",
        "state": "ENABLED",
        "httpTarget": {
            "uri": "https://example.com/callback",
            "httpMethod": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": "eyJrZXkiOiAidmFsdWUifQ==",
        },
        "retryConfig": {
            "retryCount": 3,
            "maxRetryDuration": "0s",
            "minBackoffDuration": "5s",
            "maxBackoffDuration": "3600s",
            "maxDoublings": 5,
        },
        "attemptDeadline": "180s",
        "lastAttemptTime": "2025-01-15T10:00:00Z",
        "scheduleTime": "2025-01-15T10:05:00Z",
        "status": {"code": 0},
        "labels": {"env": "test", "team": "backend"},
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-10T00:00:00Z",
    }


@pytest.fixture
def sample_pubsub_job_response():
    """Sample Cloud Scheduler job with Pub/Sub target."""
    return {
        "name": "projects/test-project/locations/us-central1/jobs/pubsub-job",
        "description": "A Pub/Sub scheduler job",
        "schedule": "0 * * * *",
        "timeZone": "UTC",
        "state": "ENABLED",
        "pubsubTarget": {
            "topicName": "projects/test-project/topics/my-topic",
            "data": "dGVzdA==",
            "attributes": {"key": "value"},
        },
    }


class TestSchedulerServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the SchedulerService."""
        from googleapiclient.discovery import build

        service = SchedulerService(project_id="test-project")

        assert service.project_id == "test-project"
        build.assert_called_once_with(
            "cloudscheduler", "v1", credentials=None
        )

    def test_init_with_credentials(self, mock_google_client):
        """Test initializing with a credentials file."""
        with mock.patch(
            "gcpoto.services.base.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            service = SchedulerService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert service.project_id == "test-project"
            mock_creds.assert_called_once()


class TestListJobs:
    def test_list_jobs(self, mock_google_client, sample_job_response):
        """Test listing Cloud Scheduler jobs."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.list
        )
        mock_list.return_value = mock_request

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.list_next
        )
        mock_list_next.return_value = None

        mock_request.execute.return_value = {
            "jobs": [sample_job_response, sample_job_response]
        }

        service = SchedulerService(project_id="test-project")
        jobs = service.list_jobs("us-central1")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(jobs) == 2
        assert isinstance(jobs[0], SchedulerJob)
        assert jobs[0].name == "test-job"
        assert jobs[0].location == "us-central1"
        assert jobs[0].schedule == "*/5 * * * *"

    def test_list_jobs_empty(self, mock_google_client):
        """Test listing jobs when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.list
        )
        mock_list.return_value = mock_request

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.list_next
        )
        mock_list_next.return_value = None

        mock_request.execute.return_value = {}

        service = SchedulerService(project_id="test-project")
        jobs = service.list_jobs("us-central1")

        assert len(jobs) == 0

    def test_list_jobs_pagination(self, mock_google_client, sample_job_response):
        """Test listing jobs with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.list
        )
        mock_list.return_value = mock_request_page1

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.list_next
        )
        mock_list_next.side_effect = [mock_request_page2, None]

        mock_request_page1.execute.return_value = {
            "jobs": [sample_job_response]
        }
        mock_request_page2.execute.return_value = {
            "jobs": [sample_job_response]
        }

        service = SchedulerService(project_id="test-project")
        jobs = service.list_jobs("us-central1")

        assert len(jobs) == 2


class TestGetJob:
    def test_get_job(self, mock_google_client, sample_job_response):
        """Test getting a specific Cloud Scheduler job."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        service = SchedulerService(project_id="test-project")
        job = service.get_job("us-central1", "test-job")

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/jobs/test-job"
        )
        assert isinstance(job, SchedulerJob)
        assert job.name == "test-job"
        assert job.project == "test-project"
        assert job.location == "us-central1"
        assert job.schedule == "*/5 * * * *"
        assert job.time_zone == "America/New_York"
        assert job.state == "ENABLED"
        assert job.description == "A test scheduler job"
        assert job.http_target["uri"] == "https://example.com/callback"
        assert job.retry_config["retryCount"] == 3
        assert job.attempt_deadline == "180s"

    def test_get_job_with_full_path(self, mock_google_client, sample_job_response):
        """Test getting a job using its full resource path."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        service = SchedulerService(project_id="test-project")
        full_path = "projects/test-project/locations/us-central1/jobs/test-job"
        job = service.get_job("us-central1", full_path)

        mock_get.assert_called_once_with(name=full_path)
        assert job.name == "test-job"

    def test_get_job_not_found(self, mock_google_client):
        """Test getting a job that does not exist."""
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.get
        )
        mock_get.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Job not found"
        )

        service = SchedulerService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_job("us-central1", "nonexistent-job")

    def test_get_job_api_error(self, mock_google_client):
        """Test getting a job with a non-404 API error."""
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.get
        )
        mock_get.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = SchedulerService(project_id="test-project")

        with pytest.raises(APIError):
            service.get_job("us-central1", "test-job")


class TestCreateJob:
    def test_create_job_with_http_target(
        self, mock_google_client, sample_job_response
    ):
        """Test creating a job with an HTTP target."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        service = SchedulerService(project_id="test-project")
        job = service.create_job(
            location="us-central1",
            job_name="test-job",
            schedule="*/5 * * * *",
            time_zone="America/New_York",
            http_target={
                "uri": "https://example.com/callback",
                "httpMethod": "POST",
            },
            description="A test scheduler job",
            retry_config={"retryCount": 3},
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1",
            body={
                "name": "projects/test-project/locations/us-central1/jobs/test-job",
                "schedule": "*/5 * * * *",
                "timeZone": "America/New_York",
                "httpTarget": {
                    "uri": "https://example.com/callback",
                    "httpMethod": "POST",
                },
                "description": "A test scheduler job",
                "retryConfig": {"retryCount": 3},
            },
        )
        assert isinstance(job, SchedulerJob)
        assert job.name == "test-job"

    def test_create_job_with_pubsub_target(
        self, mock_google_client, sample_pubsub_job_response
    ):
        """Test creating a job with a Pub/Sub target."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_pubsub_job_response

        service = SchedulerService(project_id="test-project")
        job = service.create_job(
            location="us-central1",
            job_name="pubsub-job",
            schedule="0 * * * *",
            time_zone="UTC",
            pubsub_target={
                "topicName": "projects/test-project/topics/my-topic",
                "data": "dGVzdA==",
            },
        )

        assert isinstance(job, SchedulerJob)
        assert job.name == "pubsub-job"
        assert job.pubsub_target is not None

    def test_create_job_minimal(self, mock_google_client, sample_job_response):
        """Test creating a job with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        service = SchedulerService(project_id="test-project")
        job = service.create_job(
            location="us-central1",
            job_name="test-job",
            schedule="*/5 * * * *",
            time_zone="UTC",
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1",
            body={
                "name": "projects/test-project/locations/us-central1/jobs/test-job",
                "schedule": "*/5 * * * *",
                "timeZone": "UTC",
            },
        )
        assert isinstance(job, SchedulerJob)

    def test_create_job_conflict(self, mock_google_client):
        """Test creating a job that already exists."""
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.create
        )
        mock_create.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Job already exists"
        )

        service = SchedulerService(project_id="test-project")

        with pytest.raises(ValueError, match="Job 'test-job' already exists"):
            service.create_job(
                location="us-central1",
                job_name="test-job",
                schedule="*/5 * * * *",
                time_zone="UTC",
            )

    def test_create_job_api_error(self, mock_google_client):
        """Test creating a job with an API error."""
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.create
        )
        mock_create.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        service = SchedulerService(project_id="test-project")

        with pytest.raises(APIError):
            service.create_job(
                location="us-central1",
                job_name="test-job",
                schedule="invalid",
                time_zone="UTC",
            )


class TestUpdateJob:
    def test_update_job(self, mock_google_client, sample_job_response):
        """Test updating a Cloud Scheduler job."""
        updated_response = dict(sample_job_response)
        updated_response["schedule"] = "0 * * * *"
        updated_response["description"] = "Updated description"

        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = updated_response

        service = SchedulerService(project_id="test-project")
        job = service.update_job(
            location="us-central1",
            job_name="test-job",
            update_fields={
                "schedule": "0 * * * *",
                "description": "Updated description",
            },
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/jobs/test-job",
            body={
                "name": "projects/test-project/locations/us-central1/jobs/test-job",
                "schedule": "0 * * * *",
                "description": "Updated description",
            },
            updateMask="schedule,description",
        )
        assert isinstance(job, SchedulerJob)
        assert job.schedule == "0 * * * *"

    def test_update_job_not_found(self, mock_google_client):
        """Test updating a job that does not exist."""
        mock_patch = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.patch
        )
        mock_patch.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Job not found"
        )

        service = SchedulerService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.update_job(
                location="us-central1",
                job_name="nonexistent-job",
                update_fields={"schedule": "0 * * * *"},
            )


class TestDeleteJob:
    def test_delete_job(self, mock_google_client):
        """Test deleting a Cloud Scheduler job."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = SchedulerService(project_id="test-project")
        result = service.delete_job("us-central1", "test-job")

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/jobs/test-job"
        )
        assert result is True

    def test_delete_job_not_found(self, mock_google_client):
        """Test deleting a job that does not exist."""
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.delete
        )
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Job not found"
        )

        service = SchedulerService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.delete_job("us-central1", "nonexistent-job")


class TestPauseJob:
    def test_pause_job(self, mock_google_client, sample_job_response):
        """Test pausing a Cloud Scheduler job."""
        paused_response = dict(sample_job_response)
        paused_response["state"] = "PAUSED"

        mock_request = mock.MagicMock()
        mock_pause = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.pause
        )
        mock_pause.return_value = mock_request
        mock_request.execute.return_value = paused_response

        service = SchedulerService(project_id="test-project")
        job = service.pause_job("us-central1", "test-job")

        mock_pause.assert_called_once_with(
            name="projects/test-project/locations/us-central1/jobs/test-job",
            body={},
        )
        assert isinstance(job, SchedulerJob)
        assert job.state == "PAUSED"

    def test_pause_job_not_found(self, mock_google_client):
        """Test pausing a job that does not exist."""
        mock_pause = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.pause
        )
        mock_pause.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Job not found"
        )

        service = SchedulerService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.pause_job("us-central1", "nonexistent-job")


class TestResumeJob:
    def test_resume_job(self, mock_google_client, sample_job_response):
        """Test resuming a paused Cloud Scheduler job."""
        mock_request = mock.MagicMock()
        mock_resume = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.resume
        )
        mock_resume.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        service = SchedulerService(project_id="test-project")
        job = service.resume_job("us-central1", "test-job")

        mock_resume.assert_called_once_with(
            name="projects/test-project/locations/us-central1/jobs/test-job",
            body={},
        )
        assert isinstance(job, SchedulerJob)
        assert job.state == "ENABLED"

    def test_resume_job_not_found(self, mock_google_client):
        """Test resuming a job that does not exist."""
        mock_resume = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.resume
        )
        mock_resume.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Job not found"
        )

        service = SchedulerService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.resume_job("us-central1", "nonexistent-job")


class TestRunJob:
    def test_run_job(self, mock_google_client, sample_job_response):
        """Test force-running a Cloud Scheduler job."""
        mock_request = mock.MagicMock()
        mock_run = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.run
        )
        mock_run.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        service = SchedulerService(project_id="test-project")
        job = service.run_job("us-central1", "test-job")

        mock_run.assert_called_once_with(
            name="projects/test-project/locations/us-central1/jobs/test-job",
            body={},
        )
        assert isinstance(job, SchedulerJob)
        assert job.name == "test-job"

    def test_run_job_not_found(self, mock_google_client):
        """Test running a job that does not exist."""
        mock_run = (
            mock_google_client.projects.return_value.locations.return_value.jobs.return_value.run
        )
        mock_run.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Job not found"
        )

        service = SchedulerService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.run_job("us-central1", "nonexistent-job")


class TestSchedulerJobModel:
    def test_from_api_response(self, sample_job_response):
        """Test creating a SchedulerJob from an API response."""
        job = SchedulerJob.from_api_response(sample_job_response)

        assert job.name == "test-job"
        assert job.project == "test-project"
        assert job.location == "us-central1"
        assert job.type == "scheduler.job"
        assert job.schedule == "*/5 * * * *"
        assert job.time_zone == "America/New_York"
        assert job.state == "ENABLED"
        assert job.description == "A test scheduler job"
        assert job.http_target["uri"] == "https://example.com/callback"
        assert job.retry_config["retryCount"] == 3
        assert job.attempt_deadline == "180s"
        assert job.labels == {"env": "test", "team": "backend"}

    def test_from_api_response_with_project_id(self, sample_job_response):
        """Test creating a SchedulerJob with explicit project_id."""
        job = SchedulerJob.from_api_response(
            sample_job_response, project_id="override-project"
        )
        assert job.project == "override-project"

    def test_from_api_response_minimal(self):
        """Test creating a SchedulerJob from a minimal response."""
        response = {
            "name": "projects/my-project/locations/us-east1/jobs/simple-job",
            "schedule": "0 0 * * *",
            "timeZone": "UTC",
        }
        job = SchedulerJob.from_api_response(response)

        assert job.name == "simple-job"
        assert job.project == "my-project"
        assert job.location == "us-east1"
        assert job.schedule == "0 0 * * *"
        assert job.time_zone == "UTC"
        assert job.state == "ENABLED"
        assert job.http_target is None
        assert job.pubsub_target is None

    def test_get_tag(self, sample_job_response):
        """Test getting a tag value."""
        job = SchedulerJob.from_api_response(sample_job_response)

        assert job.get_tag("env") == "test"
        assert job.get_tag("team") == "backend"
        assert job.get_tag("nonexistent") == ""
        assert job.get_tag("nonexistent", "default") == "default"

    def test_get_tag_no_labels(self):
        """Test getting a tag when no labels exist."""
        response = {
            "name": "projects/p/locations/l/jobs/j",
            "schedule": "* * * * *",
            "timeZone": "UTC",
        }
        job = SchedulerJob.from_api_response(response)
        assert job.get_tag("anything") == ""

    def test_to_dict(self, sample_job_response):
        """Test converting a SchedulerJob to a dictionary."""
        job = SchedulerJob.from_api_response(sample_job_response)
        data = job.to_dict()

        assert data["name"] == "test-job"
        assert data["schedule"] == "*/5 * * * *"
        assert "id" in data
        assert data["state"] == "ENABLED"

    def test_from_api_response_pubsub_target(self, sample_pubsub_job_response):
        """Test creating a SchedulerJob with a Pub/Sub target."""
        job = SchedulerJob.from_api_response(sample_pubsub_job_response)

        assert job.name == "pubsub-job"
        assert job.pubsub_target is not None
        assert (
            job.pubsub_target["topicName"]
            == "projects/test-project/topics/my-topic"
        )
        assert job.http_target is None

    def test_from_api_response_app_engine_target(self):
        """Test creating a SchedulerJob with an App Engine target."""
        response = {
            "name": "projects/test-project/locations/us-central1/jobs/ae-job",
            "schedule": "0 9 * * 1",
            "timeZone": "America/Los_Angeles",
            "state": "ENABLED",
            "appEngineHttpTarget": {
                "httpMethod": "GET",
                "relativeUri": "/cron/weekly",
                "appEngineRouting": {"service": "default"},
            },
        }
        job = SchedulerJob.from_api_response(response)

        assert job.name == "ae-job"
        assert job.app_engine_http_target is not None
        assert job.app_engine_http_target["relativeUri"] == "/cron/weekly"
        assert job.http_target is None
        assert job.pubsub_target is None
