"""Tests for the API Gateway service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.api_gateway import APIGatewayService
from gcpoto.models.api_gateway import APIGateway, APIConfig
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
def sample_gateway_response():
    """Sample API Gateway response."""
    return {
        "name": "projects/test-project/locations/us-central1/gateways/my-gateway",
        "displayName": "My Gateway",
        "state": "ACTIVE",
        "defaultHostname": "my-gateway-abc123.uc.gateway.dev",
        "apiConfig": "projects/test-project/locations/global/apis/my-api/configs/my-config",
        "labels": {"env": "test", "team": "platform"},
        "project": "test-project",
        "location": "us-central1",
        "createTime": "2024-06-01T10:00:00.000Z",
        "updateTime": "2024-06-01T12:00:00.000Z",
    }


@pytest.fixture
def sample_api_response():
    """Sample API resource response."""
    return {
        "name": "projects/test-project/locations/global/apis/my-api",
        "displayName": "My API",
        "state": "ACTIVE",
        "labels": {"env": "test"},
        "project": "test-project",
        "createTime": "2024-06-01T10:00:00.000Z",
    }


@pytest.fixture
def sample_api_config_response():
    """Sample API Config response."""
    return {
        "name": "projects/test-project/locations/global/apis/my-api/configs/my-config",
        "displayName": "My Config",
        "state": "ACTIVE",
        "serviceConfigId": "my-api-config-abc123",
        "gatewayServiceAccount": "gateway-sa@test-project.iam.gserviceaccount.com",
        "openapiDocuments": [
            {
                "document": {
                    "path": "openapi.yaml",
                    "contents": "c3dhZ2dlcg==",
                }
            }
        ],
        "labels": {"version": "v1"},
        "project": "test-project",
        "location": "global",
        "createTime": "2024-06-01T10:00:00.000Z",
        "updateTime": "2024-06-01T12:00:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create an APIGatewayService instance with mocked API client."""
    return APIGatewayService(project_id="test-project")


# ------------------------------------------------------------------ #
#  Service init
# ------------------------------------------------------------------ #


class TestAPIGatewayServiceInit:
    """Tests for APIGatewayService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the API Gateway service."""
        from googleapiclient.discovery import build

        svc = APIGatewayService(project_id="test-project")

        assert svc.project_id == "test-project"
        assert svc.service_name == "apigateway"
        assert svc.version == "v1"
        build.assert_called_once_with("apigateway", "v1", credentials=None)

    def test_init_with_credentials(self, mock_google_client):
        """Test initializing with credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = APIGatewayService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert svc.project_id == "test-project"
            mock_creds.assert_called_once()


# ------------------------------------------------------------------ #
#  Gateway operations
# ------------------------------------------------------------------ #


class TestListGateways:
    """Tests for listing gateways."""

    def test_list_gateways(self, service, sample_gateway_response):
        """Test listing API Gateways."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.list.return_value = mock_request
        mock_request.execute.return_value = {
            "gateways": [sample_gateway_response]
        }
        mock_gateways.list_next.return_value = None

        gateways = service.list_gateways("us-central1")

        mock_gateways.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(gateways) == 1
        assert isinstance(gateways[0], APIGateway)
        assert gateways[0].id == "my-gateway"
        assert gateways[0].state == "ACTIVE"
        assert gateways[0].default_hostname == "my-gateway-abc123.uc.gateway.dev"

    def test_list_gateways_empty(self, service):
        """Test listing gateways when none exist."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.list.return_value = mock_request
        mock_request.execute.return_value = {"gateways": []}
        mock_gateways.list_next.return_value = None

        gateways = service.list_gateways("us-central1")
        assert len(gateways) == 0

    def test_list_gateways_pagination(self, service, sample_gateway_response):
        """Test listing gateways with pagination."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_gateways.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "gateways": [sample_gateway_response]
        }

        second_gw = dict(sample_gateway_response)
        second_gw["name"] = "projects/test-project/locations/us-central1/gateways/gw-2"
        second_gw["displayName"] = "Gateway 2"
        mock_request_page2.execute.return_value = {
            "gateways": [second_gw]
        }

        mock_gateways.list_next.side_effect = [mock_request_page2, None]

        gateways = service.list_gateways("us-central1")
        assert len(gateways) == 2


