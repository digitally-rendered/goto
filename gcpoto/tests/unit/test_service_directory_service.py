"""Tests for the Service Directory service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.service_directory import ServiceDirectoryService
from gcpoto.models.service_directory import Namespace, ServiceEntry, Endpoint


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_NAMESPACE_RESPONSE = {
    "name": "projects/test-project/locations/us-central1/namespaces/my-namespace",
    "labels": {"env": "test", "team": "platform"},
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_NAMESPACE_RESPONSE_MINIMAL = {
    "name": "projects/test-project/locations/us-central1/namespaces/bare-namespace",
}

SAMPLE_SERVICE_RESPONSE = {
    "name": "projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service",
    "metadata": {"version": "v1", "protocol": "grpc"},
    "endpoints": [
        {"name": "endpoint-1", "address": "10.0.0.1", "port": 8080},
    ],
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_SERVICE_RESPONSE_MINIMAL = {
    "name": "projects/test-project/locations/us-central1/namespaces/my-namespace/services/bare-service",
}

SAMPLE_ENDPOINT_RESPONSE = {
    "name": "projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service/endpoints/my-endpoint",
    "address": "10.0.0.1",
    "port": 8080,
    "metadata": {"zone": "us-central1-a"},
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_ENDPOINT_RESPONSE_MINIMAL = {
    "name": "projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service/endpoints/bare-endpoint",
}


class TestServiceDirectoryServiceInit:
    """Tests for ServiceDirectoryService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = ServiceDirectoryService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "servicedirectory"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == Namespace
        mock_build.assert_called_once_with(
            "servicedirectory", "v1", credentials=None
        )


class TestNamespaceModel:
    """Tests for the Namespace model."""

    def test_from_api_response(self):
        ns = Namespace.from_api_response(SAMPLE_NAMESPACE_RESPONSE)

        assert ns.id == "my-namespace"
        assert ns.name == "my-namespace"
        assert ns.type == "servicedirectory.namespace"
        assert ns.project == "test-project"
        assert ns.location == "us-central1"
        assert ns.labels == {"env": "test", "team": "platform"}
        assert ns.created.isoformat().startswith("2025-01-01T00:00:00")
        assert ns.updated.isoformat().startswith("2025-01-02T00:00:00")

    def test_from_api_response_minimal(self):
        ns = Namespace.from_api_response(SAMPLE_NAMESPACE_RESPONSE_MINIMAL)

        assert ns.name == "bare-namespace"
        assert ns.location == "us-central1"
        assert ns.labels is None
        assert ns.created is None
        assert ns.updated is None

    def test_get_tag(self):
        ns = Namespace.from_api_response(SAMPLE_NAMESPACE_RESPONSE)
        assert ns.get_tag("env") == "test"
        assert ns.get_tag("team") == "platform"
        assert ns.get_tag("missing") == ""
        assert ns.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        ns = Namespace.from_api_response(SAMPLE_NAMESPACE_RESPONSE_MINIMAL)
        assert ns.get_tag("env") == ""
        assert ns.get_tag("env", "fallback") == "fallback"


class TestServiceEntryModel:
    """Tests for the ServiceEntry model."""

    def test_from_api_response(self):
        svc = ServiceEntry.from_api_response(SAMPLE_SERVICE_RESPONSE)

        assert svc.id == "my-service"
        assert svc.name == "my-service"
        assert svc.type == "servicedirectory.service"
        assert svc.project == "test-project"
        assert svc.namespace_name == "my-namespace"
        assert svc.location == "us-central1"
        assert svc.metadata == {"version": "v1", "protocol": "grpc"}
        assert svc.endpoints is not None
        assert len(svc.endpoints) == 1
        assert svc.created.isoformat().startswith("2025-01-01T00:00:00")

    def test_from_api_response_minimal(self):
        svc = ServiceEntry.from_api_response(
            SAMPLE_SERVICE_RESPONSE_MINIMAL
        )

        assert svc.name == "bare-service"
        assert svc.namespace_name == "my-namespace"
        assert svc.location == "us-central1"
        assert svc.metadata is None
        assert svc.endpoints is None
        assert svc.created is None


