"""Tests for Dataflow service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.dataflow import DataflowService
from gcpoto.models.dataflow import DataflowJob, DataflowTemplate
from gcpoto.exceptions import ResourceNotFoundError, APIError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
JOB_ID = "2026-03-31_00_00_00-12345"
JOB_NAME = "test-dataflow-job"
TEMPLATE_GCS_PATH = "gs://dataflow-templates/test-template"


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

        # Set up projects().locations().jobs().messages() chain
        mock_messages = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.jobs.return_value.messages.return_value = (
            mock_messages
        )

        # Set up projects().locations().templates() chain
        mock_templates = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.templates.return_value = (
            mock_templates
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a DataflowService with mocked client."""
    return DataflowService(project_id=PROJECT_ID)


@pytest.fixture
def sample_job_response():
    """Sample Dataflow job API response."""
    return {
        "id": JOB_ID,
        "name": JOB_NAME,
        "projectId": PROJECT_ID,
        "location": LOCATION,
        "type": "JOB_TYPE_BATCH",
        "currentState": "JOB_STATE_RUNNING",
        "createTime": "2026-03-31T10:00:00Z",
        "startTime": "2026-03-31T10:00:05Z",
        "currentStateTime": "2026-03-31T10:00:05Z",
        "requestedState": "JOB_STATE_RUNNING",
        "pipelineDescription": {
            "originalPipelineTransform": [
                {"name": "ReadFromSource", "kind": "ParallelRead"}
            ],
            "executionPipelineStage": [
                {"name": "F0", "kind": "PAR_DO_KIND"}
            ],
        },
        "stageStates": [
            {
                "executionStageName": "F0",
                "executionStageState": "JOB_STATE_RUNNING",
                "currentStateTime": "2026-03-31T10:00:05Z",
            }
        ],
        "environment": {
            "tempStoragePrefix": "gs://test-bucket/temp",
            "workerPools": [
                {"machineType": "n1-standard-4", "numWorkers": 2}
            ],
            "serviceAccountEmail": "sa@test-project.iam.gserviceaccount.com",
        },
        "sdkPipelineOptions": {
            "options": {"project": PROJECT_ID, "region": LOCATION}
        },
        "tempFiles": ["gs://test-bucket/temp/file1", "gs://test-bucket/temp/file2"],
        "labels": {"env": "test", "team": "data-eng"},
    }


@pytest.fixture
def sample_streaming_job_response(sample_job_response):
    """Sample Dataflow streaming job API response."""
    return {
        **sample_job_response,
        "type": "JOB_TYPE_STREAMING",
        "name": "test-streaming-job",
    }


@pytest.fixture
def sample_template_response():
    """Sample Dataflow template launch API response."""
    return {
        "job": {
            "id": JOB_ID,
            "name": JOB_NAME,
            "projectId": PROJECT_ID,
            "location": LOCATION,
            "createTime": "2026-03-31T10:00:00Z",
            "currentStateTime": "2026-03-31T10:00:00Z",
            "labels": {"template": "test"},
        },
        "metadata": {
            "name": "Test Template",
            "description": "A test template",
            "parameters": [
                {
                    "name": "inputFile",
                    "label": "Input file",
                    "helpText": "Path to input",
                    "isOptional": False,
                }
            ],
        },
    }


@pytest.fixture
def sample_message_response():
    """Sample Dataflow job message API response."""
    return {
        "jobMessages": [
            {
                "id": "msg-1",
                "time": "2026-03-31T10:00:01Z",
                "messageText": "Worker pool started.",
                "messageImportance": "JOB_MESSAGE_BASIC",
            },
            {
                "id": "msg-2",
                "time": "2026-03-31T10:00:02Z",
                "messageText": "Pipeline running.",
                "messageImportance": "JOB_MESSAGE_DETAILED",
            },
        ]
    }


@pytest.fixture
def mock_jobs(mock_google_client):
    """Shortcut to mock jobs resource."""
    return mock_google_client.projects.return_value.locations.return_value.jobs.return_value


@pytest.fixture
def mock_messages(mock_google_client):
    """Shortcut to mock messages resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .jobs.return_value.messages.return_value
    )


@pytest.fixture
def mock_templates(mock_google_client):
    """Shortcut to mock templates resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .templates.return_value
    )


class TestDataflowServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the DataflowService."""
        from googleapiclient.discovery import build

        svc = DataflowService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("dataflow", "v1b3", credentials=None)

    def test_init_with_credentials_file(self, mock_google_client):
        """Test initializing with a credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = DataflowService(
                project_id=PROJECT_ID, credentials_file="/path/to/creds.json"
            )
            assert svc.project_id == PROJECT_ID
            mock_creds.assert_called_once()


class TestListJobs:
    def test_list_jobs(self, service, mock_jobs, sample_job_response):
        """Test listing Dataflow jobs."""
        mock_request = mock.MagicMock()
        mock_jobs.list.return_value = mock_request
        mock_request.execute.return_value = {
            "jobs": [sample_job_response, sample_job_response]
        }
        mock_jobs.list_next.return_value = None

        jobs = service.list_jobs(LOCATION)

        mock_jobs.list.assert_called_once_with(
            projectId=PROJECT_ID, location=LOCATION
        )
        assert len(jobs) == 2
        assert isinstance(jobs[0], DataflowJob)
        assert jobs[0].name == JOB_NAME
        assert jobs[0].project == PROJECT_ID
        assert jobs[0].location == LOCATION
        assert jobs[0].job_type == "JOB_TYPE_BATCH"
        assert jobs[0].current_state == "JOB_STATE_RUNNING"

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

        job = service.get_job(LOCATION, JOB_ID)

        mock_jobs.get.assert_called_once_with(
            projectId=PROJECT_ID, location=LOCATION, jobId=JOB_ID
        )
        assert isinstance(job, DataflowJob)
        assert job.name == JOB_NAME
        assert job.id == JOB_ID
        assert job.current_state == "JOB_STATE_RUNNING"
        assert job.job_type == "JOB_TYPE_BATCH"
        assert job.environment == sample_job_response["environment"]
        assert job.pipeline_description == sample_job_response["pipelineDescription"]
        assert job.stage_states == sample_job_response["stageStates"]
        assert job.sdk_pipeline_options == sample_job_response["sdkPipelineOptions"]
        assert job.temp_files == sample_job_response["tempFiles"]

    def test_get_job_not_found(self, service, mock_jobs):
        """Test getting a job that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_jobs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_job(LOCATION, JOB_ID)


class TestCreateJob:
    def test_create_job(self, service, mock_jobs, sample_job_response):
        """Test creating a new job."""
        mock_request = mock.MagicMock()
        mock_jobs.create.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        job_body = {
            "name": JOB_NAME,
            "type": "JOB_TYPE_BATCH",
            "environment": {
                "tempStoragePrefix": "gs://test-bucket/temp",
            },
        }

        job = service.create_job(LOCATION, job_body)

        mock_jobs.create.assert_called_once_with(
            projectId=PROJECT_ID, location=LOCATION, body=job_body
        )
        assert isinstance(job, DataflowJob)
        assert job.name == JOB_NAME

    def test_create_job_api_error(self, service, mock_jobs):
        """Test creating a job when API returns an error."""
        mock_request = mock.MagicMock()
        mock_jobs.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_job(LOCATION, {"name": "bad-job"})


class TestUpdateJob:
    def test_update_job(self, service, mock_jobs, sample_job_response):
        """Test updating a job's state."""
        updated_response = {
            **sample_job_response,
            "requestedState": "JOB_STATE_CANCELLED",
        }
        mock_request = mock.MagicMock()
        mock_jobs.update.return_value = mock_request
        mock_request.execute.return_value = updated_response

        job = service.update_job(LOCATION, JOB_ID, "JOB_STATE_CANCELLED")

        mock_jobs.update.assert_called_once_with(
            projectId=PROJECT_ID,
            location=LOCATION,
            jobId=JOB_ID,
            body={"requestedState": "JOB_STATE_CANCELLED"},
        )
        assert isinstance(job, DataflowJob)

    def test_update_job_not_found(self, service, mock_jobs):
        """Test updating a job that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_jobs.update.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_job(LOCATION, JOB_ID, "JOB_STATE_CANCELLED")


class TestCancelJob:
    def test_cancel_job(self, service, mock_jobs, sample_job_response):
        """Test cancelling a running job."""
        cancelled_response = {
            **sample_job_response,
            "currentState": "JOB_STATE_CANCELLING",
            "requestedState": "JOB_STATE_CANCELLED",
        }
        mock_request = mock.MagicMock()
        mock_jobs.update.return_value = mock_request
        mock_request.execute.return_value = cancelled_response

        job = service.cancel_job(LOCATION, JOB_ID)

        mock_jobs.update.assert_called_once_with(
            projectId=PROJECT_ID,
            location=LOCATION,
            jobId=JOB_ID,
            body={"requestedState": "JOB_STATE_CANCELLED"},
        )
        assert isinstance(job, DataflowJob)

    def test_cancel_job_not_found(self, service, mock_jobs):
        """Test cancelling a job that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_jobs.update.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.cancel_job(LOCATION, JOB_ID)