class TestGetGateway:
    """Tests for getting a gateway."""

    def test_get_gateway(self, service, sample_gateway_response):
        """Test getting a specific gateway."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.get.return_value = mock_request
        mock_request.execute.return_value = sample_gateway_response

        gateway = service.get_gateway("us-central1", "my-gateway")

        mock_gateways.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/gateways/my-gateway"
        )
        assert isinstance(gateway, APIGateway)
        assert gateway.id == "my-gateway"
        assert gateway.display_name == "My Gateway"

    def test_get_gateway_not_found(self, service):
        """Test getting a gateway that does not exist."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_gateway("us-central1", "nonexistent")

    def test_get_gateway_api_error(self, service):
        """Test getting a gateway with an API error."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_gateway("us-central1", "my-gateway")


class TestCreateGateway:
    """Tests for creating a gateway."""

    def test_create_gateway(self, service, sample_gateway_response):
        """Test creating an API Gateway."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.create.return_value = mock_request
        mock_request.execute.return_value = sample_gateway_response

        gateway = service.create_gateway(
            location="us-central1",
            gateway_id="my-gateway",
            api_config="projects/test-project/locations/global/apis/my-api/configs/my-config",
            display_name="My Gateway",
            labels={"env": "test"},
        )

        mock_gateways.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1",
            gatewayId="my-gateway",
            body={
                "apiConfig": "projects/test-project/locations/global/apis/my-api/configs/my-config",
                "displayName": "My Gateway",
                "labels": {"env": "test"},
            },
        )
        assert isinstance(gateway, APIGateway)
        assert gateway.id == "my-gateway"

    def test_create_gateway_minimal(self, service, sample_gateway_response):
        """Test creating a gateway with minimal parameters."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.create.return_value = mock_request
        mock_request.execute.return_value = sample_gateway_response

        service.create_gateway(
            location="us-central1",
            gateway_id="my-gateway",
            api_config="projects/test-project/locations/global/apis/my-api/configs/my-config",
        )

        mock_gateways.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1",
            gatewayId="my-gateway",
            body={
                "apiConfig": "projects/test-project/locations/global/apis/my-api/configs/my-config",
            },
        )

    def test_create_gateway_already_exists(self, service):
        """Test creating a gateway that already exists."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_gateway(
                location="us-central1",
                gateway_id="my-gateway",
                api_config="some-config",
            )

    def test_create_gateway_api_error(self, service):
        """Test creating a gateway with an API error."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_gateway(
                location="us-central1",
                gateway_id="my-gateway",
                api_config="some-config",
            )


class TestUpdateGateway:
    """Tests for updating a gateway."""

    def test_update_gateway(self, service, sample_gateway_response):
        """Test updating an API Gateway."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.patch.return_value = mock_request
        updated_response = dict(sample_gateway_response)
        updated_response["displayName"] = "Updated Gateway"
        mock_request.execute.return_value = updated_response

        gateway = service.update_gateway(
            location="us-central1",
            gateway_id="my-gateway",
            update_mask="displayName",
            update_fields={"displayName": "Updated Gateway"},
        )

        mock_gateways.patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/gateways/my-gateway",
            updateMask="displayName",
            body={"displayName": "Updated Gateway"},
        )
        assert isinstance(gateway, APIGateway)

    def test_update_gateway_not_found(self, service):
        """Test updating a gateway that does not exist."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_gateway(
                location="us-central1",
                gateway_id="nonexistent",
                update_mask="displayName",
                update_fields={"displayName": "Test"},
            )


class TestDeleteGateway:
    """Tests for deleting a gateway."""

    def test_delete_gateway(self, service):
        """Test deleting an API Gateway."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_gateway("us-central1", "my-gateway")

        mock_gateways.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/gateways/my-gateway"
        )
        assert result is True

    def test_delete_gateway_not_found(self, service):
        """Test deleting a gateway that does not exist."""
        mock_gateways = (
            service.service.projects.return_value
            .locations.return_value
            .gateways.return_value
        )
        mock_request = mock.MagicMock()
        mock_gateways.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_gateway("us-central1", "nonexistent")


# ------------------------------------------------------------------ #
#  API operations
# ------------------------------------------------------------------ #


