"""Tests for Cloud Deploy service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.cloud_deploy import CloudDeployService
from gcpoto.models.cloud_deploy import DeliveryPipeline, Release, Rollout
from gcpoto.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
PIPELINE_NAME = "test-pipeline"
RELEASE_NAME = "release-001"
ROLLOUT_NAME = "rollout-001"

LOCATION_PATH = f"projects/{PROJECT_ID}/locations/{LOCATION}"
PIPELINE_PATH = f"{LOCATION_PATH}/deliveryPipelines/{PIPELINE_NAME}"
RELEASE_PATH = f"{PIPELINE_PATH}/releases/{RELEASE_NAME}"
ROLLOUT_PATH = f"{RELEASE_PATH}/rollouts/{ROLLOUT_NAME}"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().locations().deliveryPipelines() chain
        mock_pipelines = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.deliveryPipelines.return_value = (
            mock_pipelines
        )

        # Set up .releases() chain
        mock_releases = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.deliveryPipelines.return_value.releases.return_value = (
            mock_releases
        )

        # Set up .releases().rollouts() chain
        mock_rollouts = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.deliveryPipelines.return_value.releases.return_value.rollouts.return_value = (
            mock_rollouts
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a CloudDeployService with mocked client."""
    return CloudDeployService(project_id=PROJECT_ID)


@pytest.fixture
def mock_pipelines(mock_google_client):
    """Shortcut to mock pipelines resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .deliveryPipelines.return_value
    )


@pytest.fixture
def mock_releases(mock_google_client):
    """Shortcut to mock releases resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .deliveryPipelines.return_value.releases.return_value
    )


@pytest.fixture
def mock_rollouts(mock_google_client):
    """Shortcut to mock rollouts resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .deliveryPipelines.return_value.releases.return_value
        .rollouts.return_value
    )


@pytest.fixture
def sample_pipeline_response():
    """Sample Cloud Deploy pipeline API response."""
    return {
        "name": PIPELINE_PATH,
        "description": "Test delivery pipeline",
        "serialPipeline": {
            "stages": [
                {"targetId": "dev", "profiles": ["dev"]},
                {"targetId": "prod", "profiles": ["prod"]},
            ],
        },
        "condition": {"pipelineReadyCondition": {"status": True}},
        "labels": {"env": "test", "team": "platform"},
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T11:00:00Z",
    }


@pytest.fixture
def sample_release_response():
    """Sample Cloud Deploy release API response."""
    return {
        "name": RELEASE_PATH,
        "description": "Test release",
        "skaffoldConfigUri": "gs://my-bucket/skaffold.yaml",
        "skaffoldConfigPath": "skaffold.yaml",
        "renderState": "SUCCEEDED",
        "deliveryPipelineSnapshot": {
            "serialPipeline": {
                "stages": [{"targetId": "dev"}],
            },
        },
        "labels": {"version": "v1.0.0"},
        "createTime": "2026-03-31T12:00:00Z",
        "updateTime": "2026-03-31T12:30:00Z",
    }


@pytest.fixture
def sample_rollout_response():
    """Sample Cloud Deploy rollout API response."""
    return {
        "name": ROLLOUT_PATH,
        "targetId": "dev",
        "state": "SUCCEEDED",
        "deployStartTime": "2026-03-31T13:00:00Z",
        "deployEndTime": "2026-03-31T13:05:00Z",
        "labels": {"deploy": "auto"},
        "createTime": "2026-03-31T12:59:00Z",
        "updateTime": "2026-03-31T13:05:00Z",
    }


class TestCloudDeployServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the CloudDeployService."""
        from googleapiclient.discovery import build

        svc = CloudDeployService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("clouddeploy", "v1", credentials=None)

    def test_init_with_credentials_file(self, mock_google_client):
        """Test initializing with a credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = CloudDeployService(
                project_id=PROJECT_ID, credentials_file="/path/to/creds.json"
            )
            assert svc.project_id == PROJECT_ID
            mock_creds.assert_called_once()


class TestListPipelines:
    def test_list_pipelines(self, service, mock_pipelines, sample_pipeline_response):
        """Test listing delivery pipelines."""
        mock_request = mock.MagicMock()
        mock_pipelines.list.return_value = mock_request
        mock_request.execute.return_value = {
            "deliveryPipelines": [sample_pipeline_response, sample_pipeline_response]
        }
        mock_pipelines.list_next.return_value = None

        pipelines = service.list_pipelines(LOCATION)

        mock_pipelines.list.assert_called_once_with(parent=LOCATION_PATH)
        assert len(pipelines) == 2
        assert isinstance(pipelines[0], DeliveryPipeline)
        assert pipelines[0].name == PIPELINE_NAME
        assert pipelines[0].project == PROJECT_ID
        assert pipelines[0].location == LOCATION

    def test_list_pipelines_empty(self, service, mock_pipelines):
        """Test listing pipelines when none exist."""
        mock_request = mock.MagicMock()
        mock_pipelines.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_pipelines.list_next.return_value = None

        pipelines = service.list_pipelines(LOCATION)
        assert len(pipelines) == 0

    def test_list_pipelines_pagination(
        self, service, mock_pipelines, sample_pipeline_response
    ):
        """Test listing pipelines with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_pipelines.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "deliveryPipelines": [sample_pipeline_response]
        }

        mock_pipelines.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "deliveryPipelines": [sample_pipeline_response]
        }

        pipelines = service.list_pipelines(LOCATION)
        assert len(pipelines) == 2


