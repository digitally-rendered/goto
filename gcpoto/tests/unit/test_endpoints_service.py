"""Tests for the Cloud Endpoints service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.endpoints import EndpointsService
from gcpoto.models.endpoints import ManagedService, ServiceConfig
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
)


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_managed_service_response():
    """Sample managed service response."""
    return {
        "serviceName": "my-service.endpoints.test-project.cloud.goog",
        "producerProjectId": "test-project",
    }


@pytest.fixture
def sample_service_config_response():
    """Sample service config response."""
    return {
        "id": "2024-06-01r0",
        "name": "my-service.endpoints.test-project.cloud.goog",
        "serviceName": "my-service.endpoints.test-project.cloud.goog",
        "producerProjectId": "test-project",
        "title": "My Service API",
        "documentation": {"summary": "My service documentation"},
        "apis": [{"name": "my-service-api", "version": "v1"}],
        "quota": {"limits": []},
        "createTime": "2024-06-01T10:00:00.000Z",
        "updateTime": "2024-06-01T12:00:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create an EndpointsService instance with mocked API client."""
    return EndpointsService(project_id="test-project")


# ------------------------------------------------------------------ #
#  Service init
# ------------------------------------------------------------------ #


class TestEndpointsServiceInit:
    """Tests for EndpointsService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the Endpoints service."""
        from googleapiclient.discovery import build

        svc = EndpointsService(project_id="test-project")

        assert svc.project_id == "test-project"
        assert svc.service_name == "servicemanagement"
        assert svc.version == "v1"
        build.assert_called_once_with(
            "servicemanagement", "v1", credentials=None
        )

    def test_init_with_credentials(self, mock_google_client):
        """Test initializing with credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = EndpointsService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert svc.project_id == "test-project"
            mock_creds.assert_called_once()


# ------------------------------------------------------------------ #
#  Managed Service operations
# ------------------------------------------------------------------ #


class TestListServices:
    """Tests for listing managed services."""

    def test_list_services(self, service, sample_managed_service_response):
        """Test listing managed services."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.list.return_value = mock_request
        mock_request.execute.return_value = {
            "services": [sample_managed_service_response]
        }
        mock_services.list_next.return_value = None

        results = service.list_services()

        mock_services.list.assert_called_once_with(
            producerProjectId="test-project"
        )
        assert len(results) == 1
        assert isinstance(results[0], ManagedService)
        assert results[0].service_name_field == (
            "my-service.endpoints.test-project.cloud.goog"
        )

    def test_list_services_empty(self, service):
        """Test listing services when none exist."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.list.return_value = mock_request
        mock_request.execute.return_value = {"services": []}
        mock_services.list_next.return_value = None

        results = service.list_services()
        assert len(results) == 0

    def test_list_services_pagination(
        self, service, sample_managed_service_response
    ):
        """Test listing services with pagination."""
        mock_services = service.service.services.return_value
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_services.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "services": [sample_managed_service_response]
        }

        second_svc = dict(sample_managed_service_response)
        second_svc["serviceName"] = "other-service.endpoints.test-project.cloud.goog"
        mock_request_page2.execute.return_value = {
            "services": [second_svc]
        }

        mock_services.list_next.side_effect = [mock_request_page2, None]

        results = service.list_services()
        assert len(results) == 2


class TestGetService:
    """Tests for getting a managed service."""

    def test_get_service(self, service, sample_managed_service_response):
        """Test getting a specific managed service."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.get.return_value = mock_request
        mock_request.execute.return_value = sample_managed_service_response

        result = service.get_service(
            "my-service.endpoints.test-project.cloud.goog"
        )

        mock_services.get.assert_called_once_with(
            serviceName="my-service.endpoints.test-project.cloud.goog"
        )
        assert isinstance(result, ManagedService)
        assert result.producer_project_id == "test-project"

    def test_get_service_not_found(self, service):
        """Test getting a service that does not exist."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_service("nonexistent")

    def test_get_service_api_error(self, service):
        """Test getting a service with an API error."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_service("my-service")