class TestListApis:
    """Tests for listing APIs."""

    def test_list_apis(self, service, sample_api_response):
        """Test listing APIs."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.list.return_value = mock_request
        mock_request.execute.return_value = {
            "apis": [sample_api_response]
        }
        mock_apis.list_next.return_value = None

        apis = service.list_apis()

        mock_apis.list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(apis) == 1
        assert isinstance(apis[0], APIGateway)

    def test_list_apis_with_location(self, service, sample_api_response):
        """Test listing APIs with a specific location."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.list.return_value = mock_request
        mock_request.execute.return_value = {"apis": []}
        mock_apis.list_next.return_value = None

        service.list_apis(location="us-east1")

        mock_apis.list.assert_called_once_with(
            parent="projects/test-project/locations/us-east1"
        )

    def test_list_apis_empty(self, service):
        """Test listing APIs when none exist."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.list.return_value = mock_request
        mock_request.execute.return_value = {"apis": []}
        mock_apis.list_next.return_value = None

        apis = service.list_apis()
        assert len(apis) == 0


class TestGetApi:
    """Tests for getting an API."""

    def test_get_api(self, service, sample_api_response):
        """Test getting a specific API."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.get.return_value = mock_request
        mock_request.execute.return_value = sample_api_response

        api = service.get_api("my-api")

        mock_apis.get.assert_called_once_with(
            name="projects/test-project/locations/global/apis/my-api"
        )
        assert isinstance(api, APIGateway)
        assert api.id == "my-api"

    def test_get_api_not_found(self, service):
        """Test getting an API that does not exist."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_api("nonexistent")


class TestCreateApi:
    """Tests for creating an API."""

    def test_create_api(self, service, sample_api_response):
        """Test creating an API."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.create.return_value = mock_request
        mock_request.execute.return_value = sample_api_response

        api = service.create_api(
            api_id="my-api",
            display_name="My API",
            labels={"env": "test"},
        )

        mock_apis.create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            apiId="my-api",
            body={
                "displayName": "My API",
                "labels": {"env": "test"},
            },
        )
        assert isinstance(api, APIGateway)

    def test_create_api_minimal(self, service, sample_api_response):
        """Test creating an API with minimal parameters."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.create.return_value = mock_request
        mock_request.execute.return_value = sample_api_response

        service.create_api(api_id="my-api")

        mock_apis.create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            apiId="my-api",
            body={},
        )

    def test_create_api_already_exists(self, service):
        """Test creating an API that already exists."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_api(api_id="my-api")


class TestDeleteApi:
    """Tests for deleting an API."""

    def test_delete_api(self, service):
        """Test deleting an API."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_api("my-api")

        mock_apis.delete.assert_called_once_with(
            name="projects/test-project/locations/global/apis/my-api"
        )
        assert result is True

    def test_delete_api_not_found(self, service):
        """Test deleting an API that does not exist."""
        mock_apis = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
        )
        mock_request = mock.MagicMock()
        mock_apis.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_api("nonexistent")


# ------------------------------------------------------------------ #
#  API Config operations
# ------------------------------------------------------------------ #


class TestListApiConfigs:
    """Tests for listing API configs."""

    def test_list_api_configs(self, service, sample_api_config_response):
        """Test listing API configs."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.list.return_value = mock_request
        mock_request.execute.return_value = {
            "apiConfigs": [sample_api_config_response]
        }
        mock_configs.list_next.return_value = None

        configs = service.list_api_configs("my-api")

        mock_configs.list.assert_called_once_with(
            parent="projects/test-project/locations/global/apis/my-api"
        )
        assert len(configs) == 1
        assert isinstance(configs[0], APIConfig)
        assert configs[0].id == "my-config"
        assert configs[0].state == "ACTIVE"

    def test_list_api_configs_empty(self, service):
        """Test listing API configs when none exist."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.list.return_value = mock_request
        mock_request.execute.return_value = {"apiConfigs": []}
        mock_configs.list_next.return_value = None

        configs = service.list_api_configs("my-api")
        assert len(configs) == 0


class TestGetApiConfig:
    """Tests for getting an API config."""

    def test_get_api_config(self, service, sample_api_config_response):
        """Test getting a specific API config."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.get.return_value = mock_request
        mock_request.execute.return_value = sample_api_config_response

        config = service.get_api_config("my-api", "my-config")

        mock_configs.get.assert_called_once_with(
            name="projects/test-project/locations/global/apis/my-api/configs/my-config"
        )
        assert isinstance(config, APIConfig)
        assert config.id == "my-config"
        assert config.display_name == "My Config"
        assert config.service_config_id == "my-api-config-abc123"

    def test_get_api_config_not_found(self, service):
        """Test getting an API config that does not exist."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_api_config("my-api", "nonexistent")

    def test_get_api_config_api_error(self, service):
        """Test getting an API config with an API error."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_api_config("my-api", "my-config")