class TestGetPipeline:
    def test_get_pipeline(self, service, mock_pipelines, sample_pipeline_response):
        """Test getting a specific pipeline."""
        mock_request = mock.MagicMock()
        mock_pipelines.get.return_value = mock_request
        mock_request.execute.return_value = sample_pipeline_response

        pipeline = service.get_pipeline(LOCATION, PIPELINE_NAME)

        mock_pipelines.get.assert_called_once_with(name=PIPELINE_PATH)
        assert isinstance(pipeline, DeliveryPipeline)
        assert pipeline.name == PIPELINE_NAME
        assert pipeline.description == "Test delivery pipeline"
        assert pipeline.serial_pipeline == sample_pipeline_response["serialPipeline"]

    def test_get_pipeline_not_found(self, service, mock_pipelines):
        """Test getting a pipeline that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_pipelines.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_pipeline(LOCATION, PIPELINE_NAME)

    def test_get_pipeline_with_full_path(
        self, service, mock_pipelines, sample_pipeline_response
    ):
        """Test getting a pipeline using a full resource path."""
        mock_request = mock.MagicMock()
        mock_pipelines.get.return_value = mock_request
        mock_request.execute.return_value = sample_pipeline_response

        service.get_pipeline(LOCATION, PIPELINE_PATH)
        mock_pipelines.get.assert_called_once_with(name=PIPELINE_PATH)


class TestCreatePipeline:
    def test_create_pipeline(self, service, mock_pipelines, sample_pipeline_response):
        """Test creating a new pipeline."""
        mock_request = mock.MagicMock()
        mock_pipelines.create.return_value = mock_request
        mock_request.execute.return_value = sample_pipeline_response

        serial_pipeline = {
            "stages": [
                {"targetId": "dev", "profiles": ["dev"]},
                {"targetId": "prod", "profiles": ["prod"]},
            ],
        }

        pipeline = service.create_pipeline(
            LOCATION,
            PIPELINE_NAME,
            serial_pipeline=serial_pipeline,
            description="Test delivery pipeline",
            labels={"env": "test"},
        )

        mock_pipelines.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={
                "serialPipeline": serial_pipeline,
                "description": "Test delivery pipeline",
                "labels": {"env": "test"},
            },
            deliveryPipelineId=PIPELINE_NAME,
        )
        assert isinstance(pipeline, DeliveryPipeline)
        assert pipeline.name == PIPELINE_NAME

    def test_create_pipeline_minimal(
        self, service, mock_pipelines, sample_pipeline_response
    ):
        """Test creating a pipeline with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_pipelines.create.return_value = mock_request
        mock_request.execute.return_value = sample_pipeline_response

        pipeline = service.create_pipeline(LOCATION, PIPELINE_NAME)

        mock_pipelines.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={},
            deliveryPipelineId=PIPELINE_NAME,
        )
        assert isinstance(pipeline, DeliveryPipeline)

    def test_create_pipeline_already_exists(self, service, mock_pipelines):
        """Test creating a pipeline that already exists."""
        mock_request = mock.MagicMock()
        mock_pipelines.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_pipeline(LOCATION, PIPELINE_NAME)


