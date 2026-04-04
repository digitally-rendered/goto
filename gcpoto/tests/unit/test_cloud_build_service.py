"""Tests for Cloud Build service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.cloud_build import CloudBuildService
from gcpoto.models.cloud_build import Build, BuildTrigger
from gcpoto.exceptions import ResourceNotFoundError, APIError


PROJECT_ID = "test-project"
BUILD_ID = "build-12345-abcde"
TRIGGER_ID = "trigger-67890-fghij"
TRIGGER_NAME = "my-build-trigger"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().builds() chain
        mock_builds = mock.MagicMock()
        mock_service.projects.return_value.builds.return_value = mock_builds

        # Set up projects().triggers() chain
        mock_triggers = mock.MagicMock()
        mock_service.projects.return_value.triggers.return_value = (
            mock_triggers
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a CloudBuildService with mocked client."""
    return CloudBuildService(project_id=PROJECT_ID)


@pytest.fixture
def sample_build_response():
    """Sample Cloud Build API response."""
    return {
        "id": BUILD_ID,
        "name": BUILD_ID,
        "projectId": PROJECT_ID,
        "status": "SUCCESS",
        "source": {
            "storageSource": {
                "bucket": "my-source-bucket",
                "object": "source.tar.gz",
            }
        },
        "steps": [
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": ["build", "-t", "gcr.io/test-project/my-image", "."],
            },
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": ["push", "gcr.io/test-project/my-image"],
            },
        ],
        "results": {
            "images": [
                {
                    "name": "gcr.io/test-project/my-image",
                    "digest": "sha256:abc123",
                }
            ],
            "buildStepImages": ["sha256:step1", "sha256:step2"],
        },
        "createTime": "2026-03-31T10:00:00Z",
        "startTime": "2026-03-31T10:00:05Z",
        "finishTime": "2026-03-31T10:05:00Z",
        "timeout": "600s",
        "images": ["gcr.io/test-project/my-image"],
        "artifacts": {
            "images": ["gcr.io/test-project/my-image"],
            "objects": {
                "location": "gs://my-bucket/artifacts",
                "paths": ["output.jar"],
            },
        },
        "logsBucket": "gs://my-logs-bucket",
        "sourceProvenance": {
            "resolvedStorageSource": {
                "bucket": "my-source-bucket",
                "object": "source.tar.gz",
                "generation": "123456",
            }
        },
        "options": {
            "machineType": "N1_HIGHCPU_8",
            "diskSizeGb": "100",
            "logging": "GCS_ONLY",
        },
        "substitutions": {"_IMAGE_TAG": "latest", "_REGION": "us-central1"},
        "labels": {"env": "test", "team": "platform"},
    }


@pytest.fixture
def sample_trigger_response():
    """Sample Cloud Build trigger API response."""
    return {
        "id": TRIGGER_ID,
        "name": TRIGGER_NAME,
        "projectId": PROJECT_ID,
        "description": "Build on push to main",
        "disabled": False,
        "substitutions": {"_DEPLOY_ENV": "staging"},
        "filename": "cloudbuild.yaml",
        "triggerTemplate": {
            "projectId": PROJECT_ID,
            "repoName": "my-repo",
            "branchName": "main",
        },
        "github": {
            "owner": "my-org",
            "name": "my-repo",
            "push": {"branch": "^main$"},
        },
        "pubsubConfig": {
            "topic": "projects/test-project/topics/build-trigger",
            "serviceAccountEmail": "sa@test-project.iam.gserviceaccount.com",
        },
        "webhookConfig": {
            "secret": "projects/test-project/secrets/webhook-secret/versions/1",
            "state": "ACTIVE",
        },
        "createTime": "2026-03-01T10:00:00Z",
        "updateTime": "2026-03-15T12:00:00Z",
        "labels": {"team": "platform"},
    }


