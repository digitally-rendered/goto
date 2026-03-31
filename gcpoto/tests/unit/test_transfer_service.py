"""Tests for Cloud Storage Transfer Service."""

from unittest import mock

import pytest

from gcpoto.services.transfer import TransferService
from gcpoto.models.transfer import TransferJob, TransferOperation


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up transferJobs() chain
        mock_transfer_jobs = mock.MagicMock()
        mock_service.transferJobs.return_value = mock_transfer_jobs

        # Set up transferOperations() chain
        mock_transfer_ops = mock.MagicMock()
        mock_service.transferOperations.return_value = mock_transfer_ops

        yield mock_service


@pytest.fixture
def sample_transfer_job_response():
    """Sample Storage Transfer job API response."""
    return {
        "name": "transferJobs/12345",
        "description": "Daily GCS backup",
        "projectId": "test-project",
        "status": "ENABLED",
        "schedule": {
            "scheduleStartDate": {"year": 2025, "month": 6, "day": 1},
            "startTimeOfDay": {"hours": 2, "minutes": 0, "seconds": 0},
        },
        "transferSpec": {
            "gcsDataSource": {"bucketName": "source-bucket"},
            "gcsDataSink": {"bucketName": "dest-bucket"},
        },
        "notificationConfig": {
            "pubsubTopic": "projects/test-project/topics/transfer-notify",
            "eventTypes": ["TRANSFER_OPERATION_SUCCESS"],
            "payloadFormat": "JSON",
        },
        "latestOperationName": "transferOperations/op-abc",
        "labels": {"env": "prod", "team": "data"},
        "creationTime": "2025-06-01T00:00:00Z",
        "lastModificationTime": "2025-06-15T12:00:00Z",
    }


@pytest.fixture
def sample_transfer_operation_response():
    """Sample Storage Transfer operation API response."""
    return {
        "name": "transferOperations/op-abc",
        "metadata": {
            "transferJobName": "transferJobs/12345",
            "projectId": "test-project",
            "status": "SUCCESS",
            "startTime": "2025-06-15T02:00:00Z",
            "endTime": "2025-06-15T02:30:00Z",
            "counters": {
                "objectsFoundFromSource": "100",
                "bytesFoundFromSource": "1048576",
                "objectsCopiedToSink": "100",
                "bytesCopiedToSink": "1048576",
            },
            "errorBreakdowns": [],
        },
    }


class TestTransferServiceInit:
    """Tests for TransferService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the TransferService."""
        from googleapiclient.discovery import build

        service = TransferService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "storagetransfer"
        assert service.version == "v1"
        build.assert_called_once_with(
            "storagetransfer", "v1", credentials=None
        )


class TestTransferJobModel:
    """Tests for TransferJob model."""

    def test_from_api_response(self, sample_transfer_job_response):
        """Test creating a TransferJob from an API response."""
        job = TransferJob.from_api_response(sample_transfer_job_response)

        assert job.name == "12345"
        assert job.id == "transferJobs/12345"
        assert job.project == "test-project"
        assert job.type == "storagetransfer.transferJob"
        assert job.description == "Daily GCS backup"
        assert job.status == "ENABLED"
        assert job.schedule is not None
        assert job.schedule["scheduleStartDate"]["year"] == 2025
        assert job.transfer_spec["gcsDataSource"]["bucketName"] == "source-bucket"
        assert job.notification_config is not None
        assert job.latest_operation_name == "transferOperations/op-abc"
        assert job.labels == {"env": "prod", "team": "data"}

    def test_from_api_response_with_project_id(
        self, sample_transfer_job_response
    ):
        """Test creating a TransferJob with an explicit project ID."""
        job = TransferJob.from_api_response(
            sample_transfer_job_response, project_id="override-project"
        )
        assert job.project == "override-project"

    def test_from_api_response_minimal(self):
        """Test creating a TransferJob with minimal data."""
        response = {
            "name": "transferJobs/99999",
            "projectId": "my-project",
            "status": "DISABLED",
            "transferSpec": {
                "gcsDataSource": {"bucketName": "src"},
                "gcsDataSink": {"bucketName": "dst"},
            },
        }
        job = TransferJob.from_api_response(response)

        assert job.name == "99999"
        assert job.status == "DISABLED"
        assert job.description is None
        assert job.schedule is None
        assert job.notification_config is None
        assert job.latest_operation_name is None

    def test_get_tag(self, sample_transfer_job_response):
        """Test get_tag method on TransferJob."""
        job = TransferJob.from_api_response(sample_transfer_job_response)

        assert job.get_tag("env") == "prod"
        assert job.get_tag("team") == "data"
        assert job.get_tag("nonexistent") == ""
        assert job.get_tag("nonexistent", "default") == "default"

    def test_get_tag_no_labels(self):
        """Test get_tag when no labels are present."""
        response = {
            "name": "transferJobs/1",
            "projectId": "p",
            "status": "ENABLED",
            "transferSpec": {},
        }
        job = TransferJob.from_api_response(response)
        assert job.get_tag("any_key") == ""
        assert job.get_tag("any_key", "fallback") == "fallback"