class TestCreateApiConfig:
    """Tests for creating an API config."""

    def test_create_api_config(self, service, sample_api_config_response):
        """Test creating an API config."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.create.return_value = mock_request
        mock_request.execute.return_value = sample_api_config_response

        openapi_docs = [
            {
                "document": {
                    "path": "openapi.yaml",
                    "contents": "c3dhZ2dlcg==",
                }
            }
        ]

        config = service.create_api_config(
            api_id="my-api",
            config_id="my-config",
            openapi_documents=openapi_docs,
            display_name="My Config",
        )

        mock_configs.create.assert_called_once_with(
            parent="projects/test-project/locations/global/apis/my-api",
            apiConfigId="my-config",
            body={
                "openapiDocuments": openapi_docs,
                "displayName": "My Config",
            },
        )
        assert isinstance(config, APIConfig)
        assert config.id == "my-config"

    def test_create_api_config_with_grpc(self, service, sample_api_config_response):
        """Test creating an API config with gRPC services."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.create.return_value = mock_request
        mock_request.execute.return_value = sample_api_config_response

        grpc_services = [
            {
                "fileDescriptorSet": {
                    "path": "descriptor.pb",
                    "contents": "base64data",
                }
            }
        ]

        service.create_api_config(
            api_id="my-api",
            config_id="my-config",
            grpc_services=grpc_services,
        )

        mock_configs.create.assert_called_once_with(
            parent="projects/test-project/locations/global/apis/my-api",
            apiConfigId="my-config",
            body={"grpcServices": grpc_services},
        )

    def test_create_api_config_minimal(self, service, sample_api_config_response):
        """Test creating an API config with minimal parameters."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.create.return_value = mock_request
        mock_request.execute.return_value = sample_api_config_response

        service.create_api_config(api_id="my-api", config_id="my-config")

        mock_configs.create.assert_called_once_with(
            parent="projects/test-project/locations/global/apis/my-api",
            apiConfigId="my-config",
            body={},
        )

    def test_create_api_config_already_exists(self, service):
        """Test creating an API config that already exists."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_api_config(api_id="my-api", config_id="my-config")


class TestDeleteApiConfig:
    """Tests for deleting an API config."""

    def test_delete_api_config(self, service):
        """Test deleting an API config."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_api_config("my-api", "my-config")

        mock_configs.delete.assert_called_once_with(
            name="projects/test-project/locations/global/apis/my-api/configs/my-config"
        )
        assert result is True

    def test_delete_api_config_not_found(self, service):
        """Test deleting an API config that does not exist."""
        mock_configs = (
            service.service.projects.return_value
            .locations.return_value
            .apis.return_value
            .configs.return_value
        )
        mock_request = mock.MagicMock()
        mock_configs.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_api_config("my-api", "nonexistent")


# ------------------------------------------------------------------ #
#  Model tests
# ------------------------------------------------------------------ #


class TestAPIGatewayModel:
    """Tests for the APIGateway model."""

    def test_from_api_response(self, sample_gateway_response):
        """Test creating an APIGateway from an API response."""
        gateway = APIGateway.from_api_response(sample_gateway_response)

        assert gateway.id == "my-gateway"
        assert gateway.name == "projects/test-project/locations/us-central1/gateways/my-gateway"
        assert gateway.type == "apigateway.gateway"
        assert gateway.display_name == "My Gateway"
        assert gateway.state == "ACTIVE"
        assert gateway.default_hostname == "my-gateway-abc123.uc.gateway.dev"
        assert gateway.location == "us-central1"
        assert gateway.labels == {"env": "test", "team": "platform"}

    def test_from_api_response_minimal(self):
        """Test creating an APIGateway from a minimal response."""
        gateway = APIGateway.from_api_response({"name": "simple-gw"})

        assert gateway.id == "simple-gw"
        assert gateway.name == "simple-gw"
        assert gateway.state == ""
        assert gateway.display_name is None
        assert gateway.default_hostname is None

    def test_get_tag(self, sample_gateway_response):
        """Test the get_tag method."""
        gateway = APIGateway.from_api_response(sample_gateway_response)

        assert gateway.get_tag("env") == "test"
        assert gateway.get_tag("team") == "platform"
        assert gateway.get_tag("missing") == ""
        assert gateway.get_tag("missing", "default") == "default"


class TestAPIConfigModel:
    """Tests for the APIConfig model."""

    def test_from_api_response(self, sample_api_config_response):
        """Test creating an APIConfig from an API response."""
        config = APIConfig.from_api_response(sample_api_config_response)

        assert config.id == "my-config"
        assert config.name == "projects/test-project/locations/global/apis/my-api/configs/my-config"
        assert config.type == "apigateway.apiConfig"
        assert config.display_name == "My Config"
        assert config.state == "ACTIVE"
        assert config.service_config_id == "my-api-config-abc123"
        assert config.openapi_documents is not None
        assert len(config.openapi_documents) == 1
        assert config.labels == {"version": "v1"}

    def test_from_api_response_minimal(self):
        """Test creating an APIConfig from a minimal response."""
        config = APIConfig.from_api_response({"name": "simple-config"})

        assert config.id == "simple-config"
        assert config.state == ""
        assert config.display_name is None
        assert config.service_config_id is None
        assert config.openapi_documents is None
        assert config.grpc_services is None

    def test_get_tag(self, sample_api_config_response):
        """Test the get_tag method."""
        config = APIConfig.from_api_response(sample_api_config_response)

        assert config.get_tag("version") == "v1"
        assert config.get_tag("missing") == ""
        assert config.get_tag("missing", "default") == "default"