class TestDrainJob:
    def test_drain_job(self, service, mock_jobs, sample_streaming_job_response):
        """Test draining a streaming job."""
        drained_response = {
            **sample_streaming_job_response,
            "currentState": "JOB_STATE_DRAINING",
            "requestedState": "JOB_STATE_DRAINED",
        }
        mock_request = mock.MagicMock()
        mock_jobs.update.return_value = mock_request
        mock_request.execute.return_value = drained_response

        job = service.drain_job(LOCATION, JOB_ID)

        mock_jobs.update.assert_called_once_with(
            projectId=PROJECT_ID,
            location=LOCATION,
            jobId=JOB_ID,
            body={"requestedState": "JOB_STATE_DRAINED"},
        )
        assert isinstance(job, DataflowJob)

    def test_drain_job_not_found(self, service, mock_jobs):
        """Test draining a job that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_jobs.update.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.drain_job(LOCATION, JOB_ID)


class TestLaunchTemplate:
    def test_launch_template(
        self, service, mock_templates, sample_template_response
    ):
        """Test launching a template."""
        mock_request = mock.MagicMock()
        mock_templates.launch.return_value = mock_request
        mock_request.execute.return_value = sample_template_response

        result = service.launch_template(
            LOCATION, TEMPLATE_GCS_PATH, JOB_NAME
        )

        mock_templates.launch.assert_called_once_with(
            projectId=PROJECT_ID,
            location=LOCATION,
            gcsPath=TEMPLATE_GCS_PATH,
            body={
                "launchParameters": {"jobName": JOB_NAME},
            },
        )
        assert isinstance(result, DataflowTemplate)
        assert result.name == JOB_NAME

    def test_launch_template_with_parameters(
        self, service, mock_templates, sample_template_response
    ):
        """Test launching a template with runtime parameters."""
        mock_request = mock.MagicMock()
        mock_templates.launch.return_value = mock_request
        mock_request.execute.return_value = sample_template_response

        params = {"inputFile": "gs://bucket/input.csv", "outputTable": "project:dataset.table"}

        result = service.launch_template(
            LOCATION, TEMPLATE_GCS_PATH, JOB_NAME, parameters=params
        )

        mock_templates.launch.assert_called_once_with(
            projectId=PROJECT_ID,
            location=LOCATION,
            gcsPath=TEMPLATE_GCS_PATH,
            body={
                "launchParameters": {
                    "jobName": JOB_NAME,
                    "parameters": params,
                },
            },
        )
        assert isinstance(result, DataflowTemplate)

    def test_launch_template_with_environment(
        self, service, mock_templates, sample_template_response
    ):
        """Test launching a template with environment configuration."""
        mock_request = mock.MagicMock()
        mock_templates.launch.return_value = mock_request
        mock_request.execute.return_value = sample_template_response

        env = {
            "tempLocation": "gs://bucket/temp",
            "machineType": "n1-standard-4",
            "maxWorkers": 10,
        }

        result = service.launch_template(
            LOCATION,
            TEMPLATE_GCS_PATH,
            JOB_NAME,
            environment=env,
        )

        mock_templates.launch.assert_called_once_with(
            projectId=PROJECT_ID,
            location=LOCATION,
            gcsPath=TEMPLATE_GCS_PATH,
            body={
                "launchParameters": {
                    "jobName": JOB_NAME,
                    "environment": env,
                },
            },
        )
        assert isinstance(result, DataflowTemplate)

    def test_launch_template_with_all_options(
        self, service, mock_templates, sample_template_response
    ):
        """Test launching a template with all options."""
        mock_request = mock.MagicMock()
        mock_templates.launch.return_value = mock_request
        mock_request.execute.return_value = sample_template_response

        params = {"inputFile": "gs://bucket/input.csv"}
        env = {"tempLocation": "gs://bucket/temp"}

        result = service.launch_template(
            LOCATION,
            TEMPLATE_GCS_PATH,
            JOB_NAME,
            parameters=params,
            environment=env,
        )

        mock_templates.launch.assert_called_once_with(
            projectId=PROJECT_ID,
            location=LOCATION,
            gcsPath=TEMPLATE_GCS_PATH,
            body={
                "launchParameters": {
                    "jobName": JOB_NAME,
                    "parameters": params,
                    "environment": env,
                },
            },
        )
        assert isinstance(result, DataflowTemplate)

    def test_launch_template_not_found(self, service, mock_templates):
        """Test launching a template that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_templates.launch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.launch_template(
                LOCATION, TEMPLATE_GCS_PATH, JOB_NAME
            )

    def test_launch_template_api_error(self, service, mock_templates):
        """Test launching a template when API returns an error."""
        mock_request = mock.MagicMock()
        mock_templates.launch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.launch_template(
                LOCATION, TEMPLATE_GCS_PATH, JOB_NAME
            )