class TestTransferOperationModel:
    """Tests for TransferOperation model."""

    def test_from_api_response(self, sample_transfer_operation_response):
        """Test creating a TransferOperation from an API response."""
        op = TransferOperation.from_api_response(
            sample_transfer_operation_response
        )

        assert op.name == "op-abc"
        assert op.id == "transferOperations/op-abc"
        assert op.project == "test-project"
        assert op.type == "storagetransfer.transferOperation"
        assert op.transfer_job_name == "transferJobs/12345"
        assert op.status == "SUCCESS"
        assert op.counters is not None
        assert op.counters["objectsCopiedToSink"] == "100"
        assert op.error_breakdowns == []

    def test_from_api_response_minimal(self):
        """Test creating a TransferOperation with minimal data."""
        response = {
            "name": "transferOperations/op-xyz",
            "metadata": {
                "transferJobName": "transferJobs/1",
                "status": "IN_PROGRESS",
            },
        }
        op = TransferOperation.from_api_response(response)

        assert op.name == "op-xyz"
        assert op.status == "IN_PROGRESS"
        assert op.start_time is None
        assert op.end_time is None
        assert op.counters is None
        assert op.error_breakdowns is None

    def test_from_api_response_with_project_id(
        self, sample_transfer_operation_response
    ):
        """Test creating a TransferOperation with an explicit project ID."""
        op = TransferOperation.from_api_response(
            sample_transfer_operation_response,
            project_id="override-project",
        )
        assert op.project == "override-project"


class TestListTransferJobs:
    """Tests for listing transfer jobs."""

    def test_list_transfer_jobs(
        self, mock_google_client, sample_transfer_job_response
    ):
        """Test listing transfer jobs."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.list.return_value = mock_request
        mock_request.execute.return_value = {
            "transferJobs": [
                sample_transfer_job_response,
                sample_transfer_job_response,
            ]
        }
        mock_jobs.list_next.return_value = None

        service = TransferService(project_id="test-project")
        jobs = service.list_transfer_jobs()

        mock_jobs.list.assert_called_once_with(
            filter='{"projectId":"test-project"}'
        )
        assert len(jobs) == 2
        assert isinstance(jobs[0], TransferJob)
        assert jobs[0].name == "12345"

    def test_list_transfer_jobs_with_filter(
        self, mock_google_client, sample_transfer_job_response
    ):
        """Test listing transfer jobs with a custom filter."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.list.return_value = mock_request
        mock_request.execute.return_value = {
            "transferJobs": [sample_transfer_job_response]
        }
        mock_jobs.list_next.return_value = None

        service = TransferService(project_id="test-project")
        custom_filter = '{"projectId":"test-project","jobStatuses":["ENABLED"]}'
        jobs = service.list_transfer_jobs(filter_str=custom_filter)

        mock_jobs.list.assert_called_once_with(filter=custom_filter)
        assert len(jobs) == 1

    def test_list_transfer_jobs_empty(self, mock_google_client):
        """Test listing transfer jobs with no results."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_jobs.list_next.return_value = None

        service = TransferService(project_id="test-project")
        jobs = service.list_transfer_jobs()

        assert jobs == []

    def test_list_transfer_jobs_pagination(
        self, mock_google_client, sample_transfer_job_response
    ):
        """Test listing transfer jobs with pagination."""
        mock_jobs = mock_google_client.transferJobs.return_value

        # First page
        mock_request_1 = mock.MagicMock()
        mock_jobs.list.return_value = mock_request_1
        mock_request_1.execute.return_value = {
            "transferJobs": [sample_transfer_job_response]
        }

        # Second page
        mock_request_2 = mock.MagicMock()
        mock_request_2.execute.return_value = {
            "transferJobs": [sample_transfer_job_response]
        }
        mock_jobs.list_next.side_effect = [mock_request_2, None]

        service = TransferService(project_id="test-project")
        jobs = service.list_transfer_jobs()

        assert len(jobs) == 2


class TestGetTransferJob:
    """Tests for getting a transfer job."""

    def test_get_transfer_job(
        self, mock_google_client, sample_transfer_job_response
    ):
        """Test getting a specific transfer job."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.get.return_value = mock_request
        mock_request.execute.return_value = sample_transfer_job_response

        service = TransferService(project_id="test-project")
        job = service.get_transfer_job("transferJobs/12345")

        mock_jobs.get.assert_called_once_with(
            jobName="transferJobs/12345", projectId="test-project"
        )
        assert isinstance(job, TransferJob)
        assert job.name == "12345"
        assert job.status == "ENABLED"