class TestDeletePipeline:
    def test_delete_pipeline(self, service, mock_pipelines):
        """Test deleting a pipeline."""
        mock_request = mock.MagicMock()
        mock_pipelines.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_pipeline(LOCATION, PIPELINE_NAME)

        mock_pipelines.delete.assert_called_once_with(name=PIPELINE_PATH)
        assert result is True

    def test_delete_pipeline_not_found(self, service, mock_pipelines):
        """Test deleting a pipeline that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_pipelines.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_pipeline(LOCATION, PIPELINE_NAME)


class TestListReleases:
    def test_list_releases(self, service, mock_releases, sample_release_response):
        """Test listing releases for a pipeline."""
        mock_request = mock.MagicMock()
        mock_releases.list.return_value = mock_request
        mock_request.execute.return_value = {
            "releases": [sample_release_response, sample_release_response]
        }
        mock_releases.list_next.return_value = None

        releases = service.list_releases(LOCATION, PIPELINE_NAME)

        mock_releases.list.assert_called_once_with(parent=PIPELINE_PATH)
        assert len(releases) == 2
        assert isinstance(releases[0], Release)
        assert releases[0].name == RELEASE_NAME
        assert releases[0].pipeline_name == PIPELINE_NAME

    def test_list_releases_empty(self, service, mock_releases):
        """Test listing releases when none exist."""
        mock_request = mock.MagicMock()
        mock_releases.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_releases.list_next.return_value = None

        releases = service.list_releases(LOCATION, PIPELINE_NAME)
        assert len(releases) == 0


class TestGetRelease:
    def test_get_release(self, service, mock_releases, sample_release_response):
        """Test getting a specific release."""
        mock_request = mock.MagicMock()
        mock_releases.get.return_value = mock_request
        mock_request.execute.return_value = sample_release_response

        release = service.get_release(LOCATION, PIPELINE_NAME, RELEASE_NAME)

        mock_releases.get.assert_called_once_with(name=RELEASE_PATH)
        assert isinstance(release, Release)
        assert release.name == RELEASE_NAME
        assert release.skaffold_config_uri == "gs://my-bucket/skaffold.yaml"
        assert release.render_state == "SUCCEEDED"

    def test_get_release_not_found(self, service, mock_releases):
        """Test getting a release that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_releases.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_release(LOCATION, PIPELINE_NAME, RELEASE_NAME)


