"""Tests for Looker service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.looker import LookerService
from gcpoto.models.looker import LookerInstance
from gcpoto.exceptions import ResourceNotFoundError, APIError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
INSTANCE_NAME = "my-looker"


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
    """Create a LookerService with mocked client."""
    return LookerService(project_id=PROJECT_ID)


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
        "platformEdition": "ADVANCED",
        "state": "ACTIVE",
        "lookerUri": "https://my-looker.looker.app",
        "adminSettings": {"allowedEmailDomains": ["example.com"]},
        "maintenanceWindow": {
            "dayOfWeek": "SUNDAY",
            "startTime": {"hours": 2},
        },
        "denyMaintenancePeriod": {
            "startDate": {"year": 2026, "month": 12, "day": 20},
            "endDate": {"year": 2026, "month": 12, "day": 31},
        },
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T11:00:00Z",
        "labels": {"env": "test", "team": "analytics"},
    }


class TestLookerServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the LookerService."""
        from googleapiclient.discovery import build

        svc = LookerService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("looker", "v1", credentials=None)


class TestListInstances:
    def test_list_instances(
        self, service, mock_instances, sample_instance_response
    ):
        """Test listing Looker instances."""
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
        assert isinstance(results[0], LookerInstance)
        assert results[0].platform_edition == "ADVANCED"

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

        assert isinstance(result, LookerInstance)
        assert result.platform_edition == "ADVANCED"
        assert result.state == "ACTIVE"
        assert result.looker_uri == "https://my-looker.looker.app"

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
            LOCATION, INSTANCE_NAME, "ADVANCED"
        )

        assert isinstance(result, LookerInstance)
        assert result.platform_edition == "ADVANCED"

    def test_create_instance_api_error(self, service, mock_instances):
        """Test creating an instance when API returns an error."""
        mock_request = mock.MagicMock()
        mock_instances.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_instance(
                LOCATION, INSTANCE_NAME, "STANDARD"
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
            "platformEdition",
            {"platformEdition": "ELITE"},
        )

        mock_instances.patch.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/{INSTANCE_NAME}",
            updateMask="platformEdition",
            body={"platformEdition": "ELITE"},
        )
        assert isinstance(result, LookerInstance)

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
                "platformEdition",
                {"platformEdition": "ELITE"},
            )


class TestDeleteInstance:
    def test_delete_instance(self, service, mock_instances):
        """Test deleting an instance."""
        mock_instances.delete.return_value.execute.return_value = {}

        result = service.delete_instance(LOCATION, INSTANCE_NAME)
        assert result is True

    def test_delete_instance_not_found(self, service, mock_instances):
        """Test deleting an instance that doesn't exist."""
        mock_instances.delete.return_value.execute.side_effect = (
            HttpError(
                resp=mock.MagicMock(status=404), content=b"Not found"
            )
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
            "state": "ACTIVE",
        }

        result = service.restart_instance(LOCATION, INSTANCE_NAME)

        mock_instances.restart.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/{INSTANCE_NAME}"
        )
        assert isinstance(result, LookerInstance)

    def test_restart_instance_not_found(
        self, service, mock_instances
    ):
        """Test restarting an instance that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_instances.restart.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.restart_instance(LOCATION, INSTANCE_NAME)


class TestExportInstance:
    def test_export_instance(self, service, mock_instances):
        """Test exporting an instance."""
        mock_request = mock.MagicMock()
        mock_instances.export.return_value = mock_request
        mock_request.execute.return_value = {
            "name": "operations/export-op-123",
            "done": False,
        }

        result = service.export_instance(
            LOCATION, INSTANCE_NAME, "gs://my-bucket/export"
        )

        mock_instances.export.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/{INSTANCE_NAME}",
            body={"gcsUri": "gs://my-bucket/export"},
        )
        assert "name" in result

    def test_export_instance_not_found(
        self, service, mock_instances
    ):
        """Test exporting an instance that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_instances.export.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.export_instance(
                LOCATION, INSTANCE_NAME, "gs://my-bucket/export"
            )


class TestImportInstance:
    def test_import_instance(self, service, mock_instances):
        """Test importing an instance."""
        mock_request = mock.MagicMock()
        mock_instances.import_.return_value = mock_request
        mock_request.execute.return_value = {
            "name": "operations/import-op-123",
            "done": False,
        }

        result = service.import_instance(
            LOCATION, INSTANCE_NAME, "gs://my-bucket/export"
        )

        mock_instances.import_.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/{INSTANCE_NAME}",
            body={"gcsUri": "gs://my-bucket/export"},
        )
        assert "name" in result

    def test_import_instance_not_found(
        self, service, mock_instances
    ):
        """Test importing into an instance that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_instances.import_.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.import_instance(
                LOCATION, INSTANCE_NAME, "gs://my-bucket/export"
            )


class TestLookerInstanceModel:
    def test_from_api_response(self, sample_instance_response):
        """Test creating a LookerInstance from API response."""
        instance = LookerInstance.from_api_response(
            sample_instance_response
        )

        assert instance.id == INSTANCE_NAME
        assert instance.location == LOCATION
        assert instance.project == PROJECT_ID
        assert instance.platform_edition == "ADVANCED"
        assert instance.state == "ACTIVE"
        assert instance.looker_uri == "https://my-looker.looker.app"
        assert instance.admin_settings is not None
        assert instance.maintenance_window is not None
        assert instance.deny_maintenance_period is not None
        assert instance.type == "looker.instance"

    def test_from_api_response_minimal(self):
        """Test creating a LookerInstance from minimal API response."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/minimal"
        }
        instance = LookerInstance.from_api_response(response)

        assert instance.id == "minimal"
        assert instance.platform_edition == ""
        assert instance.state == ""
        assert instance.looker_uri is None
        assert instance.admin_settings is None

    def test_get_tag(self, sample_instance_response):
        """Test getting tags from a LookerInstance."""
        instance = LookerInstance.from_api_response(
            sample_instance_response
        )

        assert instance.get_tag("env") == "test"
        assert instance.get_tag("team") == "analytics"
        assert instance.get_tag("missing") == ""
        assert instance.get_tag("missing", "default") == "default"