@pytest.fixture
def mock_builds(mock_google_client):
    """Shortcut to mock builds resource."""
    return mock_google_client.projects.return_value.builds.return_value


@pytest.fixture
def mock_triggers(mock_google_client):
    """Shortcut to mock triggers resource."""
    return mock_google_client.projects.return_value.triggers.return_value


class TestCloudBuildServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the CloudBuildService."""
        from googleapiclient.discovery import build

        svc = CloudBuildService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("cloudbuild", "v1", credentials=None)

    def test_init_with_credentials_file(self, mock_google_client):
        """Test initializing with a credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = CloudBuildService(
                project_id=PROJECT_ID,
                credentials_file="/path/to/creds.json",
            )
            assert svc.project_id == PROJECT_ID
            mock_creds.assert_called_once()


class TestListBuilds:
    def test_list_builds(self, service, mock_builds, sample_build_response):
        """Test listing Cloud Build builds."""
        mock_request = mock.MagicMock()
        mock_builds.list.return_value = mock_request
        mock_request.execute.return_value = {
            "builds": [sample_build_response, sample_build_response]
        }
        mock_builds.list_next.return_value = None

        builds = service.list_builds()

        mock_builds.list.assert_called_once_with(projectId=PROJECT_ID)
        assert len(builds) == 2
        assert isinstance(builds[0], Build)
        assert builds[0].id == BUILD_ID
        assert builds[0].status == "SUCCESS"
        assert builds[0].project == PROJECT_ID

    def test_list_builds_with_filter(
        self, service, mock_builds, sample_build_response
    ):
        """Test listing builds with a filter string."""
        mock_request = mock.MagicMock()
        mock_builds.list.return_value = mock_request
        mock_request.execute.return_value = {
            "builds": [sample_build_response]
        }
        mock_builds.list_next.return_value = None

        builds = service.list_builds(filter_str='status="SUCCESS"')

        mock_builds.list.assert_called_once_with(
            projectId=PROJECT_ID, filter='status="SUCCESS"'
        )
        assert len(builds) == 1

    def test_list_builds_empty(self, service, mock_builds):
        """Test listing builds when none exist."""
        mock_request = mock.MagicMock()
        mock_builds.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_builds.list_next.return_value = None

        builds = service.list_builds()
        assert len(builds) == 0

    def test_list_builds_pagination(
        self, service, mock_builds, sample_build_response
    ):
        """Test listing builds with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_builds.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "builds": [sample_build_response]
        }

        mock_builds.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "builds": [sample_build_response]
        }

        builds = service.list_builds()
        assert len(builds) == 2


class TestGetBuild:
    def test_get_build(self, service, mock_builds, sample_build_response):
        """Test getting a specific build."""
        mock_request = mock.MagicMock()
        mock_builds.get.return_value = mock_request
        mock_request.execute.return_value = sample_build_response

        build_result = service.get_build(BUILD_ID)

        mock_builds.get.assert_called_once_with(
            projectId=PROJECT_ID, id=BUILD_ID
        )
        assert isinstance(build_result, Build)
        assert build_result.id == BUILD_ID
        assert build_result.status == "SUCCESS"
        assert build_result.source == sample_build_response["source"]
        assert len(build_result.steps) == 2
        assert build_result.results == sample_build_response["results"]
        assert build_result.timeout == "600s"
        assert build_result.images == ["gcr.io/test-project/my-image"]
        assert build_result.artifacts is not None
        assert build_result.logs_bucket == "gs://my-logs-bucket"
        assert build_result.source_provenance is not None
        assert build_result.options is not None
        assert build_result.substitutions == {
            "_IMAGE_TAG": "latest",
            "_REGION": "us-central1",
        }

    def test_get_build_not_found(self, service, mock_builds):
        """Test getting a build that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_builds.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_build(BUILD_ID)


