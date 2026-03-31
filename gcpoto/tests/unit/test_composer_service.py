"""Tests for Composer service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.composer import ComposerService
from gcpoto.models.composer import ComposerEnvironment
from gcpoto.exceptions import ResourceNotFoundError, APIError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
ENVIRONMENT_NAME = "my-composer-env"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_environments = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.environments.return_value = (
            mock_environments
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a ComposerService with mocked client."""
    return ComposerService(project_id=PROJECT_ID)


@pytest.fixture
def mock_environments(mock_google_client):
    """Shortcut to mock environments resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .environments.return_value
    )


@pytest.fixture
def sample_environment_response():
    """Sample environment API response."""
    return {
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/environments/{ENVIRONMENT_NAME}",
        "state": "RUNNING",
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T11:00:00Z",
        "config": {
            "softwareConfig": {
                "imageVersion": "composer-2.5.0-airflow-2.6.3",
                "airflowConfigOverrides": {
                    "core-dags_are_paused_at_creation": "True"
                },
                "pypiPackages": {"pandas": ">=1.0"},
                "envVariables": {"ENV": "test"},
            },
            "nodeConfig": {
                "machineType": "n1-standard-2",
            },
            "gkeCluster": "projects/test-project/zones/us-central1-a/clusters/composer-cluster",
            "dagGcsPrefix": "gs://us-central1-my-composer-env-bucket/dags",
            "airflowUri": "https://abc123-tp.appspot.com",
        },
        "labels": {"env": "test", "team": "data"},
    }


class TestComposerServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the ComposerService."""
        from googleapiclient.discovery import build

        svc = ComposerService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("composer", "v1", credentials=None)


class TestListEnvironments:
    def test_list_environments(
        self, service, mock_environments, sample_environment_response
    ):
        """Test listing environments."""
        mock_request = mock.MagicMock()
        mock_environments.list.return_value = mock_request
        mock_request.execute.return_value = {
            "environments": [sample_environment_response]
        }
        mock_environments.list_next.return_value = None

        results = service.list_environments(LOCATION)

        mock_environments.list.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}"
        )
        assert len(results) == 1
        assert isinstance(results[0], ComposerEnvironment)
        assert results[0].state == "RUNNING"

    def test_list_environments_empty(self, service, mock_environments):
        """Test listing environments when none exist."""
        mock_request = mock.MagicMock()
        mock_environments.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_environments.list_next.return_value = None

        results = service.list_environments(LOCATION)
        assert len(results) == 0


