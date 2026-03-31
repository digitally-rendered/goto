"""Tests for the Media CDN service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.media_cdn import MediaCDNService
from gcpoto.models.media_cdn import EdgeCacheService, EdgeCacheOrigin


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_EDGE_CACHE_SERVICE_RESPONSE = {
    "id": "ecs-abc123",
    "name": "projects/test-project/locations/global/edgeCacheServices/my-service",
    "projectId": "test-project",
    "location": "global",
    "description": "A test edge cache service",
    "routing": {
        "hostRules": [
            {"hosts": ["example.com"], "pathMatcher": "routes"},
        ],
        "pathMatchers": [
            {
                "name": "routes",
                "routeRules": [
                    {
                        "priority": 1,
                        "matchRules": [{"prefixMatch": "/"}],
                        "origin": "projects/test-project/locations/global/edgeCacheOrigins/my-origin",
                    },
                ],
            },
        ],
    },
    "edgeSslCertificates": [
        "projects/test-project/locations/global/certificates/my-cert",
    ],
    "edgeSecurityPolicy": "projects/test-project/locations/global/securityPolicies/my-policy",
    "disableQuic": False,
    "labels": {"env": "test", "team": "cdn"},
    "createTime": "2025-07-01T00:00:00Z",
    "updateTime": "2025-07-02T00:00:00Z",
}

SAMPLE_EDGE_CACHE_ORIGIN_RESPONSE = {
    "id": "eco-abc123",
    "name": "projects/test-project/locations/global/edgeCacheOrigins/my-origin",
    "projectId": "test-project",
    "location": "global",
    "originAddress": "backend.example.com",
    "protocol": "HTTPS",
    "port": 443,
    "retryConditions": ["CONNECT_FAILURE", "HTTP_5XX"],
    "maxAttempts": 3,
    "failoverOrigin": "projects/test-project/locations/global/edgeCacheOrigins/backup-origin",
    "labels": {"tier": "primary"},
    "createTime": "2025-07-01T00:00:00Z",
    "updateTime": "2025-07-02T00:00:00Z",
}


class TestMediaCDNServiceInit:
    """Tests for MediaCDNService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = MediaCDNService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "networkservices"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == EdgeCacheService
        mock_build.assert_called_once_with(
            "networkservices", "v1", credentials=None
        )


class TestEdgeCacheServiceModel:
    """Tests for the EdgeCacheService model."""

    def test_from_api_response(self):
        svc = EdgeCacheService.from_api_response(
            SAMPLE_EDGE_CACHE_SERVICE_RESPONSE
        )

        assert svc.id == "ecs-abc123"
        assert svc.name == "projects/test-project/locations/global/edgeCacheServices/my-service"
        assert svc.type == "networkservices.edgeCacheService"
        assert svc.project == "test-project"
        assert svc.location == "global"
        assert svc.description == "A test edge cache service"
        assert svc.routing is not None
        assert len(svc.routing["hostRules"]) == 1
        assert svc.edge_ssl_certificates is not None
        assert len(svc.edge_ssl_certificates) == 1
        assert svc.edge_security_policy is not None
        assert svc.disable_quic is False
        assert svc.labels == {"env": "test", "team": "cdn"}
        assert svc.created.isoformat().startswith("2025-07-01T00:00:00")

    def test_from_api_response_minimal(self):
        response = {"name": "bare-service", "projectId": "p"}
        svc = EdgeCacheService.from_api_response(response)

        assert svc.name == "bare-service"
        assert svc.id == ""
        assert svc.location == ""
        assert svc.description is None
        assert svc.routing == {}
        assert svc.edge_ssl_certificates is None
        assert svc.edge_security_policy is None
        assert svc.disable_quic is False

    def test_get_tag(self):
        svc = EdgeCacheService.from_api_response(
            SAMPLE_EDGE_CACHE_SERVICE_RESPONSE
        )
        assert svc.get_tag("env") == "test"
        assert svc.get_tag("team") == "cdn"
        assert svc.get_tag("missing") == ""
        assert svc.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {"name": "bare", "projectId": "p"}
        svc = EdgeCacheService.from_api_response(response)
        assert svc.get_tag("env") == ""
        assert svc.get_tag("env", "fallback") == "fallback"