class TestCreateTransferJob:
    """Tests for creating a transfer job."""

    def test_create_transfer_job_basic(
        self, mock_google_client, sample_transfer_job_response
    ):
        """Test creating a transfer job with required fields."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.create.return_value = mock_request
        mock_request.execute.return_value = sample_transfer_job_response

        service = TransferService(project_id="test-project")
        transfer_spec = {
            "gcsDataSource": {"bucketName": "source-bucket"},
            "gcsDataSink": {"bucketName": "dest-bucket"},
        }
        job = service.create_transfer_job(
            description="Daily backup",
            transfer_spec=transfer_spec,
        )

        mock_jobs.create.assert_called_once_with(
            body={
                "projectId": "test-project",
                "description": "Daily backup",
                "transferSpec": transfer_spec,
                "status": "ENABLED",
            }
        )
        assert isinstance(job, TransferJob)
        assert job.name == "12345"

    def test_create_transfer_job_full(
        self, mock_google_client, sample_transfer_job_response
    ):
        """Test creating a transfer job with all options."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.create.return_value = mock_request
        mock_request.execute.return_value = sample_transfer_job_response

        service = TransferService(project_id="test-project")
        transfer_spec = {
            "gcsDataSource": {"bucketName": "source-bucket"},
            "gcsDataSink": {"bucketName": "dest-bucket"},
        }
        schedule = {
            "scheduleStartDate": {"year": 2025, "month": 6, "day": 1},
            "startTimeOfDay": {"hours": 2, "minutes": 0, "seconds": 0},
        }
        notification_config = {
            "pubsubTopic": "projects/test-project/topics/notify",
            "eventTypes": ["TRANSFER_OPERATION_SUCCESS"],
        }

        job = service.create_transfer_job(
            description="Full backup",
            transfer_spec=transfer_spec,
            schedule=schedule,
            notification_config=notification_config,
        )

        mock_jobs.create.assert_called_once_with(
            body={
                "projectId": "test-project",
                "description": "Full backup",
                "transferSpec": transfer_spec,
                "status": "ENABLED",
                "schedule": schedule,
                "notificationConfig": notification_config,
            }
        )
        assert isinstance(job, TransferJob)


class TestUpdateTransferJob:
    """Tests for updating a transfer job."""

    def test_update_transfer_job(
        self, mock_google_client, sample_transfer_job_response
    ):
        """Test updating a transfer job."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.patch.return_value = mock_request
        mock_request.execute.return_value = sample_transfer_job_response

        service = TransferService(project_id="test-project")
        job = service.update_transfer_job(
            job_name="transferJobs/12345",
            update_fields={"description": "Updated backup"},
            update_mask="description",
        )

        mock_jobs.patch.assert_called_once_with(
            jobName="transferJobs/12345",
            body={
                "projectId": "test-project",
                "transferJob": {"description": "Updated backup"},
                "updateTransferJobFieldMask": "description",
            },
        )
        assert isinstance(job, TransferJob)


class TestPauseResumeTransferJob:
    """Tests for pausing and resuming transfer jobs."""

    def test_pause_transfer_job(self, mock_google_client):
        """Test pausing a transfer job."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.patch.return_value = mock_request
        mock_request.execute.return_value = {}

        service = TransferService(project_id="test-project")
        service.pause_transfer_job("transferJobs/12345")

        mock_jobs.patch.assert_called_once_with(
            jobName="transferJobs/12345",
            body={
                "projectId": "test-project",
                "transferJob": {"status": "DISABLED"},
                "updateTransferJobFieldMask": "status",
            },
        )

    def test_resume_transfer_job(self, mock_google_client):
        """Test resuming a transfer job."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.patch.return_value = mock_request
        mock_request.execute.return_value = {}

        service = TransferService(project_id="test-project")
        service.resume_transfer_job("transferJobs/12345")

        mock_jobs.patch.assert_called_once_with(
            jobName="transferJobs/12345",
            body={
                "projectId": "test-project",
                "transferJob": {"status": "ENABLED"},
                "updateTransferJobFieldMask": "status",
            },
        )


class TestDeleteTransferJob:
    """Tests for deleting a transfer job."""

    def test_delete_transfer_job(self, mock_google_client):
        """Test deleting (soft delete) a transfer job."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.patch.return_value = mock_request
        mock_request.execute.return_value = {}

        service = TransferService(project_id="test-project")
        service.delete_transfer_job("transferJobs/12345")

        mock_jobs.patch.assert_called_once_with(
            jobName="transferJobs/12345",
            body={
                "projectId": "test-project",
                "transferJob": {"status": "DELETED"},
                "updateTransferJobFieldMask": "status",
            },
        )