class TestCreateBuild:
    def test_create_build(
        self, service, mock_builds, sample_build_response
    ):
        """Test creating a new build."""
        mock_request = mock.MagicMock()
        mock_builds.create.return_value = mock_request
        mock_request.execute.return_value = sample_build_response

        build_body = {
            "steps": [
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["build", "-t", "gcr.io/test-project/my-image", "."],
                }
            ],
            "images": ["gcr.io/test-project/my-image"],
        }

        build_result = service.create_build(build_body)

        mock_builds.create.assert_called_once_with(
            projectId=PROJECT_ID, body=build_body
        )
        assert isinstance(build_result, Build)
        assert build_result.id == BUILD_ID

    def test_create_build_api_error(self, service, mock_builds):
        """Test creating a build when API returns an error."""
        mock_request = mock.MagicMock()
        mock_builds.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_build({"steps": []})


class TestCancelBuild:
    def test_cancel_build(
        self, service, mock_builds, sample_build_response
    ):
        """Test cancelling a running build."""
        cancelled_response = {
            **sample_build_response,
            "status": "CANCELLED",
        }
        mock_request = mock.MagicMock()
        mock_builds.cancel.return_value = mock_request
        mock_request.execute.return_value = cancelled_response

        build_result = service.cancel_build(BUILD_ID)

        mock_builds.cancel.assert_called_once_with(
            projectId=PROJECT_ID, id=BUILD_ID, body={}
        )
        assert isinstance(build_result, Build)
        assert build_result.status == "CANCELLED"

    def test_cancel_build_not_found(self, service, mock_builds):
        """Test cancelling a build that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_builds.cancel.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.cancel_build(BUILD_ID)


class TestRetryBuild:
    def test_retry_build(
        self, service, mock_builds, sample_build_response
    ):
        """Test retrying a build."""
        retried_response = {
            **sample_build_response,
            "id": "build-retry-67890",
            "status": "QUEUED",
        }
        mock_request = mock.MagicMock()
        mock_builds.retry.return_value = mock_request
        mock_request.execute.return_value = retried_response

        build_result = service.retry_build(BUILD_ID)

        mock_builds.retry.assert_called_once_with(
            projectId=PROJECT_ID, id=BUILD_ID, body={}
        )
        assert isinstance(build_result, Build)
        assert build_result.status == "QUEUED"

    def test_retry_build_not_found(self, service, mock_builds):
        """Test retrying a build that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_builds.retry.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.retry_build(BUILD_ID)

    def test_retry_build_api_error(self, service, mock_builds):
        """Test retrying a build when API returns a non-404 error."""
        mock_request = mock.MagicMock()
        mock_builds.retry.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.retry_build(BUILD_ID)