class TestGetEnvironment:
    def test_get_environment(
        self, service, mock_environments, sample_environment_response
    ):
        """Test getting a specific environment."""
        mock_request = mock.MagicMock()
        mock_environments.get.return_value = mock_request
        mock_request.execute.return_value = sample_environment_response

        result = service.get_environment(LOCATION, ENVIRONMENT_NAME)

        assert isinstance(result, ComposerEnvironment)
        assert result.state == "RUNNING"
        assert result.config is not None
        assert "softwareConfig" in result.config

    def test_get_environment_not_found(self, service, mock_environments):
        """Test getting an environment that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_environments.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_environment(LOCATION, ENVIRONMENT_NAME)


class TestCreateEnvironment:
    def test_create_environment(
        self, service, mock_environments, sample_environment_response
    ):
        """Test creating a new environment."""
        mock_request = mock.MagicMock()
        mock_environments.create.return_value = mock_request
        mock_request.execute.return_value = sample_environment_response

        config = {
            "softwareConfig": {
                "imageVersion": "composer-2.5.0-airflow-2.6.3"
            }
        }
        result = service.create_environment(
            LOCATION, ENVIRONMENT_NAME, config
        )

        mock_environments.create.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
            body={
                "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/environments/{ENVIRONMENT_NAME}",
                "config": config,
            },
        )
        assert isinstance(result, ComposerEnvironment)

    def test_create_environment_with_labels(
        self, service, mock_environments, sample_environment_response
    ):
        """Test creating an environment with labels."""
        mock_request = mock.MagicMock()
        mock_environments.create.return_value = mock_request
        mock_request.execute.return_value = sample_environment_response

        config = {"softwareConfig": {"imageVersion": "composer-2.5.0"}}
        labels = {"env": "test"}
        result = service.create_environment(
            LOCATION, ENVIRONMENT_NAME, config, labels=labels
        )

        call_body = mock_environments.create.call_args[1]["body"]
        assert call_body["labels"] == labels
        assert isinstance(result, ComposerEnvironment)

    def test_create_environment_api_error(
        self, service, mock_environments
    ):
        """Test creating an environment when API returns an error."""
        mock_request = mock.MagicMock()
        mock_environments.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_environment(LOCATION, ENVIRONMENT_NAME, {})


class TestUpdateEnvironment:
    def test_update_environment(
        self, service, mock_environments, sample_environment_response
    ):
        """Test updating an environment."""
        mock_request = mock.MagicMock()
        mock_environments.patch.return_value = mock_request
        mock_request.execute.return_value = sample_environment_response

        update_config = {
            "config": {
                "softwareConfig": {
                    "pypiPackages": {"numpy": ">=1.0"}
                }
            }
        }
        result = service.update_environment(
            LOCATION,
            ENVIRONMENT_NAME,
            "config.softwareConfig.pypiPackages",
            update_config,
        )

        mock_environments.patch.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/environments/{ENVIRONMENT_NAME}",
            updateMask="config.softwareConfig.pypiPackages",
            body=update_config,
        )
        assert isinstance(result, ComposerEnvironment)

    def test_update_environment_not_found(
        self, service, mock_environments
    ):
        """Test updating an environment that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_environments.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_environment(
                LOCATION, ENVIRONMENT_NAME, "labels", {"labels": {}}
            )


class TestDeleteEnvironment:
    def test_delete_environment(self, service, mock_environments):
        """Test deleting an environment."""
        mock_environments.delete.return_value.execute.return_value = {}

        result = service.delete_environment(LOCATION, ENVIRONMENT_NAME)
        assert result is True

    def test_delete_environment_not_found(
        self, service, mock_environments
    ):
        """Test deleting an environment that doesn't exist."""
        mock_environments.delete.return_value.execute.side_effect = (
            HttpError(
                resp=mock.MagicMock(status=404), content=b"Not found"
            )
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_environment(LOCATION, ENVIRONMENT_NAME)


class TestComposerEnvironmentModel:
    def test_from_api_response(self, sample_environment_response):
        """Test creating a ComposerEnvironment from API response."""
        env = ComposerEnvironment.from_api_response(
            sample_environment_response
        )

        assert env.id == ENVIRONMENT_NAME
        assert env.location == LOCATION
        assert env.project == PROJECT_ID
        assert env.state == "RUNNING"
        assert env.config is not None
        assert "softwareConfig" in env.config
        assert env.type == "composer.environment"

    def test_from_api_response_minimal(self):
        """Test creating a ComposerEnvironment from minimal API response."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/environments/minimal"
        }
        env = ComposerEnvironment.from_api_response(response)

        assert env.id == "minimal"
        assert env.state == ""
        assert env.config == {}

    def test_get_tag(self, sample_environment_response):
        """Test getting tags from a ComposerEnvironment."""
        env = ComposerEnvironment.from_api_response(
            sample_environment_response
        )

        assert env.get_tag("env") == "test"
        assert env.get_tag("team") == "data"
        assert env.get_tag("missing") == ""
        assert env.get_tag("missing", "default") == "default"

    def test_get_tag_no_labels(self):
        """Test getting tags when no labels exist."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/environments/minimal"
        }
        env = ComposerEnvironment.from_api_response(response)

        assert env.get_tag("env") == ""
        assert env.get_tag("env", "fallback") == "fallback"

    def test_to_dict(self, sample_environment_response):
        """Test converting a ComposerEnvironment to dictionary."""
        env = ComposerEnvironment.from_api_response(
            sample_environment_response
        )
        result = env.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == ENVIRONMENT_NAME
        assert result["location"] == LOCATION
