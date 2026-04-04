"""Tests for Data Fusion service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.data_fusion import DataFusionService
from gcpoto.models.data_fusion import DataFusionInstance
from gcpoto.exceptions import ResourceNotFoundError, APIError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
INSTANCE_NAME = "my-instance"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.instances.return_value = (
            mock_instances
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a DataFusionService with mocked client."""
    return DataFusionService(project_id=PROJECT_ID)


@pytest.fixture
def mock_instances(mock_google_client):
    """Shortcut to mock instances resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .instances.return_value
    )


@pytest.fixture
def sample_instance_response():
    """Sample instance API response."""
    return {
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/{INSTANCE_NAME}",
        "type": "ENTERPRISE",
        "description": "Test Data Fusion instance",
        "enableStackdriverLogging": True,
        "enableStackdriverMonitoring": True,
        "privateInstance": False,
        "networkConfig": {"network": "default"},
        "state": "ACTIVE",
        "serviceEndpoint": "https://my-instance-test-project-dot-usc1.datafusion.googleusercontent.com",
        "apiEndpoint": "https://my-instance-test-project-dot-usc1.datafusion.googleusercontent.com/api",
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T11:00:00Z",
        "labels": {"env": "test", "team": "data"},
    }


class TestDataFusionServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the DataFusionService."""
        from googleapiclient.discovery import build

        svc = DataFusionService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with(
            "datafusion", "v1", credentials=None
        )


class TestListInstances:
    def test_list_instances(
        self, service, mock_instances, sample_instance_response
    ):
        """Test listing Data Fusion instances."""
        mock_request = mock.MagicMock()
        mock_instances.list.return_value = mock_request
        mock_request.execute.return_value = {
            "instances": [sample_instance_response]
        }
        mock_instances.list_next.return_value = None

        results = service.list_instances(LOCATION)

        mock_instances.list.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}"
        )
        assert len(results) == 1
        assert isinstance(results[0], DataFusionInstance)
        assert results[0].type_field == "ENTERPRISE"

    def test_list_instances_empty(self, service, mock_instances):
        """Test listing instances when none exist."""
        mock_request = mock.MagicMock()
        mock_instances.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_instances.list_next.return_value = None

        results = service.list_instances(LOCATION)
        assert len(results) == 0


class TestGetInstance:
    def test_get_instance(
        self, service, mock_instances, sample_instance_response
    ):
        """Test getting a specific instance."""
        mock_request = mock.MagicMock()
        mock_instances.get.return_value = mock_request
        mock_request.execute.return_value = sample_instance_response

        result = service.get_instance(LOCATION, INSTANCE_NAME)

        assert isinstance(result, DataFusionInstance)
        assert result.type_field == "ENTERPRISE"
        assert result.state == "ACTIVE"

    def test_get_instance_not_found(self, service, mock_instances):
        """Test getting an instance that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_instances.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_instance(LOCATION, INSTANCE_NAME)


class TestCreateInstance:
    def test_create_instance(
        self, service, mock_instances, sample_instance_response
    ):
        """Test creating a new instance."""
        mock_request = mock.MagicMock()
        mock_instances.create.return_value = mock_request
        mock_request.execute.return_value = sample_instance_response

        result = service.create_instance(
            LOCATION, INSTANCE_NAME, "ENTERPRISE", description="Test"
        )

        assert isinstance(result, DataFusionInstance)
        assert result.type_field == "ENTERPRISE"

    def test_create_instance_api_error(self, service, mock_instances):
        """Test creating an instance when API returns an error."""
        mock_request = mock.MagicMock()
        mock_instances.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_instance(
                LOCATION, INSTANCE_NAME, "BASIC"
            )


class TestUpdateInstance:
    def test_update_instance(
        self, service, mock_instances, sample_instance_response
    ):
        """Test updating an instance."""
        mock_request = mock.MagicMock()
        mock_instances.patch.return_value = mock_request
        mock_request.execute.return_value = sample_instance_response

        result = service.update_instance(
            LOCATION,
            INSTANCE_NAME,
            "description",
            {"description": "Updated"},
        )

        mock_instances.patch.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/{INSTANCE_NAME}",
            updateMask="description",
            body={"description": "Updated"},
        )
        assert isinstance(result, DataFusionInstance)

    def test_update_instance_not_found(self, service, mock_instances):
        """Test updating an instance that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_instances.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_instance(
                LOCATION,
                INSTANCE_NAME,
                "description",
                {"description": "Updated"},
            )


class TestDeleteInstance:
    def test_delete_instance(self, service, mock_instances):
        """Test deleting an instance."""
        mock_instances.delete.return_value.execute.return_value = {}

        result = service.delete_instance(LOCATION, INSTANCE_NAME)
        assert result is True

    def test_delete_instance_not_found(self, service, mock_instances):
        """Test deleting an instance that doesn't exist."""
        mock_instances.delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_instance(LOCATION, INSTANCE_NAME)


class TestRestartInstance:
    def test_restart_instance(
        self, service, mock_instances, sample_instance_response
    ):
        """Test restarting an instance."""
        mock_request = mock.MagicMock()
        mock_instances.restart.return_value = mock_request
        mock_request.execute.return_value = {
            **sample_instance_response,
            "state": "RESTARTING",
        }

        result = service.restart_instance(LOCATION, INSTANCE_NAME)

        mock_instances.restart.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/{INSTANCE_NAME}"
        )
        assert isinstance(result, DataFusionInstance)

    def test_restart_instance_not_found(self, service, mock_instances):
        """Test restarting an instance that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_instances.restart.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.restart_instance(LOCATION, INSTANCE_NAME)


class TestDataFusionInstanceModel:
    def test_from_api_response(self, sample_instance_response):
        """Test creating a DataFusionInstance from API response."""
        instance = DataFusionInstance.from_api_response(
            sample_instance_response
        )

        assert instance.id == INSTANCE_NAME
        assert instance.location == LOCATION
        assert instance.project == PROJECT_ID
        assert instance.type_field == "ENTERPRISE"
        assert instance.description == "Test Data Fusion instance"
        assert instance.enable_stackdriver_logging is True
        assert instance.enable_stackdriver_monitoring is True
        assert instance.private_instance is False
        assert instance.state == "ACTIVE"
        assert instance.service_endpoint is not None
        assert instance.api_endpoint is not None
        assert instance.type == "datafusion.instance"

    def test_from_api_response_minimal(self):
        """Test creating a DataFusionInstance from minimal API response."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/minimal"
        }
        instance = DataFusionInstance.from_api_response(response)

        assert instance.id == "minimal"
        assert instance.type_field == ""
        assert instance.description is None
        assert instance.state == ""

    def test_get_tag(self, sample_instance_response):
        """Test getting tags from a DataFusionInstance."""
        instance = DataFusionInstance.from_api_response(
            sample_instance_response
        )

        assert instance.get_tag("env") == "test"
        assert instance.get_tag("team") == "data"
        assert instance.get_tag("missing") == ""
        assert instance.get_tag("missing", "default") == "default"