class TestCreateService:
    """Tests for creating a managed service."""

    def test_create_service(self, service, sample_managed_service_response):
        """Test creating a managed service."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.create.return_value = mock_request
        mock_request.execute.return_value = sample_managed_service_response

        result = service.create_service(
            "my-service.endpoints.test-project.cloud.goog",
            producer_project_id="test-project",
        )

        mock_services.create.assert_called_once_with(
            body={
                "serviceName": "my-service.endpoints.test-project.cloud.goog",
                "producerProjectId": "test-project",
            }
        )
        assert isinstance(result, ManagedService)

    def test_create_service_default_project(
        self, service, sample_managed_service_response
    ):
        """Test creating a service with default project ID."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.create.return_value = mock_request
        mock_request.execute.return_value = sample_managed_service_response

        service.create_service(
            "my-service.endpoints.test-project.cloud.goog"
        )

        mock_services.create.assert_called_once_with(
            body={
                "serviceName": "my-service.endpoints.test-project.cloud.goog",
                "producerProjectId": "test-project",
            }
        )

    def test_create_service_already_exists(self, service):
        """Test creating a service that already exists."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_service("existing-service")

    def test_create_service_api_error(self, service):
        """Test creating a service with an API error."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_service("my-service")


class TestDeleteService:
    """Tests for deleting a managed service."""

    def test_delete_service(self, service):
        """Test deleting a managed service."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_service(
            "my-service.endpoints.test-project.cloud.goog"
        )

        mock_services.delete.assert_called_once_with(
            serviceName="my-service.endpoints.test-project.cloud.goog"
        )
        assert result is True

    def test_delete_service_not_found(self, service):
        """Test deleting a service that does not exist."""
        mock_services = service.service.services.return_value
        mock_request = mock.MagicMock()
        mock_services.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_service("nonexistent")


# ------------------------------------------------------------------ #
#  Service Config operations
# ------------------------------------------------------------------ #


class TestListServiceConfigs:
    """Tests for listing service configs."""

    def test_list_service_configs(
        self, service, sample_service_config_response
    ):
        """Test listing service configs."""
        mock_configs = (
            service.service.services.return_value.configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.list.return_value = mock_request
        mock_request.execute.return_value = {
            "serviceConfigs": [sample_service_config_response]
        }
        mock_configs.list_next.return_value = None

        configs = service.list_service_configs(
            "my-service.endpoints.test-project.cloud.goog"
        )

        mock_configs.list.assert_called_once_with(
            serviceName="my-service.endpoints.test-project.cloud.goog"
        )
        assert len(configs) == 1
        assert isinstance(configs[0], ServiceConfig)
        assert configs[0].title == "My Service API"

    def test_list_service_configs_empty(self, service):
        """Test listing service configs when none exist."""
        mock_configs = (
            service.service.services.return_value.configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.list.return_value = mock_request
        mock_request.execute.return_value = {"serviceConfigs": []}
        mock_configs.list_next.return_value = None

        configs = service.list_service_configs("my-service")
        assert len(configs) == 0


class TestGetServiceConfig:
    """Tests for getting a service config."""

    def test_get_service_config(
        self, service, sample_service_config_response
    ):
        """Test getting a specific service config."""
        mock_configs = (
            service.service.services.return_value.configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.get.return_value = mock_request
        mock_request.execute.return_value = sample_service_config_response

        config = service.get_service_config(
            "my-service.endpoints.test-project.cloud.goog",
            "2024-06-01r0",
        )

        mock_configs.get.assert_called_once_with(
            serviceName="my-service.endpoints.test-project.cloud.goog",
            configId="2024-06-01r0",
        )
        assert isinstance(config, ServiceConfig)
        assert config.id == "2024-06-01r0"
        assert config.title == "My Service API"

    def test_get_service_config_not_found(self, service):
        """Test getting a service config that does not exist."""
        mock_configs = (
            service.service.services.return_value.configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_service_config("my-service", "nonexistent")

    def test_get_service_config_api_error(self, service):
        """Test getting a service config with an API error."""
        mock_configs = (
            service.service.services.return_value.configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_service_config("my-service", "config-1")


class TestSubmitConfigSource:
    """Tests for submitting a config source."""

    def test_submit_config_source(self, service):
        """Test submitting a config source."""
        mock_configs = (
            service.service.services.return_value.configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.submit.return_value = mock_request
        mock_request.execute.return_value = {
            "name": "operations/my-operation",
            "done": False,
        }

        config_source = {
            "files": [
                {
                    "filePath": "openapi.yaml",
                    "fileContents": "c3dhZ2dlcg==",
                    "fileType": "OPEN_API_YAML",
                }
            ]
        }

        result = service.submit_config_source(
            "my-service.endpoints.test-project.cloud.goog",
            config_source,
        )

        mock_configs.submit.assert_called_once_with(
            serviceName="my-service.endpoints.test-project.cloud.goog",
            body={"configSource": config_source},
        )
        assert result["name"] == "operations/my-operation"

    def test_submit_config_source_not_found(self, service):
        """Test submitting a config source for a nonexistent service."""
        mock_configs = (
            service.service.services.return_value.configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.submit.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.submit_config_source("nonexistent", {})

    def test_submit_config_source_api_error(self, service):
        """Test submitting a config source with an API error."""
        mock_configs = (
            service.service.services.return_value.configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.submit.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.submit_config_source("my-service", {})


# ------------------------------------------------------------------ #
#  Service Rollout operations
# ------------------------------------------------------------------ #


class TestListServiceRollouts:
    """Tests for listing service rollouts."""

    def test_list_service_rollouts(self, service):
        """Test listing service rollouts."""
        mock_rollouts = (
            service.service.services.return_value.rollouts.return_value
        )
        mock_request = mock.MagicMock()
        mock_rollouts.list.return_value = mock_request
        mock_request.execute.return_value = {
            "rollouts": [
                {
                    "rolloutId": "rollout-1",
                    "status": "SUCCESS",
                    "serviceName": "my-service",
                }
            ]
        }
        mock_rollouts.list_next.return_value = None

        rollouts = service.list_service_rollouts("my-service")

        mock_rollouts.list.assert_called_once_with(
            serviceName="my-service"
        )
        assert len(rollouts) == 1
        assert rollouts[0]["rolloutId"] == "rollout-1"

    def test_list_service_rollouts_empty(self, service):
        """Test listing rollouts when none exist."""
        mock_rollouts = (
            service.service.services.return_value.rollouts.return_value
        )
        mock_request = mock.MagicMock()
        mock_rollouts.list.return_value = mock_request
        mock_request.execute.return_value = {"rollouts": []}
        mock_rollouts.list_next.return_value = None

        rollouts = service.list_service_rollouts("my-service")
        assert len(rollouts) == 0


class TestCreateServiceRollout:
    """Tests for creating a service rollout."""

    def test_create_service_rollout(self, service):
        """Test creating a service rollout."""
        mock_rollouts = (
            service.service.services.return_value.rollouts.return_value
        )
        mock_request = mock.MagicMock()
        mock_rollouts.create.return_value = mock_request
        mock_request.execute.return_value = {
            "name": "operations/rollout-op",
            "done": False,
        }

        rollout_body = {
            "serviceName": "my-service",
            "trafficPercentStrategy": {
                "percentages": {"config-id": 100.0}
            },
        }

        result = service.create_service_rollout("my-service", rollout_body)

        mock_rollouts.create.assert_called_once_with(
            serviceName="my-service", body=rollout_body
        )
        assert result["name"] == "operations/rollout-op"

    def test_create_service_rollout_not_found(self, service):
        """Test creating a rollout for a nonexistent service."""
        mock_rollouts = (
            service.service.services.return_value.rollouts.return_value
        )
        mock_request = mock.MagicMock()
        mock_rollouts.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.create_service_rollout("nonexistent", {})

    def test_create_service_rollout_api_error(self, service):
        """Test creating a rollout with an API error."""
        mock_rollouts = (
            service.service.services.return_value.rollouts.return_value
        )
        mock_request = mock.MagicMock()
        mock_rollouts.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_service_rollout("my-service", {})


# ------------------------------------------------------------------ #
#  Model tests
# ------------------------------------------------------------------ #


class TestManagedServiceModel:
    """Tests for the ManagedService model."""

    def test_from_api_response(self, sample_managed_service_response):
        """Test creating a ManagedService from an API response."""
        svc = ManagedService.from_api_response(
            sample_managed_service_response
        )

        assert svc.id == "my-service.endpoints.test-project.cloud.goog"
        assert svc.service_name_field == (
            "my-service.endpoints.test-project.cloud.goog"
        )
        assert svc.producer_project_id == "test-project"
        assert svc.type == "endpoints.managedService"

    def test_from_api_response_minimal(self):
        """Test creating a ManagedService from a minimal response."""
        svc = ManagedService.from_api_response({})

        assert svc.id == ""
        assert svc.service_name_field == ""
        assert svc.producer_project_id is None


class TestServiceConfigModel:
    """Tests for the ServiceConfig model."""

    def test_from_api_response(self, sample_service_config_response):
        """Test creating a ServiceConfig from an API response."""
        config = ServiceConfig.from_api_response(
            sample_service_config_response
        )

        assert config.id == "2024-06-01r0"
        assert config.title == "My Service API"
        assert config.documentation == {"summary": "My service documentation"}
        assert config.apis is not None
        assert len(config.apis) == 1
        assert config.quota is not None
        assert config.type == "endpoints.serviceConfig"

    def test_from_api_response_minimal(self):
        """Test creating a ServiceConfig from a minimal response."""
        config = ServiceConfig.from_api_response({"name": "simple-config"})

        assert config.name == "simple-config"
        assert config.title is None
        assert config.documentation is None
        assert config.apis is None
        assert config.quota is None
