"""Tests for Cloud NAT service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.cloud_nat import CloudNATService
from gcpoto.models.cloud_nat import NATConfig
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
)


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_routers = mock.MagicMock()
        mock_service.routers.return_value = mock_routers

        yield mock_service


@pytest.fixture
def sample_router_response():
    """Sample Cloud Router API response."""
    return {
        "name": "my-router",
        "region": "us-central1",
        "network": "projects/test-project/global/networks/default",
        "nats": [
            {
                "name": "my-nat",
                "natIpAllocateOption": "AUTO_ONLY",
                "sourceSubnetworkIpRangesToNat": "ALL_SUBNETWORKS_ALL_IP_RANGES",
            }
        ],
    }


@pytest.fixture
def sample_nat_response():
    """Sample Cloud NAT API response."""
    return {
        "name": "my-nat",
        "project": "test-project",
        "region": "us-central1",
        "routerName": "my-router",
        "natIpAllocateOption": "AUTO_ONLY",
        "sourceSubnetworkIpRangesToNat": "ALL_SUBNETWORKS_ALL_IP_RANGES",
        "minPortsPerVm": 64,
        "logConfig": {"enable": True, "filter": "ALL"},
    }


@pytest.fixture
def service(mock_google_client):
    """Create a CloudNATService instance with mocked API client."""
    svc = CloudNATService(project_id="test-project")
    return svc


class TestCloudNATServiceInit:
    """Tests for CloudNATService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the CloudNATService."""
        from googleapiclient.discovery import build

        service = CloudNATService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "compute"
        assert service.version == "v1"
        build.assert_called_once_with("compute", "v1", credentials=None)


class TestListRouters:
    """Tests for listing Cloud Routers."""

    def test_list_routers(self, service, sample_router_response):
        """Test listing Cloud Routers."""
        mock_request = mock.MagicMock()
        mock_list = service.service.routers.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "items": [sample_router_response]
        }

        mock_list_next = service.service.routers.return_value.list_next
        mock_list_next.return_value = None

        routers = service.list_routers("us-central1")

        mock_list.assert_called_once_with(
            project="test-project", region="us-central1"
        )
        assert len(routers) == 1
        assert routers[0]["name"] == "my-router"

    def test_list_routers_empty(self, service):
        """Test listing routers when none exist."""
        mock_request = mock.MagicMock()
        mock_list = service.service.routers.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}

        mock_list_next = service.service.routers.return_value.list_next
        mock_list_next.return_value = None

        routers = service.list_routers("us-central1")

        assert len(routers) == 0


class TestGetRouter:
    """Tests for getting a Cloud Router."""

    def test_get_router(self, service, sample_router_response):
        """Test getting a specific Cloud Router."""
        mock_request = mock.MagicMock()
        mock_get = service.service.routers.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_router_response

        router = service.get_router("us-central1", "my-router")

        mock_get.assert_called_once_with(
            project="test-project", region="us-central1", router="my-router"
        )
        assert router["name"] == "my-router"

    def test_get_router_not_found(self, service):
        """Test getting a router that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = service.service.routers.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_router("us-central1", "nonexistent-router")