class TestListJobMessages:
    def test_list_job_messages(
        self, service, mock_messages, sample_message_response
    ):
        """Test listing job messages."""
        mock_request = mock.MagicMock()
        mock_messages.list.return_value = mock_request
        mock_request.execute.return_value = sample_message_response
        mock_messages.list_next.return_value = None

        messages = service.list_job_messages(LOCATION, JOB_ID)

        mock_messages.list.assert_called_once_with(
            projectId=PROJECT_ID, location=LOCATION, jobId=JOB_ID
        )
        assert len(messages) == 2
        assert messages[0]["messageText"] == "Worker pool started."
        assert messages[1]["messageImportance"] == "JOB_MESSAGE_DETAILED"

    def test_list_job_messages_with_importance_filter(
        self, service, mock_messages, sample_message_response
    ):
        """Test listing job messages with minimum importance filter."""
        mock_request = mock.MagicMock()
        mock_messages.list.return_value = mock_request
        mock_request.execute.return_value = sample_message_response
        mock_messages.list_next.return_value = None

        messages = service.list_job_messages(
            LOCATION, JOB_ID, minimum_importance="JOB_MESSAGE_WARNING"
        )

        mock_messages.list.assert_called_once_with(
            projectId=PROJECT_ID,
            location=LOCATION,
            jobId=JOB_ID,
            minimumImportance="JOB_MESSAGE_WARNING",
        )
        assert len(messages) == 2

    def test_list_job_messages_empty(self, service, mock_messages):
        """Test listing job messages when none exist."""
        mock_request = mock.MagicMock()
        mock_messages.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_messages.list_next.return_value = None

        messages = service.list_job_messages(LOCATION, JOB_ID)
        assert len(messages) == 0

    def test_list_job_messages_pagination(
        self, service, mock_messages, sample_message_response
    ):
        """Test listing job messages with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_messages.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = sample_message_response

        mock_messages.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "jobMessages": [
                {
                    "id": "msg-3",
                    "time": "2026-03-31T10:00:03Z",
                    "messageText": "Job completed.",
                    "messageImportance": "JOB_MESSAGE_BASIC",
                }
            ]
        }

        messages = service.list_job_messages(LOCATION, JOB_ID)
        assert len(messages) == 3


class TestDataflowJobModel:
    def test_from_api_response(self, sample_job_response):
        """Test creating a DataflowJob from API response."""
        job = DataflowJob.from_api_response(sample_job_response)

        assert job.id == JOB_ID
        assert job.name == JOB_NAME
        assert job.project == PROJECT_ID
        assert job.location == LOCATION
        assert job.type == "dataflow.job"
        assert job.job_type == "JOB_TYPE_BATCH"
        assert job.current_state == "JOB_STATE_RUNNING"
        assert job.requested_state == "JOB_STATE_RUNNING"
        assert job.pipeline_description is not None
        assert job.stage_states is not None
        assert len(job.stage_states) == 1
        assert job.environment is not None
        assert job.sdk_pipeline_options is not None
        assert job.temp_files is not None
        assert len(job.temp_files) == 2

    def test_from_api_response_minimal(self):
        """Test creating a DataflowJob from minimal API response."""
        response = {"id": JOB_ID, "name": JOB_NAME, "projectId": PROJECT_ID}
        job = DataflowJob.from_api_response(response)

        assert job.id == JOB_ID
        assert job.name == JOB_NAME
        assert job.job_type == ""
        assert job.current_state == ""
        assert job.requested_state is None
        assert job.pipeline_description is None
        assert job.stage_states is None
        assert job.environment is None
        assert job.sdk_pipeline_options is None
        assert job.temp_files is None

    def test_from_api_response_with_project_id_override(self, sample_job_response):
        """Test that explicit project_id overrides response value."""
        job = DataflowJob.from_api_response(
            sample_job_response, project_id="override-project"
        )
        assert job.project == "override-project"

    def test_get_tag(self, sample_job_response):
        """Test getting tags from a DataflowJob."""
        job = DataflowJob.from_api_response(sample_job_response)

        assert job.get_tag("env") == "test"
        assert job.get_tag("team") == "data-eng"
        assert job.get_tag("missing") == ""
        assert job.get_tag("missing", "default") == "default"

    def test_get_tag_no_labels(self):
        """Test getting tags when no labels exist."""
        response = {"id": JOB_ID, "name": JOB_NAME, "projectId": PROJECT_ID}
        job = DataflowJob.from_api_response(response)

        assert job.get_tag("env") == ""
        assert job.get_tag("env", "fallback") == "fallback"

    def test_streaming_job(self, sample_streaming_job_response):
        """Test creating a streaming job from API response."""
        job = DataflowJob.from_api_response(sample_streaming_job_response)

        assert job.job_type == "JOB_TYPE_STREAMING"
        assert job.name == "test-streaming-job"

    def test_to_dict(self, sample_job_response):
        """Test converting a DataflowJob to dictionary."""
        job = DataflowJob.from_api_response(sample_job_response)
        result = job.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == JOB_ID
        assert result["name"] == JOB_NAME
        assert result["location"] == LOCATION


class TestDataflowTemplateModel:
    def test_from_api_response(self, sample_template_response):
        """Test creating a DataflowTemplate from API response."""
        template = DataflowTemplate.from_api_response(sample_template_response)

        assert template.name == JOB_NAME
        assert template.id == JOB_ID
        assert template.project == PROJECT_ID
        assert template.location == LOCATION
        assert template.type == "dataflow.template"
        assert template.metadata is not None
        assert template.metadata["name"] == "Test Template"

    def test_from_api_response_minimal(self):
        """Test creating a DataflowTemplate from minimal API response."""
        response = {
            "job": {
                "id": JOB_ID,
                "name": JOB_NAME,
                "projectId": PROJECT_ID,
            }
        }
        template = DataflowTemplate.from_api_response(response)

        assert template.name == JOB_NAME
        assert template.id == JOB_ID
        assert template.metadata is None
        assert template.runtime_parameters is None

    def test_from_api_response_with_project_id_override(
        self, sample_template_response
    ):
        """Test that explicit project_id overrides response value."""
        template = DataflowTemplate.from_api_response(
            sample_template_response, project_id="override-project"
        )
        assert template.project == "override-project"

    def test_get_tag(self, sample_template_response):
        """Test getting tags from a DataflowTemplate."""
        template = DataflowTemplate.from_api_response(sample_template_response)

        assert template.get_tag("template") == "test"
        assert template.get_tag("missing") == ""
        assert template.get_tag("missing", "default") == "default"

    def test_get_tag_no_labels(self):
        """Test getting tags when no labels exist."""
        response = {
            "job": {
                "id": JOB_ID,
                "name": JOB_NAME,
                "projectId": PROJECT_ID,
            }
        }
        template = DataflowTemplate.from_api_response(response)

        assert template.get_tag("key") == ""
        assert template.get_tag("key", "fallback") == "fallback"

    def test_to_dict(self, sample_template_response):
        """Test converting a DataflowTemplate to dictionary."""
        template = DataflowTemplate.from_api_response(sample_template_response)
        result = template.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == JOB_NAME
        assert result["location"] == LOCATION