class TestRunTransferJob:
    """Tests for running a transfer job."""

    def test_run_transfer_job(self, mock_google_client):
        """Test running a transfer job immediately."""
        mock_jobs = mock_google_client.transferJobs.return_value
        mock_request = mock.MagicMock()
        mock_jobs.run.return_value = mock_request
        mock_request.execute.return_value = {
            "name": "transferOperations/op-new"
        }

        service = TransferService(project_id="test-project")
        result = service.run_transfer_job("transferJobs/12345")

        mock_jobs.run.assert_called_once_with(
            jobName="transferJobs/12345",
            body={"projectId": "test-project"},
        )
        assert result == {"name": "transferOperations/op-new"}


class TestListTransferOperations:
    """Tests for listing transfer operations."""

    def test_list_transfer_operations(
        self, mock_google_client, sample_transfer_operation_response
    ):
        """Test listing transfer operations for a job."""
        mock_ops = mock_google_client.transferOperations.return_value
        mock_request = mock.MagicMock()
        mock_ops.list.return_value = mock_request
        mock_request.execute.return_value = {
            "operations": [
                sample_transfer_operation_response,
                sample_transfer_operation_response,
            ]
        }
        mock_ops.list_next.return_value = None

        service = TransferService(project_id="test-project")
        ops = service.list_transfer_operations("transferJobs/12345")

        mock_ops.list.assert_called_once_with(
            name="transferOperations",
            filter='{"projectId":"test-project","jobNames":["transferJobs/12345"]}',
        )
        assert len(ops) == 2
        assert isinstance(ops[0], TransferOperation)
        assert ops[0].status == "SUCCESS"

    def test_list_transfer_operations_empty(self, mock_google_client):
        """Test listing transfer operations with no results."""
        mock_ops = mock_google_client.transferOperations.return_value
        mock_request = mock.MagicMock()
        mock_ops.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_ops.list_next.return_value = None

        service = TransferService(project_id="test-project")
        ops = service.list_transfer_operations("transferJobs/12345")

        assert ops == []

    def test_list_transfer_operations_pagination(
        self, mock_google_client, sample_transfer_operation_response
    ):
        """Test listing transfer operations with pagination."""
        mock_ops = mock_google_client.transferOperations.return_value

        # First page
        mock_request_1 = mock.MagicMock()
        mock_ops.list.return_value = mock_request_1
        mock_request_1.execute.return_value = {
            "operations": [sample_transfer_operation_response]
        }

        # Second page
        mock_request_2 = mock.MagicMock()
        mock_request_2.execute.return_value = {
            "operations": [sample_transfer_operation_response]
        }
        mock_ops.list_next.side_effect = [mock_request_2, None]

        service = TransferService(project_id="test-project")
        ops = service.list_transfer_operations("transferJobs/12345")

        assert len(ops) == 2


class TestGetTransferOperation:
    """Tests for getting a transfer operation."""

    def test_get_transfer_operation(
        self, mock_google_client, sample_transfer_operation_response
    ):
        """Test getting a specific transfer operation."""
        mock_ops = mock_google_client.transferOperations.return_value
        mock_request = mock.MagicMock()
        mock_ops.get.return_value = mock_request
        mock_request.execute.return_value = (
            sample_transfer_operation_response
        )

        service = TransferService(project_id="test-project")
        op = service.get_transfer_operation("transferOperations/op-abc")

        mock_ops.get.assert_called_once_with(
            name="transferOperations/op-abc"
        )
        assert isinstance(op, TransferOperation)
        assert op.name == "op-abc"
        assert op.status == "SUCCESS"
        assert op.transfer_job_name == "transferJobs/12345"