class TestListTriggers:
    def test_list_triggers(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test listing Cloud Build triggers."""
        mock_request = mock.MagicMock()
        mock_triggers.list.return_value = mock_request
        mock_request.execute.return_value = {
            "triggers": [sample_trigger_response, sample_trigger_response]
        }
        mock_triggers.list_next.return_value = None

        triggers = service.list_triggers()

        mock_triggers.list.assert_called_once_with(projectId=PROJECT_ID)
        assert len(triggers) == 2
        assert isinstance(triggers[0], BuildTrigger)
        assert triggers[0].id == TRIGGER_ID
        assert triggers[0].name == TRIGGER_NAME
        assert triggers[0].project == PROJECT_ID

    def test_list_triggers_empty(self, service, mock_triggers):
        """Test listing triggers when none exist."""
        mock_request = mock.MagicMock()
        mock_triggers.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_triggers.list_next.return_value = None

        triggers = service.list_triggers()
        assert len(triggers) == 0

    def test_list_triggers_pagination(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test listing triggers with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_triggers.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "triggers": [sample_trigger_response]
        }

        mock_triggers.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "triggers": [sample_trigger_response]
        }

        triggers = service.list_triggers()
        assert len(triggers) == 2


class TestGetTrigger:
    def test_get_trigger(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test getting a specific trigger."""
        mock_request = mock.MagicMock()
        mock_triggers.get.return_value = mock_request
        mock_request.execute.return_value = sample_trigger_response

        trigger = service.get_trigger(TRIGGER_ID)

        mock_triggers.get.assert_called_once_with(
            projectId=PROJECT_ID, triggerId=TRIGGER_ID
        )
        assert isinstance(trigger, BuildTrigger)
        assert trigger.id == TRIGGER_ID
        assert trigger.name == TRIGGER_NAME
        assert trigger.description == "Build on push to main"
        assert trigger.disabled is False
        assert trigger.filename == "cloudbuild.yaml"
        assert trigger.trigger_template is not None
        assert trigger.github is not None
        assert trigger.pubsub_config is not None
        assert trigger.webhook_config is not None
        assert trigger.substitutions == {"_DEPLOY_ENV": "staging"}

    def test_get_trigger_not_found(self, service, mock_triggers):
        """Test getting a trigger that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_triggers.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_trigger(TRIGGER_ID)


class TestCreateTrigger:
    def test_create_trigger(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test creating a new trigger."""
        mock_request = mock.MagicMock()
        mock_triggers.create.return_value = mock_request
        mock_request.execute.return_value = sample_trigger_response

        trigger_body = {
            "name": TRIGGER_NAME,
            "description": "Build on push to main",
            "filename": "cloudbuild.yaml",
            "triggerTemplate": {
                "repoName": "my-repo",
                "branchName": "main",
            },
        }

        trigger = service.create_trigger(trigger_body)

        mock_triggers.create.assert_called_once_with(
            projectId=PROJECT_ID, body=trigger_body
        )
        assert isinstance(trigger, BuildTrigger)
        assert trigger.name == TRIGGER_NAME

    def test_create_trigger_api_error(self, service, mock_triggers):
        """Test creating a trigger when API returns an error."""
        mock_request = mock.MagicMock()
        mock_triggers.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_trigger({"name": "bad-trigger"})


class TestUpdateTrigger:
    def test_update_trigger(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test updating a trigger."""
        updated_response = {
            **sample_trigger_response,
            "description": "Updated description",
        }
        mock_request = mock.MagicMock()
        mock_triggers.patch.return_value = mock_request
        mock_request.execute.return_value = updated_response

        trigger_body = {
            "description": "Updated description",
            "filename": "cloudbuild.yaml",
        }

        trigger = service.update_trigger(TRIGGER_ID, trigger_body)

        mock_triggers.patch.assert_called_once_with(
            projectId=PROJECT_ID,
            triggerId=TRIGGER_ID,
            body=trigger_body,
        )
        assert isinstance(trigger, BuildTrigger)
        assert trigger.description == "Updated description"

    def test_update_trigger_not_found(self, service, mock_triggers):
        """Test updating a trigger that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_triggers.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_trigger(TRIGGER_ID, {"description": "new"})

    def test_update_trigger_api_error(self, service, mock_triggers):
        """Test updating a trigger when API returns a non-404 error."""
        mock_request = mock.MagicMock()
        mock_triggers.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.update_trigger(TRIGGER_ID, {"description": "new"})


class TestDeleteTrigger:
    def test_delete_trigger(self, service, mock_triggers):
        """Test deleting a trigger."""
        mock_triggers.delete.return_value.execute.return_value = {}

        result = service.delete_trigger(TRIGGER_ID)

        mock_triggers.delete.assert_called_once_with(
            projectId=PROJECT_ID, triggerId=TRIGGER_ID
        )
        assert result is True

    def test_delete_trigger_not_found(self, service, mock_triggers):
        """Test deleting a trigger that doesn't exist."""
        mock_triggers.delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_trigger(TRIGGER_ID)


class TestRunTrigger:
    def test_run_trigger(
        self, service, mock_triggers, sample_build_response
    ):
        """Test running a trigger."""
        mock_request = mock.MagicMock()
        mock_triggers.run.return_value = mock_request
        mock_request.execute.return_value = sample_build_response

        build_result = service.run_trigger(TRIGGER_ID)

        mock_triggers.run.assert_called_once_with(
            projectId=PROJECT_ID,
            triggerId=TRIGGER_ID,
            body={},
        )
        assert isinstance(build_result, Build)
        assert build_result.id == BUILD_ID

    def test_run_trigger_with_source(
        self, service, mock_triggers, sample_build_response
    ):
        """Test running a trigger with a source override."""
        mock_request = mock.MagicMock()
        mock_triggers.run.return_value = mock_request
        mock_request.execute.return_value = sample_build_response

        source = {
            "repoSource": {
                "repoName": "my-repo",
                "branchName": "feature-branch",
            }
        }

        build_result = service.run_trigger(TRIGGER_ID, source=source)

        mock_triggers.run.assert_called_once_with(
            projectId=PROJECT_ID,
            triggerId=TRIGGER_ID,
            body={"source": source},
        )
        assert isinstance(build_result, Build)

    def test_run_trigger_not_found(self, service, mock_triggers):
        """Test running a trigger that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_triggers.run.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.run_trigger(TRIGGER_ID)

    def test_run_trigger_api_error(self, service, mock_triggers):
        """Test running a trigger when API returns a non-404 error."""
        mock_request = mock.MagicMock()
        mock_triggers.run.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.run_trigger(TRIGGER_ID)


class TestBuildModel:
    def test_from_api_response(self, sample_build_response):
        """Test creating a Build from API response."""
        build_obj = Build.from_api_response(sample_build_response)

        assert build_obj.id == BUILD_ID
        assert build_obj.name == BUILD_ID
        assert build_obj.project == PROJECT_ID
        assert build_obj.type == "cloudbuild.build"
        assert build_obj.status == "SUCCESS"
        assert build_obj.source is not None
        assert len(build_obj.steps) == 2
        assert build_obj.results is not None
        assert build_obj.timeout == "600s"
        assert build_obj.images == ["gcr.io/test-project/my-image"]
        assert build_obj.artifacts is not None
        assert build_obj.logs_bucket == "gs://my-logs-bucket"
        assert build_obj.source_provenance is not None
        assert build_obj.options is not None
        assert build_obj.substitutions == {
            "_IMAGE_TAG": "latest",
            "_REGION": "us-central1",
        }

    def test_from_api_response_minimal(self):
        """Test creating a Build from minimal API response."""
        response = {
            "id": BUILD_ID,
            "projectId": PROJECT_ID,
            "steps": [{"name": "gcr.io/cloud-builders/docker"}],
        }
        build_obj = Build.from_api_response(response)

        assert build_obj.id == BUILD_ID
        assert build_obj.name == BUILD_ID
        assert build_obj.status == ""
        assert build_obj.source is None
        assert len(build_obj.steps) == 1
        assert build_obj.results is None
        assert build_obj.timeout is None
        assert build_obj.images is None
        assert build_obj.artifacts is None
        assert build_obj.logs_bucket is None
        assert build_obj.source_provenance is None
        assert build_obj.options is None
        assert build_obj.substitutions is None

    def test_from_api_response_with_project_id_override(
        self, sample_build_response
    ):
        """Test that explicit project_id overrides response value."""
        build_obj = Build.from_api_response(
            sample_build_response, project_id="override-project"
        )
        assert build_obj.project == "override-project"

    def test_get_tag(self, sample_build_response):
        """Test getting tags from a Build."""
        build_obj = Build.from_api_response(sample_build_response)

        assert build_obj.get_tag("env") == "test"
        assert build_obj.get_tag("team") == "platform"
        assert build_obj.get_tag("missing") == ""
        assert build_obj.get_tag("missing", "default") == "default"

    def test_get_tag_no_labels(self):
        """Test getting tags when no labels exist."""
        response = {
            "id": BUILD_ID,
            "projectId": PROJECT_ID,
            "steps": [],
        }
        build_obj = Build.from_api_response(response)

        assert build_obj.get_tag("env") == ""
        assert build_obj.get_tag("env", "fallback") == "fallback"

    def test_to_dict(self, sample_build_response):
        """Test converting a Build to dictionary."""
        build_obj = Build.from_api_response(sample_build_response)
        result = build_obj.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == BUILD_ID
        assert result["status"] == "SUCCESS"
        assert len(result["steps"]) == 2


class TestBuildTriggerModel:
    def test_from_api_response(self, sample_trigger_response):
        """Test creating a BuildTrigger from API response."""
        trigger = BuildTrigger.from_api_response(sample_trigger_response)

        assert trigger.id == TRIGGER_ID
        assert trigger.name == TRIGGER_NAME
        assert trigger.project == PROJECT_ID
        assert trigger.type == "cloudbuild.trigger"
        assert trigger.description == "Build on push to main"
        assert trigger.disabled is False
        assert trigger.substitutions == {"_DEPLOY_ENV": "staging"}
        assert trigger.filename == "cloudbuild.yaml"
        assert trigger.trigger_template is not None
        assert trigger.trigger_template["repoName"] == "my-repo"
        assert trigger.github is not None
        assert trigger.github["owner"] == "my-org"
        assert trigger.pubsub_config is not None
        assert trigger.webhook_config is not None

    def test_from_api_response_minimal(self):
        """Test creating a BuildTrigger from minimal API response."""
        response = {
            "id": TRIGGER_ID,
            "name": TRIGGER_NAME,
            "projectId": PROJECT_ID,
        }
        trigger = BuildTrigger.from_api_response(response)

        assert trigger.id == TRIGGER_ID
        assert trigger.name == TRIGGER_NAME
        assert trigger.description is None
        assert trigger.disabled is False
        assert trigger.substitutions is None
        assert trigger.filename is None
        assert trigger.trigger_template is None
        assert trigger.github is None
        assert trigger.pubsub_config is None
        assert trigger.webhook_config is None

    def test_from_api_response_with_project_id_override(
        self, sample_trigger_response
    ):
        """Test that explicit project_id overrides response value."""
        trigger = BuildTrigger.from_api_response(
            sample_trigger_response, project_id="override-project"
        )
        assert trigger.project == "override-project"

    def test_from_api_response_disabled_trigger(self):
        """Test creating a disabled BuildTrigger."""
        response = {
            "id": TRIGGER_ID,
            "name": TRIGGER_NAME,
            "projectId": PROJECT_ID,
            "disabled": True,
        }
        trigger = BuildTrigger.from_api_response(response)
        assert trigger.disabled is True

    def test_get_tag(self, sample_trigger_response):
        """Test getting tags from a BuildTrigger."""
        trigger = BuildTrigger.from_api_response(sample_trigger_response)

        assert trigger.get_tag("team") == "platform"
        assert trigger.get_tag("missing") == ""
        assert trigger.get_tag("missing", "default") == "default"

    def test_get_tag_no_labels(self):
        """Test getting tags when no labels exist."""
        response = {
            "id": TRIGGER_ID,
            "name": TRIGGER_NAME,
            "projectId": PROJECT_ID,
        }
        trigger = BuildTrigger.from_api_response(response)

        assert trigger.get_tag("key") == ""
        assert trigger.get_tag("key", "fallback") == "fallback"

    def test_to_dict(self, sample_trigger_response):
        """Test converting a BuildTrigger to dictionary."""
        trigger = BuildTrigger.from_api_response(sample_trigger_response)
        result = trigger.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == TRIGGER_ID
        assert result["name"] == TRIGGER_NAME
        assert result["description"] == "Build on push to main"