class TestCreateNAT:
    """Tests for creating a NAT configuration."""

    def test_create_nat(self, service, sample_router_response):
        """Test creating a NAT configuration."""
        mock_get_request = mock.MagicMock()
        mock_get = service.service.routers.return_value.get
        mock_get.return_value = mock_get_request
        router_without_nat = dict(sample_router_response)
        router_without_nat["nats"] = []
        mock_get_request.execute.return_value = router_without_nat

        mock_patch_request = mock.MagicMock()
        mock_patch = service.service.routers.return_value.patch
        mock_patch.return_value = mock_patch_request
        mock_patch_request.execute.return_value = {}

        nat = service.create_nat(
            region="us-central1",
            router_name="my-router",
            nat_name="my-nat",
        )

        assert isinstance(nat, NATConfig)
        assert nat.name == "my-nat"
        assert nat.nat_ip_allocate_option == "AUTO_ONLY"
        assert (
            nat.source_subnetwork_ip_ranges_to_nat
            == "ALL_SUBNETWORKS_ALL_IP_RANGES"
        )

    def test_create_nat_custom_options(self, service, sample_router_response):
        """Test creating a NAT with custom options."""
        mock_get_request = mock.MagicMock()
        mock_get = service.service.routers.return_value.get
        mock_get.return_value = mock_get_request
        router_without_nat = dict(sample_router_response)
        router_without_nat["nats"] = []
        mock_get_request.execute.return_value = router_without_nat

        mock_patch_request = mock.MagicMock()
        mock_patch = service.service.routers.return_value.patch
        mock_patch.return_value = mock_patch_request
        mock_patch_request.execute.return_value = {}

        nat = service.create_nat(
            region="us-central1",
            router_name="my-router",
            nat_name="my-nat",
            nat_ip_allocate_option="MANUAL_ONLY",
            source_subnetwork_ip_ranges_to_nat="LIST_OF_SUBNETWORKS",
        )

        assert nat.nat_ip_allocate_option == "MANUAL_ONLY"
        assert nat.source_subnetwork_ip_ranges_to_nat == "LIST_OF_SUBNETWORKS"

    def test_create_nat_router_not_found(self, service):
        """Test creating NAT on a router that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = service.service.routers.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.create_nat(
                region="us-central1",
                router_name="nonexistent-router",
                nat_name="my-nat",
            )


class TestUpdateNAT:
    """Tests for updating a NAT configuration."""

    def test_update_nat(self, service, sample_router_response):
        """Test updating a NAT configuration."""
        mock_get_request = mock.MagicMock()
        mock_get = service.service.routers.return_value.get
        mock_get.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_router_response

        mock_patch_request = mock.MagicMock()
        mock_patch = service.service.routers.return_value.patch
        mock_patch.return_value = mock_patch_request
        mock_patch_request.execute.return_value = {}

        nat = service.update_nat(
            region="us-central1",
            router_name="my-router",
            nat_name="my-nat",
            update_fields={"minPortsPerVm": 128},
        )

        assert isinstance(nat, NATConfig)
        assert nat.name == "my-nat"

    def test_update_nat_not_found(self, service, sample_router_response):
        """Test updating a NAT that does not exist."""
        mock_get_request = mock.MagicMock()
        mock_get = service.service.routers.return_value.get
        mock_get.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_router_response

        with pytest.raises(ResourceNotFoundError):
            service.update_nat(
                region="us-central1",
                router_name="my-router",
                nat_name="nonexistent-nat",
                update_fields={"minPortsPerVm": 128},
            )


class TestDeleteNAT:
    """Tests for deleting a NAT configuration."""

    def test_delete_nat(self, service, sample_router_response):
        """Test deleting a NAT configuration."""
        mock_get_request = mock.MagicMock()
        mock_get = service.service.routers.return_value.get
        mock_get.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_router_response

        mock_patch_request = mock.MagicMock()
        mock_patch = service.service.routers.return_value.patch
        mock_patch.return_value = mock_patch_request
        mock_patch_request.execute.return_value = {}

        result = service.delete_nat("us-central1", "my-router", "my-nat")

        assert result is True

    def test_delete_nat_not_found(self, service, sample_router_response):
        """Test deleting a NAT that does not exist."""
        mock_get_request = mock.MagicMock()
        mock_get = service.service.routers.return_value.get
        mock_get.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_router_response

        with pytest.raises(ResourceNotFoundError):
            service.delete_nat(
                "us-central1", "my-router", "nonexistent-nat"
            )


class TestGetNATMappingInfo:
    """Tests for getting NAT mapping info."""

    def test_get_nat_mapping_info(self, service):
        """Test getting NAT mapping information."""
        mock_request = mock.MagicMock()
        mock_get_mapping = (
            service.service.routers.return_value.getNatMappingInfo
        )
        mock_get_mapping.return_value = mock_request
        mock_request.execute.return_value = {
            "result": [
                {
                    "instanceName": "instance-1",
                    "interfaceNatMappings": [],
                }
            ]
        }

        mock_get_next = (
            service.service.routers.return_value.getNatMappingInfo_next
        )
        mock_get_next.return_value = None

        mappings = service.get_nat_mapping_info("us-central1", "my-router")

        mock_get_mapping.assert_called_once_with(
            project="test-project", region="us-central1", router="my-router"
        )
        assert len(mappings) == 1
        assert mappings[0]["instanceName"] == "instance-1"

    def test_get_nat_mapping_info_not_found(self, service):
        """Test getting mapping info for a router that does not exist."""
        mock_request = mock.MagicMock()
        mock_get_mapping = (
            service.service.routers.return_value.getNatMappingInfo
        )
        mock_get_mapping.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_nat_mapping_info("us-central1", "nonexistent-router")


class TestNATConfigModel:
    """Tests for the NATConfig model."""

    def test_from_api_response(self, sample_nat_response):
        """Test creating a NATConfig from an API response."""
        nat = NATConfig.from_api_response(sample_nat_response)

        assert nat.name == "my-nat"
        assert nat.region == "us-central1"
        assert nat.router_name == "my-router"
        assert nat.nat_ip_allocate_option == "AUTO_ONLY"
        assert (
            nat.source_subnetwork_ip_ranges_to_nat
            == "ALL_SUBNETWORKS_ALL_IP_RANGES"
        )
        assert nat.min_ports_per_vm == 64
        assert nat.log_config == {"enable": True, "filter": "ALL"}
        assert nat.type == "compute.natConfig"

    def test_from_api_response_minimal(self):
        """Test creating a NATConfig from a minimal API response."""
        nat = NATConfig.from_api_response({"name": "simple-nat"})

        assert nat.name == "simple-nat"
        assert nat.region == ""
        assert nat.nat_ip_allocate_option == "AUTO_ONLY"
        assert nat.subnetworks is None
        assert nat.nat_ips is None