class TestEdgeCacheOriginModel:
    """Tests for the EdgeCacheOrigin model."""

    def test_from_api_response(self):
        origin = EdgeCacheOrigin.from_api_response(
            SAMPLE_EDGE_CACHE_ORIGIN_RESPONSE
        )

        assert origin.id == "eco-abc123"
        assert origin.name == "projects/test-project/locations/global/edgeCacheOrigins/my-origin"
        assert origin.type == "networkservices.edgeCacheOrigin"
        assert origin.project == "test-project"
        assert origin.location == "global"
        assert origin.origin_address == "backend.example.com"
        assert origin.protocol == "HTTPS"
        assert origin.port == 443
        assert origin.retry_conditions == ["CONNECT_FAILURE", "HTTP_5XX"]
        assert origin.max_attempts == 3
        assert origin.failover_origin is not None

    def test_from_api_response_minimal(self):
        response = {"name": "bare-origin", "projectId": "p"}
        origin = EdgeCacheOrigin.from_api_response(response)

        assert origin.name == "bare-origin"
        assert origin.id == ""
        assert origin.location == ""
        assert origin.origin_address == ""
        assert origin.protocol is None
        assert origin.port is None
        assert origin.retry_conditions is None
        assert origin.max_attempts is None
        assert origin.failover_origin is None


def _setup_edge_cache_service_mock(mock_service):
    """Helper to set up the nested mock chain for edge cache service operations."""
    mock_projects = mock.MagicMock()
    mock_service.projects.return_value = mock_projects
    mock_locations = mock.MagicMock()
    mock_projects.locations.return_value = mock_locations
    mock_edge_cache_services = mock.MagicMock()
    mock_locations.edgeCacheServices.return_value = mock_edge_cache_services
    return mock_edge_cache_services


def _setup_edge_cache_origin_mock(mock_service):
    """Helper to set up the nested mock chain for edge cache origin operations."""
    mock_projects = mock.MagicMock()
    mock_service.projects.return_value = mock_projects
    mock_locations = mock.MagicMock()
    mock_projects.locations.return_value = mock_locations
    mock_edge_cache_origins = mock.MagicMock()
    mock_locations.edgeCacheOrigins.return_value = mock_edge_cache_origins
    return mock_edge_cache_origins