class TestEndpointModel:
    """Tests for the Endpoint model."""

    def test_from_api_response(self):
        ep = Endpoint.from_api_response(SAMPLE_ENDPOINT_RESPONSE)

        assert ep.id == "my-endpoint"
        assert ep.name == "my-endpoint"
        assert ep.type == "servicedirectory.endpoint"
        assert ep.project == "test-project"
        assert ep.service_name_ref == "my-service"
        assert ep.namespace_name == "my-namespace"
        assert ep.location == "us-central1"
        assert ep.address == "10.0.0.1"
        assert ep.port == 8080
        assert ep.metadata == {"zone": "us-central1-a"}
        assert ep.created.isoformat().startswith("2025-01-01T00:00:00")

    def test_from_api_response_minimal(self):
        ep = Endpoint.from_api_response(SAMPLE_ENDPOINT_RESPONSE_MINIMAL)

        assert ep.name == "bare-endpoint"
        assert ep.service_name_ref == "my-service"
        assert ep.namespace_name == "my-namespace"
        assert ep.location == "us-central1"
        assert ep.address is None
        assert ep.port is None
        assert ep.metadata is None
        assert ep.created is None


class TestServiceDirectoryNamespaces:
    """Tests for namespace-related methods."""

    def test_list_namespaces(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_list = mock.MagicMock()
        mock_namespaces.list.return_value = mock_list
        mock_list.execute.return_value = {
            "namespaces": [SAMPLE_NAMESPACE_RESPONSE],
        }
        mock_namespaces.list_next.return_value = None

        service = ServiceDirectoryService(project_id="test-project")
        results = service.list_namespaces("us-central1")

        mock_namespaces.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(results) == 1
        assert isinstance(results[0], Namespace)
        assert results[0].name == "my-namespace"

    def test_list_namespaces_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_list = mock.MagicMock()
        mock_namespaces.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_namespaces.list_next.return_value = None

        service = ServiceDirectoryService(project_id="test-project")
        results = service.list_namespaces("us-central1")

        assert results == []

    def test_list_namespaces_pagination(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_list = mock.MagicMock()
        mock_namespaces.list.return_value = mock_list

        page1_response = {
            "namespaces": [SAMPLE_NAMESPACE_RESPONSE],
        }
        second_namespace = {
            "name": "projects/test-project/locations/us-central1/namespaces/second-namespace",
        }
        page2_response = {
            "namespaces": [second_namespace],
        }

        mock_list.execute.return_value = page1_response

        mock_list_page2 = mock.MagicMock()
        mock_list_page2.execute.return_value = page2_response
        mock_namespaces.list_next.side_effect = [mock_list_page2, None]

        service = ServiceDirectoryService(project_id="test-project")
        results = service.list_namespaces("us-central1")

        assert len(results) == 2
        assert results[0].name == "my-namespace"
        assert results[1].name == "second-namespace"

    def test_get_namespace(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_get = mock.MagicMock()
        mock_namespaces.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_NAMESPACE_RESPONSE

        service = ServiceDirectoryService(project_id="test-project")
        result = service.get_namespace("us-central1", "my-namespace")

        mock_namespaces.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/namespaces/my-namespace"
        )
        assert isinstance(result, Namespace)
        assert result.name == "my-namespace"

    def test_create_namespace(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_create = mock.MagicMock()
        mock_namespaces.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_NAMESPACE_RESPONSE

        service = ServiceDirectoryService(project_id="test-project")
        result = service.create_namespace(
            location="us-central1",
            namespace_id="my-namespace",
            labels={"env": "test"},
        )

        mock_namespaces.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1",
            namespaceId="my-namespace",
            body={"labels": {"env": "test"}},
        )
        assert isinstance(result, Namespace)
        assert result.name == "my-namespace"

    def test_create_namespace_no_labels(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_create = mock.MagicMock()
        mock_namespaces.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_NAMESPACE_RESPONSE

        service = ServiceDirectoryService(project_id="test-project")
        service.create_namespace(
            location="us-central1",
            namespace_id="my-namespace",
        )

        call_args = mock_namespaces.create.call_args
        body = call_args[1]["body"]
        assert "labels" not in body

    def test_delete_namespace(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_delete = mock.MagicMock()
        mock_namespaces.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = ServiceDirectoryService(project_id="test-project")
        result = service.delete_namespace("us-central1", "my-namespace")

        mock_namespaces.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/namespaces/my-namespace"
        )
        mock_delete.execute.assert_called_once()
        assert result is True


class TestServiceDirectoryServices:
    """Tests for service-related methods."""

    def test_list_services(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_list = mock.MagicMock()
        mock_services.list.return_value = mock_list
        mock_list.execute.return_value = {
            "services": [SAMPLE_SERVICE_RESPONSE],
        }
        mock_services.list_next.return_value = None

        service = ServiceDirectoryService(project_id="test-project")
        results = service.list_services("us-central1", "my-namespace")

        mock_services.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/namespaces/my-namespace"
        )
        assert len(results) == 1
        assert isinstance(results[0], ServiceEntry)
        assert results[0].name == "my-service"

    def test_list_services_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_list = mock.MagicMock()
        mock_services.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_services.list_next.return_value = None

        service = ServiceDirectoryService(project_id="test-project")
        results = service.list_services("us-central1", "my-namespace")

        assert results == []

    def test_get_service(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_get = mock.MagicMock()
        mock_services.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_SERVICE_RESPONSE

        service = ServiceDirectoryService(project_id="test-project")
        result = service.get_service(
            "us-central1", "my-namespace", "my-service"
        )

        mock_services.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service"
        )
        assert isinstance(result, ServiceEntry)
        assert result.name == "my-service"
        assert result.namespace_name == "my-namespace"

    def test_create_service(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_create = mock.MagicMock()
        mock_services.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_SERVICE_RESPONSE

        service = ServiceDirectoryService(project_id="test-project")
        result = service.create_service(
            location="us-central1",
            namespace_id="my-namespace",
            service_id="my-service",
            metadata={"version": "v1"},
        )

        mock_services.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/namespaces/my-namespace",
            serviceId="my-service",
            body={"metadata": {"version": "v1"}},
        )
        assert isinstance(result, ServiceEntry)
        assert result.name == "my-service"

    def test_create_service_no_metadata(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_create = mock.MagicMock()
        mock_services.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_SERVICE_RESPONSE

        service = ServiceDirectoryService(project_id="test-project")
        service.create_service(
            location="us-central1",
            namespace_id="my-namespace",
            service_id="my-service",
        )

        call_args = mock_services.create.call_args
        body = call_args[1]["body"]
        assert "metadata" not in body

    def test_delete_service(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_delete = mock.MagicMock()
        mock_services.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = ServiceDirectoryService(project_id="test-project")
        result = service.delete_service(
            "us-central1", "my-namespace", "my-service"
        )

        mock_services.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service"
        )
        mock_delete.execute.assert_called_once()
        assert result is True


class TestServiceDirectoryEndpoints:
    """Tests for endpoint-related methods."""

    def test_list_endpoints(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_endpoints = mock.MagicMock()
        mock_services.endpoints.return_value = mock_endpoints
        mock_list = mock.MagicMock()
        mock_endpoints.list.return_value = mock_list
        mock_list.execute.return_value = {
            "endpoints": [SAMPLE_ENDPOINT_RESPONSE],
        }
        mock_endpoints.list_next.return_value = None

        service = ServiceDirectoryService(project_id="test-project")
        results = service.list_endpoints(
            "us-central1", "my-namespace", "my-service"
        )

        mock_endpoints.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service"
        )
        assert len(results) == 1
        assert isinstance(results[0], Endpoint)
        assert results[0].name == "my-endpoint"

    def test_list_endpoints_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_endpoints = mock.MagicMock()
        mock_services.endpoints.return_value = mock_endpoints
        mock_list = mock.MagicMock()
        mock_endpoints.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_endpoints.list_next.return_value = None

        service = ServiceDirectoryService(project_id="test-project")
        results = service.list_endpoints(
            "us-central1", "my-namespace", "my-service"
        )

        assert results == []

    def test_get_endpoint(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_endpoints = mock.MagicMock()
        mock_services.endpoints.return_value = mock_endpoints
        mock_get = mock.MagicMock()
        mock_endpoints.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_ENDPOINT_RESPONSE

        service = ServiceDirectoryService(project_id="test-project")
        result = service.get_endpoint(
            "us-central1", "my-namespace", "my-service", "my-endpoint"
        )

        mock_endpoints.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service/endpoints/my-endpoint"
        )
        assert isinstance(result, Endpoint)
        assert result.name == "my-endpoint"
        assert result.address == "10.0.0.1"
        assert result.port == 8080

    def test_create_endpoint(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_endpoints = mock.MagicMock()
        mock_services.endpoints.return_value = mock_endpoints
        mock_create = mock.MagicMock()
        mock_endpoints.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_ENDPOINT_RESPONSE

        service = ServiceDirectoryService(project_id="test-project")
        result = service.create_endpoint(
            location="us-central1",
            namespace_id="my-namespace",
            service_id="my-service",
            endpoint_id="my-endpoint",
            address="10.0.0.1",
            port=8080,
            metadata={"zone": "us-central1-a"},
        )

        mock_endpoints.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service",
            endpointId="my-endpoint",
            body={
                "address": "10.0.0.1",
                "port": 8080,
                "metadata": {"zone": "us-central1-a"},
            },
        )
        assert isinstance(result, Endpoint)
        assert result.name == "my-endpoint"

    def test_create_endpoint_minimal(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_endpoints = mock.MagicMock()
        mock_services.endpoints.return_value = mock_endpoints
        mock_create = mock.MagicMock()
        mock_endpoints.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_ENDPOINT_RESPONSE

        service = ServiceDirectoryService(project_id="test-project")
        service.create_endpoint(
            location="us-central1",
            namespace_id="my-namespace",
            service_id="my-service",
            endpoint_id="my-endpoint",
        )

        call_args = mock_endpoints.create.call_args
        body = call_args[1]["body"]
        assert "address" not in body
        assert "port" not in body
        assert "metadata" not in body

    def test_delete_endpoint(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_endpoints = mock.MagicMock()
        mock_services.endpoints.return_value = mock_endpoints
        mock_delete = mock.MagicMock()
        mock_endpoints.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = ServiceDirectoryService(project_id="test-project")
        result = service.delete_endpoint(
            "us-central1", "my-namespace", "my-service", "my-endpoint"
        )

        mock_endpoints.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service/endpoints/my-endpoint"
        )
        mock_delete.execute.assert_called_once()
        assert result is True


class TestServiceDirectoryResolve:
    """Tests for the resolve_service method."""

    def test_resolve_service(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_namespaces = mock.MagicMock()
        mock_locations.namespaces.return_value = mock_namespaces
        mock_services = mock.MagicMock()
        mock_namespaces.services.return_value = mock_services
        mock_resolve = mock.MagicMock()
        mock_services.resolve.return_value = mock_resolve
        mock_resolve.execute.return_value = {
            "service": SAMPLE_SERVICE_RESPONSE,
        }

        service = ServiceDirectoryService(project_id="test-project")
        result = service.resolve_service(
            "us-central1", "my-namespace", "my-service"
        )

        mock_services.resolve.assert_called_once_with(
            name="projects/test-project/locations/us-central1/namespaces/my-namespace/services/my-service"
        )
        assert isinstance(result, ServiceEntry)
        assert result.name == "my-service"
        assert result.endpoints is not None


class TestServiceDirectoryPathHelpers:
    """Tests for internal path formatting helpers."""

    def test_namespace_path(self, mock_discovery):
        _, _ = mock_discovery
        service = ServiceDirectoryService(project_id="test-project")
        assert service._namespace_path("us-central1", "my-namespace") == (
            "projects/test-project/locations/us-central1"
            "/namespaces/my-namespace"
        )

    def test_service_path(self, mock_discovery):
        _, _ = mock_discovery
        service = ServiceDirectoryService(project_id="test-project")
        assert service._service_path(
            "us-central1", "my-namespace", "my-service"
        ) == (
            "projects/test-project/locations/us-central1"
            "/namespaces/my-namespace/services/my-service"
        )

    def test_endpoint_path(self, mock_discovery):
        _, _ = mock_discovery
        service = ServiceDirectoryService(project_id="test-project")
        assert service._endpoint_path(
            "us-central1", "my-namespace", "my-service", "my-endpoint"
        ) == (
            "projects/test-project/locations/us-central1"
            "/namespaces/my-namespace/services/my-service"
            "/endpoints/my-endpoint"
        )