class TestCreateRelease:
    def test_create_release(self, service, mock_releases, sample_release_response):
        """Test creating a new release."""
        mock_request = mock.MagicMock()
        mock_releases.create.return_value = mock_request
        mock_request.execute.return_value = sample_release_response

        release = service.create_release(
            LOCATION,
            PIPELINE_NAME,
            RELEASE_NAME,
            skaffold_config_uri="gs://my-bucket/skaffold.yaml",
            skaffold_config_path="skaffold.yaml",
        )

        mock_releases.create.assert_called_once_with(
            parent=PIPELINE_PATH,
            body={
                "skaffoldConfigUri": "gs://my-bucket/skaffold.yaml",
                "skaffoldConfigPath": "skaffold.yaml",
            },
            releaseId=RELEASE_NAME,
        )
        assert isinstance(release, Release)
        assert release.name == RELEASE_NAME

    def test_create_release_minimal(
        self, service, mock_releases, sample_release_response
    ):
        """Test creating a release with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_releases.create.return_value = mock_request
        mock_request.execute.return_value = sample_release_response

        release = service.create_release(
            LOCATION,
            PIPELINE_NAME,
            RELEASE_NAME,
            skaffold_config_uri="gs://my-bucket/skaffold.yaml",
        )

        mock_releases.create.assert_called_once_with(
            parent=PIPELINE_PATH,
            body={"skaffoldConfigUri": "gs://my-bucket/skaffold.yaml"},
            releaseId=RELEASE_NAME,
        )
        assert isinstance(release, Release)

    def test_create_release_already_exists(self, service, mock_releases):
        """Test creating a release that already exists."""
        mock_request = mock.MagicMock()
        mock_releases.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_release(
                LOCATION,
                PIPELINE_NAME,
                RELEASE_NAME,
                skaffold_config_uri="gs://my-bucket/skaffold.yaml",
            )


class TestListRollouts:
    def test_list_rollouts(self, service, mock_rollouts, sample_rollout_response):
        """Test listing rollouts for a release."""
        mock_request = mock.MagicMock()
        mock_rollouts.list.return_value = mock_request
        mock_request.execute.return_value = {
            "rollouts": [sample_rollout_response, sample_rollout_response]
        }
        mock_rollouts.list_next.return_value = None

        rollouts = service.list_rollouts(
            LOCATION, PIPELINE_NAME, RELEASE_NAME
        )

        mock_rollouts.list.assert_called_once_with(parent=RELEASE_PATH)
        assert len(rollouts) == 2
        assert isinstance(rollouts[0], Rollout)
        assert rollouts[0].name == ROLLOUT_NAME
        assert rollouts[0].target_id == "dev"
        assert rollouts[0].state == "SUCCEEDED"

    def test_list_rollouts_empty(self, service, mock_rollouts):
        """Test listing rollouts when none exist."""
        mock_request = mock.MagicMock()
        mock_rollouts.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_rollouts.list_next.return_value = None

        rollouts = service.list_rollouts(
            LOCATION, PIPELINE_NAME, RELEASE_NAME
        )
        assert len(rollouts) == 0


class TestGetRollout:
    def test_get_rollout(self, service, mock_rollouts, sample_rollout_response):
        """Test getting a specific rollout."""
        mock_request = mock.MagicMock()
        mock_rollouts.get.return_value = mock_request
        mock_request.execute.return_value = sample_rollout_response

        rollout = service.get_rollout(
            LOCATION, PIPELINE_NAME, RELEASE_NAME, ROLLOUT_NAME
        )

        mock_rollouts.get.assert_called_once_with(name=ROLLOUT_PATH)
        assert isinstance(rollout, Rollout)
        assert rollout.name == ROLLOUT_NAME
        assert rollout.target_id == "dev"
        assert rollout.state == "SUCCEEDED"

    def test_get_rollout_not_found(self, service, mock_rollouts):
        """Test getting a rollout that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_rollouts.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_rollout(
                LOCATION, PIPELINE_NAME, RELEASE_NAME, ROLLOUT_NAME
            )


class TestCreateRollout:
    def test_create_rollout(self, service, mock_rollouts, sample_rollout_response):
        """Test creating a new rollout."""
        mock_request = mock.MagicMock()
        mock_rollouts.create.return_value = mock_request
        mock_request.execute.return_value = sample_rollout_response

        rollout = service.create_rollout(
            LOCATION, PIPELINE_NAME, RELEASE_NAME, ROLLOUT_NAME, "dev"
        )

        mock_rollouts.create.assert_called_once_with(
            parent=RELEASE_PATH,
            body={"targetId": "dev"},
            rolloutId=ROLLOUT_NAME,
        )
        assert isinstance(rollout, Rollout)
        assert rollout.name == ROLLOUT_NAME
        assert rollout.target_id == "dev"

    def test_create_rollout_already_exists(self, service, mock_rollouts):
        """Test creating a rollout that already exists."""
        mock_request = mock.MagicMock()
        mock_rollouts.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_rollout(
                LOCATION, PIPELINE_NAME, RELEASE_NAME, ROLLOUT_NAME, "dev"
            )


class TestDeliveryPipelineModel:
    def test_from_api_response(self, sample_pipeline_response):
        """Test creating a DeliveryPipeline from API response."""
        pipeline = DeliveryPipeline.from_api_response(sample_pipeline_response)

        assert pipeline.name == PIPELINE_NAME
        assert pipeline.project == PROJECT_ID
        assert pipeline.location == LOCATION
        assert pipeline.description == "Test delivery pipeline"
        assert pipeline.serial_pipeline == sample_pipeline_response["serialPipeline"]
        assert pipeline.condition == sample_pipeline_response["condition"]
        assert pipeline.id == PIPELINE_PATH
        assert pipeline.type == "clouddeploy.deliveryPipeline"

    def test_from_api_response_minimal(self):
        """Test creating a DeliveryPipeline from minimal API response."""
        response = {"name": PIPELINE_PATH}
        pipeline = DeliveryPipeline.from_api_response(response)

        assert pipeline.name == PIPELINE_NAME
        assert pipeline.description is None
        assert pipeline.serial_pipeline is None
        assert pipeline.condition is None

    def test_get_tag(self, sample_pipeline_response):
        """Test getting tags from a DeliveryPipeline."""
        pipeline = DeliveryPipeline.from_api_response(sample_pipeline_response)

        assert pipeline.get_tag("env") == "test"
        assert pipeline.get_tag("team") == "platform"
        assert pipeline.get_tag("missing") == ""
        assert pipeline.get_tag("missing", "default") == "default"