class TestMediaCDNServiceEdgeCacheServices:
    """Tests for edge cache service-related methods."""

    def test_list_edge_cache_services(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_ecs = _setup_edge_cache_service_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_ecs.list.return_value = mock_list
        mock_list.execute.return_value = {
            "edgeCacheServices": [SAMPLE_EDGE_CACHE_SERVICE_RESPONSE],
        }

        service = MediaCDNService(project_id="test-project")
        results = service.list_edge_cache_services("global")

        mock_ecs.list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(results) == 1
        assert isinstance(results[0], EdgeCacheService)
        assert results[0].description == "A test edge cache service"

    def test_list_edge_cache_services_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_ecs = _setup_edge_cache_service_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_ecs.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = MediaCDNService(project_id="test-project")
        results = service.list_edge_cache_services("global")

        assert results == []

    def test_get_edge_cache_service(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_ecs = _setup_edge_cache_service_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_ecs.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_EDGE_CACHE_SERVICE_RESPONSE

        service = MediaCDNService(project_id="test-project")
        result = service.get_edge_cache_service("global", "my-service")

        mock_ecs.get.assert_called_once_with(
            name="projects/test-project/locations/global/edgeCacheServices/my-service"
        )
        assert isinstance(result, EdgeCacheService)
        assert result.description == "A test edge cache service"

    def test_create_edge_cache_service(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_ecs = _setup_edge_cache_service_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_ecs.create.return_value = mock_create
        operation_response = {"name": "operation-123", "done": False}
        mock_create.execute.return_value = operation_response

        routing = {
            "hostRules": [
                {"hosts": ["cdn.example.com"], "pathMatcher": "routes"},
            ],
        }

        service = MediaCDNService(project_id="test-project")
        result = service.create_edge_cache_service(
            location="global",
            service_name="new-service",
            routing=routing,
            labels={"env": "prod"},
        )

        mock_ecs.create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            edgeCacheServiceId="new-service",
            body={
                "routing": routing,
                "labels": {"env": "prod"},
            },
        )
        assert result == operation_response

    def test_create_edge_cache_service_no_labels(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_ecs = _setup_edge_cache_service_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_ecs.create.return_value = mock_create
        mock_create.execute.return_value = {"name": "op-1"}

        service = MediaCDNService(project_id="test-project")
        service.create_edge_cache_service(
            location="global",
            service_name="new-service",
            routing={"hostRules": []},
        )

        call_args = mock_ecs.create.call_args
        body = call_args[1]["body"]
        assert "labels" not in body

    def test_update_edge_cache_service(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_ecs = _setup_edge_cache_service_mock(mock_service)
        mock_patch = mock.MagicMock()
        mock_ecs.patch.return_value = mock_patch
        operation_response = {"name": "operation-456", "done": False}
        mock_patch.execute.return_value = operation_response

        service = MediaCDNService(project_id="test-project")
        result = service.update_edge_cache_service(
            location="global",
            service_name="my-service",
            update_mask="description",
            update_fields={"description": "Updated description"},
        )

        mock_ecs.patch.assert_called_once_with(
            name="projects/test-project/locations/global/edgeCacheServices/my-service",
            updateMask="description",
            body={"description": "Updated description"},
        )
        assert result == operation_response

    def test_delete_edge_cache_service(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_ecs = _setup_edge_cache_service_mock(mock_service)
        mock_delete = mock.MagicMock()
        mock_ecs.delete.return_value = mock_delete
        operation_response = {"name": "operation-del", "done": False}
        mock_delete.execute.return_value = operation_response

        service = MediaCDNService(project_id="test-project")
        result = service.delete_edge_cache_service("global", "my-service")

        mock_ecs.delete.assert_called_once_with(
            name="projects/test-project/locations/global/edgeCacheServices/my-service"
        )
        assert result == operation_response


class TestMediaCDNServiceEdgeCacheOrigins:
    """Tests for edge cache origin-related methods."""

    def test_list_edge_cache_origins(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_eco = _setup_edge_cache_origin_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_eco.list.return_value = mock_list
        mock_list.execute.return_value = {
            "edgeCacheOrigins": [SAMPLE_EDGE_CACHE_ORIGIN_RESPONSE],
        }

        service = MediaCDNService(project_id="test-project")
        results = service.list_edge_cache_origins("global")

        mock_eco.list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(results) == 1
        assert isinstance(results[0], EdgeCacheOrigin)
        assert results[0].origin_address == "backend.example.com"

    def test_list_edge_cache_origins_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_eco = _setup_edge_cache_origin_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_eco.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = MediaCDNService(project_id="test-project")
        results = service.list_edge_cache_origins("global")

        assert results == []

    def test_get_edge_cache_origin(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_eco = _setup_edge_cache_origin_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_eco.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_EDGE_CACHE_ORIGIN_RESPONSE

        service = MediaCDNService(project_id="test-project")
        result = service.get_edge_cache_origin("global", "my-origin")

        mock_eco.get.assert_called_once_with(
            name="projects/test-project/locations/global/edgeCacheOrigins/my-origin"
        )
        assert isinstance(result, EdgeCacheOrigin)
        assert result.origin_address == "backend.example.com"
        assert result.protocol == "HTTPS"

    def test_create_edge_cache_origin(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_eco = _setup_edge_cache_origin_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_eco.create.return_value = mock_create
        operation_response = {"name": "operation-eco-1", "done": False}
        mock_create.execute.return_value = operation_response

        service = MediaCDNService(project_id="test-project")
        result = service.create_edge_cache_origin(
            location="global",
            origin_name="new-origin",
            origin_address="backend.example.com",
            protocol="HTTPS",
        )

        mock_eco.create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            edgeCacheOriginId="new-origin",
            body={
                "originAddress": "backend.example.com",
                "protocol": "HTTPS",
            },
        )
        assert result == operation_response

    def test_create_edge_cache_origin_no_protocol(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_eco = _setup_edge_cache_origin_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_eco.create.return_value = mock_create
        mock_create.execute.return_value = {"name": "op-1"}

        service = MediaCDNService(project_id="test-project")
        service.create_edge_cache_origin(
            location="global",
            origin_name="new-origin",
            origin_address="backend.example.com",
        )

        call_args = mock_eco.create.call_args
        body = call_args[1]["body"]
        assert "protocol" not in body
        assert body["originAddress"] == "backend.example.com"

    def test_update_edge_cache_origin(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_eco = _setup_edge_cache_origin_mock(mock_service)
        mock_patch = mock.MagicMock()
        mock_eco.patch.return_value = mock_patch
        operation_response = {"name": "operation-eco-upd", "done": False}
        mock_patch.execute.return_value = operation_response

        service = MediaCDNService(project_id="test-project")
        result = service.update_edge_cache_origin(
            location="global",
            origin_name="my-origin",
            update_mask="protocol",
            update_fields={"protocol": "HTTP2"},
        )

        mock_eco.patch.assert_called_once_with(
            name="projects/test-project/locations/global/edgeCacheOrigins/my-origin",
            updateMask="protocol",
            body={"protocol": "HTTP2"},
        )
        assert result == operation_response

    def test_delete_edge_cache_origin(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_eco = _setup_edge_cache_origin_mock(mock_service)
        mock_delete = mock.MagicMock()
        mock_eco.delete.return_value = mock_delete
        operation_response = {"name": "operation-eco-del", "done": False}
        mock_delete.execute.return_value = operation_response

        service = MediaCDNService(project_id="test-project")
        result = service.delete_edge_cache_origin("global", "my-origin")

        mock_eco.delete.assert_called_once_with(
            name="projects/test-project/locations/global/edgeCacheOrigins/my-origin"
        )
        assert result == operation_response
