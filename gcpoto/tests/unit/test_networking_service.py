"""Tests for the VPC / Networking service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.networking import NetworkingService
from gcpoto.models.networking import (
    VPCNetwork,
    Subnet,
    FirewallRule,
    StaticAddress,
)


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


# ---- Service Initialization ----


class TestNetworkingServiceInit:
    def test_initialization(self, mock_discovery):
        """Test initializing a NetworkingService."""
        mock_build, _ = mock_discovery
        service = NetworkingService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "compute"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == VPCNetwork
        mock_build.assert_called_once_with("compute", "v1", credentials=None)

    def test_initialization_with_credentials(self, mock_discovery):
        """Test initializing with a credentials file."""
        mock_build, _ = mock_discovery
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            service = NetworkingService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert service.credentials_file == "/path/to/creds.json"


# ---- VPCNetwork Model ----


class TestVPCNetworkModel:
    def test_from_api_response(self):
        """Test creating a VPCNetwork from an API response."""
        response = {
            "id": "123456",
            "name": "my-vpc",
            "project": "test-project",
            "autoCreateSubnetworks": False,
            "routingConfig": {"routingMode": "GLOBAL"},
            "mtu": 1460,
            "description": "Test VPC network",
            "peerings": [{"name": "peer-1", "network": "other-net"}],
            "labels": {"env": "test"},
            "creationTimestamp": "2025-01-01T00:00:00Z",
        }
        network = VPCNetwork.from_api_response(response)

        assert network.id == "123456"
        assert network.name == "my-vpc"
        assert network.type == "compute.network"
        assert network.project == "test-project"
        assert network.auto_create_subnetworks is False
        assert network.routing_mode == "GLOBAL"
        assert network.mtu == 1460
        assert network.description == "Test VPC network"
        assert network.peerings == [{"name": "peer-1", "network": "other-net"}]
        assert network.labels == {"env": "test"}
        assert network._tags == {"env": "test"}

    def test_from_api_response_defaults(self):
        """Test VPCNetwork from API response with minimal data."""
        response = {"id": "1", "name": "default"}
        network = VPCNetwork.from_api_response(response)

        assert network.name == "default"
        assert network.auto_create_subnetworks is True
        assert network.routing_mode == "REGIONAL"
        assert network.mtu is None
        assert network.description is None
        assert network.peerings is None

    def test_get_tag(self):
        """Test the get_tag method."""
        response = {
            "id": "1",
            "name": "test",
            "labels": {"env": "prod"},
        }
        network = VPCNetwork.from_api_response(response)

        assert network.get_tag("env") == "prod"
        assert network.get_tag("missing") == ""
        assert network.get_tag("missing", "default") == "default"


# ---- Subnet Model ----


class TestSubnetModel:
    def test_from_api_response(self):
        """Test creating a Subnet from an API response."""
        response = {
            "id": "789",
            "name": "my-subnet",
            "project": "test-project",
            "network": "projects/test-project/global/networks/my-vpc",
            "region": "projects/test-project/regions/us-central1",
            "ipCidrRange": "10.0.0.0/24",
            "gatewayAddress": "10.0.0.1",
            "privateIpGoogleAccess": True,
            "secondaryIpRanges": [
                {"rangeName": "pods", "ipCidrRange": "10.1.0.0/16"},
            ],
            "purpose": "PRIVATE",
            "labels": {"team": "platform"},
            "creationTimestamp": "2025-01-01T00:00:00Z",
        }
        subnet = Subnet.from_api_response(response)

        assert subnet.id == "789"
        assert subnet.name == "my-subnet"
        assert subnet.type == "compute.subnetwork"
        assert subnet.network == "projects/test-project/global/networks/my-vpc"
        assert subnet.region == "us-central1"
        assert subnet.ip_cidr_range == "10.0.0.0/24"
        assert subnet.gateway_address == "10.0.0.1"
        assert subnet.private_ip_google_access is True
        assert subnet.secondary_ip_ranges == [
            {"rangeName": "pods", "ipCidrRange": "10.1.0.0/16"}
        ]
        assert subnet.purpose == "PRIVATE"
        assert subnet._tags == {"team": "platform"}

    def test_from_api_response_defaults(self):
        """Test Subnet from API response with minimal data."""
        response = {"id": "1", "name": "default"}
        subnet = Subnet.from_api_response(response)

        assert subnet.network == ""
        assert subnet.region == ""
        assert subnet.ip_cidr_range == ""
        assert subnet.gateway_address is None
        assert subnet.private_ip_google_access is False
        assert subnet.secondary_ip_ranges is None
        assert subnet.purpose is None

    def test_get_tag(self):
        """Test the get_tag method on Subnet."""
        response = {
            "id": "1",
            "name": "test",
            "labels": {"team": "infra"},
        }
        subnet = Subnet.from_api_response(response)
        assert subnet.get_tag("team") == "infra"
        assert subnet.get_tag("missing", "n/a") == "n/a"


# ---- FirewallRule Model ----


class TestFirewallRuleModel:
    def test_from_api_response(self):
        """Test creating a FirewallRule from an API response."""
        response = {
            "id": "456",
            "name": "allow-http",
            "project": "test-project",
            "network": "projects/test-project/global/networks/my-vpc",
            "direction": "INGRESS",
            "priority": 1000,
            "allowed": [{"IPProtocol": "tcp", "ports": ["80", "443"]}],
            "sourceRanges": ["0.0.0.0/0"],
            "targetTags": ["http-server"],
            "disabled": False,
            "labels": {"managed-by": "gcpoto"},
            "creationTimestamp": "2025-06-01T00:00:00Z",
        }
        rule = FirewallRule.from_api_response(response)

        assert rule.id == "456"
        assert rule.name == "allow-http"
        assert rule.type == "compute.firewall"
        assert rule.network == "projects/test-project/global/networks/my-vpc"
        assert rule.direction == "INGRESS"
        assert rule.priority == 1000
        assert rule.allowed == [{"IPProtocol": "tcp", "ports": ["80", "443"]}]
        assert rule.denied is None
        assert rule.source_ranges == ["0.0.0.0/0"]
        assert rule.destination_ranges is None
        assert rule.source_tags is None
        assert rule.target_tags == ["http-server"]
        assert rule.disabled is False
        assert rule._tags == {"managed-by": "gcpoto"}

    def test_from_api_response_egress_deny(self):
        """Test FirewallRule with EGRESS direction and denied rules."""
        response = {
            "id": "789",
            "name": "deny-outbound",
            "direction": "EGRESS",
            "priority": 65534,
            "denied": [{"IPProtocol": "all"}],
            "destinationRanges": ["10.0.0.0/8"],
            "disabled": True,
        }
        rule = FirewallRule.from_api_response(response)

        assert rule.direction == "EGRESS"
        assert rule.priority == 65534
        assert rule.denied == [{"IPProtocol": "all"}]
        assert rule.allowed is None
        assert rule.destination_ranges == ["10.0.0.0/8"]
        assert rule.disabled is True

    def test_from_api_response_defaults(self):
        """Test FirewallRule from API response with minimal data."""
        response = {"id": "1", "name": "test"}
        rule = FirewallRule.from_api_response(response)

        assert rule.direction == "INGRESS"
        assert rule.priority == 1000
        assert rule.disabled is False

    def test_get_tag(self):
        """Test the get_tag method on FirewallRule."""
        response = {
            "id": "1",
            "name": "test",
            "labels": {"env": "staging"},
        }
        rule = FirewallRule.from_api_response(response)
        assert rule.get_tag("env") == "staging"


# ---- StaticAddress Model ----


class TestStaticAddressModel:
    def test_from_api_response(self):
        """Test creating a StaticAddress from an API response."""
        response = {
            "id": "999",
            "name": "my-static-ip",
            "project": "test-project",
            "region": "projects/test-project/regions/us-central1",
            "address": "35.192.0.1",
            "addressType": "EXTERNAL",
            "status": "RESERVED",
            "networkTier": "PREMIUM",
            "labels": {"app": "web"},
            "creationTimestamp": "2025-03-01T00:00:00Z",
        }
        addr = StaticAddress.from_api_response(response)

        assert addr.id == "999"
        assert addr.name == "my-static-ip"
        assert addr.type == "compute.address"
        assert addr.region == "us-central1"
        assert addr.address == "35.192.0.1"
        assert addr.address_type == "EXTERNAL"
        assert addr.status == "RESERVED"
        assert addr.network_tier == "PREMIUM"
        assert addr.purpose is None
        assert addr.subnetwork is None

    def test_from_api_response_internal(self):
        """Test StaticAddress with INTERNAL type."""
        response = {
            "id": "888",
            "name": "internal-ip",
            "region": "projects/test-project/regions/us-east1",
            "address": "10.128.0.5",
            "addressType": "INTERNAL",
            "status": "IN_USE",
            "purpose": "GCE_ENDPOINT",
            "subnetwork": "projects/test-project/regions/us-east1/subnetworks/default",
        }
        addr = StaticAddress.from_api_response(response)

        assert addr.address_type == "INTERNAL"
        assert addr.status == "IN_USE"
        assert addr.purpose == "GCE_ENDPOINT"
        assert addr.subnetwork == "projects/test-project/regions/us-east1/subnetworks/default"
        assert addr.region == "us-east1"

    def test_from_api_response_no_region(self):
        """Test StaticAddress with no region (global)."""
        response = {"id": "1", "name": "global-ip", "status": "RESERVED"}
        addr = StaticAddress.from_api_response(response)
        assert addr.region is None

    def test_get_tag(self):
        """Test the get_tag method on StaticAddress."""
        response = {
            "id": "1",
            "name": "test",
            "labels": {"purpose": "lb"},
        }
        addr = StaticAddress.from_api_response(response)
        assert addr.get_tag("purpose") == "lb"
        assert addr.get_tag("missing", "fallback") == "fallback"


# ---- NetworkingService: Networks ----


class TestNetworkingServiceNetworks:
    @pytest.fixture
    def service(self, mock_discovery):
        """Create a NetworkingService with mocked discovery."""
        _, mock_svc = mock_discovery
        svc = NetworkingService(project_id="test-project")
        svc.service = mock_svc
        return svc

    def test_list_networks(self, service):
        """Test listing VPC networks."""
        mock_networks = service.service.networks()
        mock_networks.list().execute.return_value = {
            "items": [
                {
                    "id": "1",
                    "name": "default",
                    "autoCreateSubnetworks": True,
                    "routingConfig": {"routingMode": "REGIONAL"},
                },
                {
                    "id": "2",
                    "name": "custom-vpc",
                    "autoCreateSubnetworks": False,
                    "routingConfig": {"routingMode": "GLOBAL"},
                    "mtu": 1500,
                },
            ]
        }

        results = service.list_networks()

        assert len(results) == 2
        assert isinstance(results[0], VPCNetwork)
        assert results[0].name == "default"
        assert results[0].auto_create_subnetworks is True
        assert results[1].name == "custom-vpc"
        assert results[1].routing_mode == "GLOBAL"
        assert results[1].mtu == 1500

    def test_list_networks_empty(self, service):
        """Test listing networks when none exist."""
        mock_networks = service.service.networks()
        mock_networks.list().execute.return_value = {}

        results = service.list_networks()
        assert results == []

    def test_get_network(self, service):
        """Test getting a specific VPC network."""
        mock_networks = service.service.networks()
        mock_networks.get().execute.return_value = {
            "id": "1",
            "name": "my-vpc",
            "autoCreateSubnetworks": False,
            "routingConfig": {"routingMode": "GLOBAL"},
            "description": "My custom VPC",
        }

        result = service.get_network("my-vpc")

        assert isinstance(result, VPCNetwork)
        assert result.name == "my-vpc"
        assert result.auto_create_subnetworks is False
        assert result.routing_mode == "GLOBAL"
        assert result.description == "My custom VPC"
        mock_networks.get.assert_called_with(
            project="test-project", network="my-vpc"
        )

    def test_create_network(self, service):
        """Test creating a VPC network."""
        mock_networks = service.service.networks()
        mock_networks.insert().execute.return_value = {
            "id": "3",
            "name": "new-vpc",
            "autoCreateSubnetworks": False,
            "routingConfig": {"routingMode": "GLOBAL"},
            "description": "A new VPC",
        }

        result = service.create_network(
            network_name="new-vpc",
            auto_create_subnetworks=False,
            routing_mode="GLOBAL",
            description="A new VPC",
        )

        assert isinstance(result, VPCNetwork)
        assert result.name == "new-vpc"
        assert result.routing_mode == "GLOBAL"
        mock_networks.insert.assert_called_with(
            project="test-project",
            body={
                "name": "new-vpc",
                "autoCreateSubnetworks": False,
                "routingConfig": {"routingMode": "GLOBAL"},
                "description": "A new VPC",
            },
        )

    def test_create_network_defaults(self, service):
        """Test creating a VPC network with default parameters."""
        mock_networks = service.service.networks()
        mock_networks.insert().execute.return_value = {
            "id": "4",
            "name": "simple-vpc",
            "autoCreateSubnetworks": True,
            "routingConfig": {"routingMode": "REGIONAL"},
        }

        result = service.create_network(network_name="simple-vpc")

        assert result.name == "simple-vpc"
        mock_networks.insert.assert_called_with(
            project="test-project",
            body={
                "name": "simple-vpc",
                "autoCreateSubnetworks": True,
                "routingConfig": {"routingMode": "REGIONAL"},
            },
        )

    def test_delete_network(self, service):
        """Test deleting a VPC network."""
        mock_networks = service.service.networks()
        mock_networks.delete().execute.return_value = {}

        result = service.delete_network("old-vpc")

        assert result is True
        mock_networks.delete.assert_called_with(
            project="test-project", network="old-vpc"
        )


# ---- NetworkingService: Subnets ----


class TestNetworkingServiceSubnets:
    @pytest.fixture
    def service(self, mock_discovery):
        """Create a NetworkingService with mocked discovery."""
        _, mock_svc = mock_discovery
        svc = NetworkingService(project_id="test-project")
        svc.service = mock_svc
        return svc

    def test_list_subnets_by_region(self, service):
        """Test listing subnets in a specific region."""
        mock_subnets = service.service.subnetworks()
        mock_subnets.list().execute.return_value = {
            "items": [
                {
                    "id": "1",
                    "name": "subnet-a",
                    "network": "projects/test-project/global/networks/my-vpc",
                    "region": "projects/test-project/regions/us-central1",
                    "ipCidrRange": "10.0.0.0/24",
                },
                {
                    "id": "2",
                    "name": "subnet-b",
                    "network": "projects/test-project/global/networks/my-vpc",
                    "region": "projects/test-project/regions/us-central1",
                    "ipCidrRange": "10.0.1.0/24",
                },
            ]
        }

        results = service.list_subnets(region="us-central1")

        assert len(results) == 2
        assert isinstance(results[0], Subnet)
        assert results[0].name == "subnet-a"
        assert results[0].ip_cidr_range == "10.0.0.0/24"
        assert results[1].name == "subnet-b"
        mock_subnets.list.assert_called_with(
            project="test-project", region="us-central1"
        )

    def test_list_subnets_aggregated(self, service):
        """Test listing subnets across all regions."""
        mock_subnets = service.service.subnetworks()
        mock_subnets.aggregatedList().execute.return_value = {
            "items": {
                "regions/us-central1": {
                    "subnetworks": [
                        {
                            "id": "1",
                            "name": "subnet-us",
                            "region": "projects/test-project/regions/us-central1",
                            "ipCidrRange": "10.0.0.0/24",
                        }
                    ]
                },
                "regions/europe-west1": {
                    "subnetworks": [
                        {
                            "id": "2",
                            "name": "subnet-eu",
                            "region": "projects/test-project/regions/europe-west1",
                            "ipCidrRange": "10.1.0.0/24",
                        }
                    ]
                },
            }
        }

        results = service.list_subnets()

        assert len(results) == 2
        names = {s.name for s in results}
        assert "subnet-us" in names
        assert "subnet-eu" in names

    def test_list_subnets_empty(self, service):
        """Test listing subnets when none exist in the region."""
        mock_subnets = service.service.subnetworks()
        mock_subnets.list().execute.return_value = {}

        results = service.list_subnets(region="us-central1")
        assert results == []

    def test_get_subnet(self, service):
        """Test getting a specific subnet."""
        mock_subnets = service.service.subnetworks()
        mock_subnets.get().execute.return_value = {
            "id": "1",
            "name": "my-subnet",
            "network": "projects/test-project/global/networks/my-vpc",
            "region": "projects/test-project/regions/us-central1",
            "ipCidrRange": "10.0.0.0/24",
            "gatewayAddress": "10.0.0.1",
            "privateIpGoogleAccess": True,
        }

        result = service.get_subnet("us-central1", "my-subnet")

        assert isinstance(result, Subnet)
        assert result.name == "my-subnet"
        assert result.region == "us-central1"
        assert result.gateway_address == "10.0.0.1"
        assert result.private_ip_google_access is True
        mock_subnets.get.assert_called_with(
            project="test-project",
            region="us-central1",
            subnetwork="my-subnet",
        )

    def test_create_subnet(self, service):
        """Test creating a subnet."""
        mock_subnets = service.service.subnetworks()
        mock_subnets.insert().execute.return_value = {
            "id": "3",
            "name": "new-subnet",
            "network": "projects/test-project/global/networks/my-vpc",
            "region": "projects/test-project/regions/us-central1",
            "ipCidrRange": "10.2.0.0/24",
        }

        result = service.create_subnet(
            region="us-central1",
            subnet_name="new-subnet",
            network="projects/test-project/global/networks/my-vpc",
            ip_cidr_range="10.2.0.0/24",
        )

        assert isinstance(result, Subnet)
        assert result.name == "new-subnet"
        assert result.ip_cidr_range == "10.2.0.0/24"
        mock_subnets.insert.assert_called_with(
            project="test-project",
            region="us-central1",
            body={
                "name": "new-subnet",
                "network": "projects/test-project/global/networks/my-vpc",
                "ipCidrRange": "10.2.0.0/24",
            },
        )

    def test_create_subnet_with_secondary_ranges(self, service):
        """Test creating a subnet with secondary IP ranges."""
        mock_subnets = service.service.subnetworks()
        mock_subnets.insert().execute.return_value = {
            "id": "4",
            "name": "gke-subnet",
            "network": "projects/test-project/global/networks/my-vpc",
            "region": "projects/test-project/regions/us-central1",
            "ipCidrRange": "10.3.0.0/24",
            "secondaryIpRanges": [
                {"rangeName": "pods", "ipCidrRange": "10.4.0.0/16"},
                {"rangeName": "services", "ipCidrRange": "10.5.0.0/20"},
            ],
        }

        secondary = [
            {"rangeName": "pods", "ipCidrRange": "10.4.0.0/16"},
            {"rangeName": "services", "ipCidrRange": "10.5.0.0/20"},
        ]
        result = service.create_subnet(
            region="us-central1",
            subnet_name="gke-subnet",
            network="projects/test-project/global/networks/my-vpc",
            ip_cidr_range="10.3.0.0/24",
            secondary_ip_ranges=secondary,
        )

        assert result.secondary_ip_ranges is not None
        assert len(result.secondary_ip_ranges) == 2
        mock_subnets.insert.assert_called_with(
            project="test-project",
            region="us-central1",
            body={
                "name": "gke-subnet",
                "network": "projects/test-project/global/networks/my-vpc",
                "ipCidrRange": "10.3.0.0/24",
                "secondaryIpRanges": secondary,
            },
        )

    def test_delete_subnet(self, service):
        """Test deleting a subnet."""
        mock_subnets = service.service.subnetworks()
        mock_subnets.delete().execute.return_value = {}

        result = service.delete_subnet("us-central1", "old-subnet")

        assert result is True
        mock_subnets.delete.assert_called_with(
            project="test-project",
            region="us-central1",
            subnetwork="old-subnet",
        )


# ---- NetworkingService: Firewall Rules ----


class TestNetworkingServiceFirewalls:
    @pytest.fixture
    def service(self, mock_discovery):
        """Create a NetworkingService with mocked discovery."""
        _, mock_svc = mock_discovery
        svc = NetworkingService(project_id="test-project")
        svc.service = mock_svc
        return svc

    def test_list_firewall_rules(self, service):
        """Test listing firewall rules."""
        mock_firewalls = service.service.firewalls()
        mock_firewalls.list().execute.return_value = {
            "items": [
                {
                    "id": "1",
                    "name": "allow-ssh",
                    "network": "projects/test-project/global/networks/default",
                    "direction": "INGRESS",
                    "priority": 1000,
                    "allowed": [{"IPProtocol": "tcp", "ports": ["22"]}],
                    "sourceRanges": ["0.0.0.0/0"],
                },
                {
                    "id": "2",
                    "name": "allow-http",
                    "network": "projects/test-project/global/networks/default",
                    "direction": "INGRESS",
                    "priority": 1000,
                    "allowed": [{"IPProtocol": "tcp", "ports": ["80"]}],
                    "targetTags": ["http-server"],
                },
            ]
        }

        results = service.list_firewall_rules()

        assert len(results) == 2
        assert isinstance(results[0], FirewallRule)
        assert results[0].name == "allow-ssh"
        assert results[0].source_ranges == ["0.0.0.0/0"]
        assert results[1].name == "allow-http"
        assert results[1].target_tags == ["http-server"]

    def test_list_firewall_rules_empty(self, service):
        """Test listing firewall rules when none exist."""
        mock_firewalls = service.service.firewalls()
        mock_firewalls.list().execute.return_value = {}

        results = service.list_firewall_rules()
        assert results == []

    def test_get_firewall_rule(self, service):
        """Test getting a specific firewall rule."""
        mock_firewalls = service.service.firewalls()
        mock_firewalls.get().execute.return_value = {
            "id": "1",
            "name": "allow-ssh",
            "network": "projects/test-project/global/networks/default",
            "direction": "INGRESS",
            "priority": 1000,
            "allowed": [{"IPProtocol": "tcp", "ports": ["22"]}],
            "sourceRanges": ["0.0.0.0/0"],
        }

        result = service.get_firewall_rule("allow-ssh")

        assert isinstance(result, FirewallRule)
        assert result.name == "allow-ssh"
        assert result.allowed == [{"IPProtocol": "tcp", "ports": ["22"]}]
        mock_firewalls.get.assert_called_with(
            project="test-project", firewall="allow-ssh"
        )

    def test_create_firewall_rule(self, service):
        """Test creating a firewall rule."""
        mock_firewalls = service.service.firewalls()
        mock_firewalls.insert().execute.return_value = {
            "id": "3",
            "name": "allow-https",
            "network": "projects/test-project/global/networks/my-vpc",
            "direction": "INGRESS",
            "priority": 900,
            "allowed": [{"IPProtocol": "tcp", "ports": ["443"]}],
            "sourceRanges": ["0.0.0.0/0"],
            "targetTags": ["https-server"],
        }

        result = service.create_firewall_rule(
            firewall_name="allow-https",
            network="projects/test-project/global/networks/my-vpc",
            direction="INGRESS",
            priority=900,
            allowed=[{"IPProtocol": "tcp", "ports": ["443"]}],
            source_ranges=["0.0.0.0/0"],
            target_tags=["https-server"],
        )

        assert isinstance(result, FirewallRule)
        assert result.name == "allow-https"
        assert result.priority == 900
        mock_firewalls.insert.assert_called_with(
            project="test-project",
            body={
                "name": "allow-https",
                "network": "projects/test-project/global/networks/my-vpc",
                "direction": "INGRESS",
                "priority": 900,
                "allowed": [{"IPProtocol": "tcp", "ports": ["443"]}],
                "sourceRanges": ["0.0.0.0/0"],
                "targetTags": ["https-server"],
            },
        )

    def test_create_firewall_rule_deny(self, service):
        """Test creating a deny firewall rule."""
        mock_firewalls = service.service.firewalls()
        mock_firewalls.insert().execute.return_value = {
            "id": "4",
            "name": "deny-all-egress",
            "network": "projects/test-project/global/networks/my-vpc",
            "direction": "EGRESS",
            "priority": 65534,
            "denied": [{"IPProtocol": "all"}],
        }

        result = service.create_firewall_rule(
            firewall_name="deny-all-egress",
            network="projects/test-project/global/networks/my-vpc",
            direction="EGRESS",
            priority=65534,
            denied=[{"IPProtocol": "all"}],
        )

        assert result.name == "deny-all-egress"
        assert result.direction == "EGRESS"
        assert result.denied == [{"IPProtocol": "all"}]

    def test_update_firewall_rule(self, service):
        """Test updating a firewall rule."""
        mock_firewalls = service.service.firewalls()
        mock_firewalls.patch().execute.return_value = {
            "id": "1",
            "name": "allow-ssh",
            "network": "projects/test-project/global/networks/default",
            "direction": "INGRESS",
            "priority": 500,
            "allowed": [{"IPProtocol": "tcp", "ports": ["22"]}],
            "sourceRanges": ["10.0.0.0/8"],
            "disabled": False,
        }

        result = service.update_firewall_rule(
            "allow-ssh",
            priority=500,
            source_ranges=["10.0.0.0/8"],
        )

        assert isinstance(result, FirewallRule)
        assert result.priority == 500
        mock_firewalls.patch.assert_called_with(
            project="test-project",
            firewall="allow-ssh",
            body={
                "priority": 500,
                "sourceRanges": ["10.0.0.0/8"],
            },
        )

    def test_update_firewall_rule_disable(self, service):
        """Test disabling a firewall rule via update."""
        mock_firewalls = service.service.firewalls()
        mock_firewalls.patch().execute.return_value = {
            "id": "1",
            "name": "allow-ssh",
            "network": "projects/test-project/global/networks/default",
            "direction": "INGRESS",
            "priority": 1000,
            "disabled": True,
        }

        result = service.update_firewall_rule("allow-ssh", disabled=True)

        assert result.disabled is True
        mock_firewalls.patch.assert_called_with(
            project="test-project",
            firewall="allow-ssh",
            body={"disabled": True},
        )

    def test_delete_firewall_rule(self, service):
        """Test deleting a firewall rule."""
        mock_firewalls = service.service.firewalls()
        mock_firewalls.delete().execute.return_value = {}

        result = service.delete_firewall_rule("old-rule")

        assert result is True
        mock_firewalls.delete.assert_called_with(
            project="test-project", firewall="old-rule"
        )


# ---- NetworkingService: Static Addresses ----


class TestNetworkingServiceAddresses:
    @pytest.fixture
    def service(self, mock_discovery):
        """Create a NetworkingService with mocked discovery."""
        _, mock_svc = mock_discovery
        svc = NetworkingService(project_id="test-project")
        svc.service = mock_svc
        return svc

    def test_list_addresses(self, service):
        """Test listing static addresses."""
        mock_addresses = service.service.addresses()
        mock_addresses.list().execute.return_value = {
            "items": [
                {
                    "id": "1",
                    "name": "web-ip",
                    "region": "projects/test-project/regions/us-central1",
                    "address": "35.192.0.1",
                    "addressType": "EXTERNAL",
                    "status": "RESERVED",
                    "networkTier": "PREMIUM",
                },
                {
                    "id": "2",
                    "name": "internal-ip",
                    "region": "projects/test-project/regions/us-central1",
                    "address": "10.128.0.5",
                    "addressType": "INTERNAL",
                    "status": "IN_USE",
                },
            ]
        }

        results = service.list_addresses(region="us-central1")

        assert len(results) == 2
        assert isinstance(results[0], StaticAddress)
        assert results[0].name == "web-ip"
        assert results[0].address == "35.192.0.1"
        assert results[0].address_type == "EXTERNAL"
        assert results[1].name == "internal-ip"
        assert results[1].address_type == "INTERNAL"

    def test_list_addresses_empty(self, service):
        """Test listing addresses when none exist."""
        mock_addresses = service.service.addresses()
        mock_addresses.list().execute.return_value = {}

        results = service.list_addresses(region="us-central1")
        assert results == []

    def test_reserve_address_external(self, service):
        """Test reserving an external static address."""
        mock_addresses = service.service.addresses()
        mock_addresses.insert().execute.return_value = {
            "id": "3",
            "name": "new-ip",
            "region": "projects/test-project/regions/us-central1",
            "address": "35.192.0.10",
            "addressType": "EXTERNAL",
            "status": "RESERVED",
        }

        result = service.reserve_address(
            region="us-central1",
            address_name="new-ip",
            address_type="EXTERNAL",
        )

        assert isinstance(result, StaticAddress)
        assert result.name == "new-ip"
        assert result.address_type == "EXTERNAL"
        assert result.status == "RESERVED"
        mock_addresses.insert.assert_called_with(
            project="test-project",
            region="us-central1",
            body={
                "name": "new-ip",
                "addressType": "EXTERNAL",
            },
        )

    def test_reserve_address_internal(self, service):
        """Test reserving an internal static address."""
        mock_addresses = service.service.addresses()
        mock_addresses.insert().execute.return_value = {
            "id": "4",
            "name": "internal-addr",
            "region": "projects/test-project/regions/us-east1",
            "address": "10.128.0.99",
            "addressType": "INTERNAL",
            "status": "RESERVED",
        }

        result = service.reserve_address(
            region="us-east1",
            address_name="internal-addr",
            address_type="INTERNAL",
        )

        assert result.address_type == "INTERNAL"
        mock_addresses.insert.assert_called_with(
            project="test-project",
            region="us-east1",
            body={
                "name": "internal-addr",
                "addressType": "INTERNAL",
            },
        )

    def test_reserve_address_default_type(self, service):
        """Test reserving an address with default type (EXTERNAL)."""
        mock_addresses = service.service.addresses()
        mock_addresses.insert().execute.return_value = {
            "id": "5",
            "name": "default-ip",
            "addressType": "EXTERNAL",
            "status": "RESERVED",
        }

        service.reserve_address(region="us-central1", address_name="default-ip")

        mock_addresses.insert.assert_called_with(
            project="test-project",
            region="us-central1",
            body={
                "name": "default-ip",
                "addressType": "EXTERNAL",
            },
        )

    def test_release_address(self, service):
        """Test releasing a static address."""
        mock_addresses = service.service.addresses()
        mock_addresses.delete().execute.return_value = {}

        result = service.release_address("us-central1", "old-ip")

        assert result is True
        mock_addresses.delete.assert_called_with(
            project="test-project",
            region="us-central1",
            address="old-ip",
        )