class TestReleaseModel:
    def test_from_api_response(self, sample_release_response):
        """Test creating a Release from API response."""
        release = Release.from_api_response(sample_release_response)

        assert release.name == RELEASE_NAME
        assert release.project == PROJECT_ID
        assert release.location == LOCATION
        assert release.pipeline_name == PIPELINE_NAME
        assert release.description == "Test release"
        assert release.skaffold_config_uri == "gs://my-bucket/skaffold.yaml"
        assert release.skaffold_config_path == "skaffold.yaml"
        assert release.render_state == "SUCCEEDED"
        assert release.id == RELEASE_PATH
        assert release.type == "clouddeploy.release"

    def test_from_api_response_minimal(self):
        """Test creating a Release from minimal API response."""
        response = {"name": RELEASE_PATH}
        release = Release.from_api_response(response)

        assert release.name == RELEASE_NAME
        assert release.description is None
        assert release.skaffold_config_uri is None
        assert release.render_state is None

    def test_get_tag(self, sample_release_response):
        """Test getting tags from a Release."""
        release = Release.from_api_response(sample_release_response)

        assert release.get_tag("version") == "v1.0.0"
        assert release.get_tag("missing") == ""
        assert release.get_tag("missing", "default") == "default"


class TestRolloutModel:
    def test_from_api_response(self, sample_rollout_response):
        """Test creating a Rollout from API response."""
        rollout = Rollout.from_api_response(sample_rollout_response)

        assert rollout.name == ROLLOUT_NAME
        assert rollout.project == PROJECT_ID
        assert rollout.location == LOCATION
        assert rollout.pipeline_name == PIPELINE_NAME
        assert rollout.release_name == RELEASE_NAME
        assert rollout.target_id == "dev"
        assert rollout.state == "SUCCEEDED"
        assert rollout.id == ROLLOUT_PATH
        assert rollout.type == "clouddeploy.rollout"

    def test_from_api_response_minimal(self):
        """Test creating a Rollout from minimal API response."""
        response = {"name": ROLLOUT_PATH}
        rollout = Rollout.from_api_response(response)

        assert rollout.name == ROLLOUT_NAME
        assert rollout.target_id == ""
        assert rollout.state == ""
        assert rollout.deploy_start_time is None
        assert rollout.deploy_end_time is None


class TestPathFormatting:
    def test_format_location_path(self, service):
        """Test location path formatting."""
        assert service._format_location_path(LOCATION) == LOCATION_PATH

    def test_format_pipeline_path(self, service):
        """Test pipeline path formatting."""
        assert (
            service._format_pipeline_path(LOCATION, PIPELINE_NAME)
            == PIPELINE_PATH
        )

    def test_format_pipeline_path_already_formatted(self, service):
        """Test that already-formatted pipeline paths are returned as-is."""
        assert (
            service._format_pipeline_path(LOCATION, PIPELINE_PATH)
            == PIPELINE_PATH
        )

    def test_format_release_path(self, service):
        """Test release path formatting."""
        assert (
            service._format_release_path(
                LOCATION, PIPELINE_NAME, RELEASE_NAME
            )
            == RELEASE_PATH
        )

    def test_format_release_path_already_formatted(self, service):
        """Test that already-formatted release paths are returned as-is."""
        assert (
            service._format_release_path(
                LOCATION, PIPELINE_NAME, RELEASE_PATH
            )
            == RELEASE_PATH
        )

    def test_format_rollout_path(self, service):
        """Test rollout path formatting."""
        assert (
            service._format_rollout_path(
                LOCATION, PIPELINE_NAME, RELEASE_NAME, ROLLOUT_NAME
            )
            == ROLLOUT_PATH
        )

    def test_format_rollout_path_already_formatted(self, service):
        """Test that already-formatted rollout paths are returned as-is."""
        assert (
            service._format_rollout_path(
                LOCATION, PIPELINE_NAME, RELEASE_NAME, ROLLOUT_PATH
            )
            == ROLLOUT_PATH
        )
