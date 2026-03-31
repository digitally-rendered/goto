"""Tests for Cloud VPN service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.vpn import VPNService
from gcpoto.models.vpn import VPNGateway, VPNTunnel
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

        mock_vpn_gateways = mock.MagicMock()
        mock_service.vpnGateways.return_value = mock_vpn_gateways

        mock_vpn_tunnels = mock.MagicMock()
        mock_service.vpnTunnels.return_value = mock_vpn_tunnels

        yield mock_service


@pytest.fixture
def sample_vpn_gateway_response():
    """Sample VPN gateway API response."""
    return {
        "id": "123456789",
        "name": "my-vpn-gateway",
        "region": "us-central1",
        "network": "projects/test-project/global/networks/default",
        "vpnInterfaces": [
            {"id": 0, "ipAddress": "35.220.1.1"},
            {"id": 1, "ipAddress": "35.220.1.2"},
        ],
        "labels": {"env": "test"},
        "project": "test-project",
        "creationTimestamp": "2024-01-15T10:30:00.000Z",
    }


@pytest.fixture
def sample_vpn_tunnel_response():
    """Sample VPN tunnel API response."""
    return {
        "id": "987654321",
        "name": "my-vpn-tunnel",
        "region": "us-central1",
        "vpnGateway": "projects/test-project/regions/us-central1/vpnGateways/my-vpn-gateway",
        "peerIp": "203.0.113.1",
        "sharedSecret": "my-secret",
        "ikeVersion": 2,
        "status": "ESTABLISHED",
        "detailedStatus": "Tunnel is up and running.",
        "localTrafficSelector": ["10.0.0.0/24"],
        "remoteTrafficSelector": ["192.168.0.0/24"],
        "project": "test-project",
        "creationTimestamp": "2024-01-15T11:00:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a VPNService instance with mocked API client."""
    svc = VPNService(project_id="test-project")
    return svc


class TestVPNServiceInit:
    """Tests for VPNService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the VPNService."""
        from googleapiclient.discovery import build

        service = VPNService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "compute"
        assert service.version == "v1"
        build.assert_called_once_with("compute", "v1", credentials=None)


class TestListVPNGateways:
    """Tests for listing VPN gateways."""

    def test_list_vpn_gateways(self, service, sample_vpn_gateway_response):
        """Test listing VPN gateways."""
        mock_request = mock.MagicMock()
        mock_list = service.service.vpnGateways.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "items": [sample_vpn_gateway_response]
        }

        mock_list_next = service.service.vpnGateways.return_value.list_next
        mock_list_next.return_value = None

        gateways = service.list_vpn_gateways("us-central1")

        mock_list.assert_called_once_with(
            project="test-project", region="us-central1"
        )
        assert len(gateways) == 1
        assert isinstance(gateways[0], VPNGateway)
        assert gateways[0].name == "my-vpn-gateway"
        assert gateways[0].network == "projects/test-project/global/networks/default"

    def test_list_vpn_gateways_empty(self, service):
        """Test listing gateways when none exist."""
        mock_request = mock.MagicMock()
        mock_list = service.service.vpnGateways.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}

        mock_list_next = service.service.vpnGateways.return_value.list_next
        mock_list_next.return_value = None

        gateways = service.list_vpn_gateways("us-central1")

        assert len(gateways) == 0


class TestGetVPNGateway:
    """Tests for getting a VPN gateway."""

    def test_get_vpn_gateway(self, service, sample_vpn_gateway_response):
        """Test getting a specific VPN gateway."""
        mock_request = mock.MagicMock()
        mock_get = service.service.vpnGateways.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_vpn_gateway_response

        gateway = service.get_vpn_gateway("us-central1", "my-vpn-gateway")

        mock_get.assert_called_once_with(
            project="test-project",
            region="us-central1",
            vpnGateway="my-vpn-gateway",
        )
        assert isinstance(gateway, VPNGateway)
        assert gateway.name == "my-vpn-gateway"
        assert len(gateway.vpn_interfaces) == 2

    def test_get_vpn_gateway_not_found(self, service):
        """Test getting a gateway that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = service.service.vpnGateways.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_vpn_gateway("us-central1", "nonexistent-gateway")


class TestCreateVPNGateway:
    """Tests for creating a VPN gateway."""

    def test_create_vpn_gateway(self, service, sample_vpn_gateway_response):
        """Test creating a VPN gateway."""
        mock_request = mock.MagicMock()
        mock_insert = service.service.vpnGateways.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.return_value = sample_vpn_gateway_response

        gateway = service.create_vpn_gateway(
            region="us-central1",
            gateway_name="my-vpn-gateway",
            network="projects/test-project/global/networks/default",
        )

        mock_insert.assert_called_once_with(
            project="test-project",
            region="us-central1",
            body={
                "name": "my-vpn-gateway",
                "network": "projects/test-project/global/networks/default",
            },
        )
        assert isinstance(gateway, VPNGateway)
        assert gateway.name == "my-vpn-gateway"

    def test_create_vpn_gateway_already_exists(self, service):
        """Test creating a gateway that already exists."""
        mock_request = mock.MagicMock()
        mock_insert = service.service.vpnGateways.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_vpn_gateway(
                region="us-central1",
                gateway_name="my-vpn-gateway",
                network="projects/test-project/global/networks/default",
            )

    def test_create_vpn_gateway_api_error(self, service):
        """Test creating a gateway with an API error."""
        mock_request = mock.MagicMock()
        mock_insert = service.service.vpnGateways.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_vpn_gateway(
                region="us-central1",
                gateway_name="my-vpn-gateway",
                network="projects/test-project/global/networks/default",
            )


class TestDeleteVPNGateway:
    """Tests for deleting a VPN gateway."""

    def test_delete_vpn_gateway(self, service):
        """Test deleting a VPN gateway."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.vpnGateways.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_vpn_gateway("us-central1", "my-vpn-gateway")

        mock_delete.assert_called_once_with(
            project="test-project",
            region="us-central1",
            vpnGateway="my-vpn-gateway",
        )
        assert result is True

    def test_delete_vpn_gateway_not_found(self, service):
        """Test deleting a gateway that does not exist."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.vpnGateways.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_vpn_gateway("us-central1", "nonexistent-gateway")


class TestListVPNTunnels:
    """Tests for listing VPN tunnels."""

    def test_list_vpn_tunnels(self, service, sample_vpn_tunnel_response):
        """Test listing VPN tunnels."""
        mock_request = mock.MagicMock()
        mock_list = service.service.vpnTunnels.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "items": [sample_vpn_tunnel_response]
        }

        mock_list_next = service.service.vpnTunnels.return_value.list_next
        mock_list_next.return_value = None

        tunnels = service.list_vpn_tunnels("us-central1")

        mock_list.assert_called_once_with(
            project="test-project", region="us-central1"
        )
        assert len(tunnels) == 1
        assert isinstance(tunnels[0], VPNTunnel)
        assert tunnels[0].name == "my-vpn-tunnel"
        assert tunnels[0].status == "ESTABLISHED"

    def test_list_vpn_tunnels_empty(self, service):
        """Test listing tunnels when none exist."""
        mock_request = mock.MagicMock()
        mock_list = service.service.vpnTunnels.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}

        mock_list_next = service.service.vpnTunnels.return_value.list_next
        mock_list_next.return_value = None

        tunnels = service.list_vpn_tunnels("us-central1")

        assert len(tunnels) == 0


class TestGetVPNTunnel:
    """Tests for getting a VPN tunnel."""

    def test_get_vpn_tunnel(self, service, sample_vpn_tunnel_response):
        """Test getting a specific VPN tunnel."""
        mock_request = mock.MagicMock()
        mock_get = service.service.vpnTunnels.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_vpn_tunnel_response

        tunnel = service.get_vpn_tunnel("us-central1", "my-vpn-tunnel")

        mock_get.assert_called_once_with(
            project="test-project",
            region="us-central1",
            vpnTunnel="my-vpn-tunnel",
        )
        assert isinstance(tunnel, VPNTunnel)
        assert tunnel.name == "my-vpn-tunnel"
        assert tunnel.peer_ip == "203.0.113.1"
        assert tunnel.ike_version == 2

    def test_get_vpn_tunnel_not_found(self, service):
        """Test getting a tunnel that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = service.service.vpnTunnels.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_vpn_tunnel("us-central1", "nonexistent-tunnel")


class TestCreateVPNTunnel:
    """Tests for creating a VPN tunnel."""

    def test_create_vpn_tunnel(self, service, sample_vpn_tunnel_response):
        """Test creating a VPN tunnel."""
        mock_request = mock.MagicMock()
        mock_insert = service.service.vpnTunnels.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.return_value = sample_vpn_tunnel_response

        tunnel = service.create_vpn_tunnel(
            region="us-central1",
            tunnel_name="my-vpn-tunnel",
            vpn_gateway="projects/test-project/regions/us-central1/vpnGateways/my-vpn-gateway",
            peer_ip="203.0.113.1",
            shared_secret="my-secret",
        )

        mock_insert.assert_called_once_with(
            project="test-project",
            region="us-central1",
            body={
                "name": "my-vpn-tunnel",
                "vpnGateway": "projects/test-project/regions/us-central1/vpnGateways/my-vpn-gateway",
                "peerIp": "203.0.113.1",
                "sharedSecret": "my-secret",
                "ikeVersion": 2,
            },
        )
        assert isinstance(tunnel, VPNTunnel)
        assert tunnel.name == "my-vpn-tunnel"

    def test_create_vpn_tunnel_ike_v1(self, service, sample_vpn_tunnel_response):
        """Test creating a VPN tunnel with IKE v1."""
        mock_request = mock.MagicMock()
        mock_insert = service.service.vpnTunnels.return_value.insert
        mock_insert.return_value = mock_request
        ike_v1_response = dict(sample_vpn_tunnel_response)
        ike_v1_response["ikeVersion"] = 1
        mock_request.execute.return_value = ike_v1_response

        tunnel = service.create_vpn_tunnel(
            region="us-central1",
            tunnel_name="my-vpn-tunnel",
            vpn_gateway="projects/test-project/regions/us-central1/vpnGateways/my-vpn-gateway",
            peer_ip="203.0.113.1",
            shared_secret="my-secret",
            ike_version=1,
        )

        assert tunnel.ike_version == 1

    def test_create_vpn_tunnel_already_exists(self, service):
        """Test creating a tunnel that already exists."""
        mock_request = mock.MagicMock()
        mock_insert = service.service.vpnTunnels.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_vpn_tunnel(
                region="us-central1",
                tunnel_name="my-vpn-tunnel",
                vpn_gateway="projects/test-project/regions/us-central1/vpnGateways/gw",
                peer_ip="203.0.113.1",
                shared_secret="my-secret",
            )

    def test_create_vpn_tunnel_api_error(self, service):
        """Test creating a tunnel with an API error."""
        mock_request = mock.MagicMock()
        mock_insert = service.service.vpnTunnels.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_vpn_tunnel(
                region="us-central1",
                tunnel_name="my-vpn-tunnel",
                vpn_gateway="projects/test-project/regions/us-central1/vpnGateways/gw",
                peer_ip="203.0.113.1",
                shared_secret="my-secret",
            )


class TestDeleteVPNTunnel:
    """Tests for deleting a VPN tunnel."""

    def test_delete_vpn_tunnel(self, service):
        """Test deleting a VPN tunnel."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.vpnTunnels.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_vpn_tunnel("us-central1", "my-vpn-tunnel")

        mock_delete.assert_called_once_with(
            project="test-project",
            region="us-central1",
            vpnTunnel="my-vpn-tunnel",
        )
        assert result is True

    def test_delete_vpn_tunnel_not_found(self, service):
        """Test deleting a tunnel that does not exist."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.vpnTunnels.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_vpn_tunnel("us-central1", "nonexistent-tunnel")


class TestVPNGatewayModel:
    """Tests for the VPNGateway model."""

    def test_from_api_response(self, sample_vpn_gateway_response):
        """Test creating a VPNGateway from an API response."""
        gateway = VPNGateway.from_api_response(sample_vpn_gateway_response)

        assert gateway.id == "123456789"
        assert gateway.name == "my-vpn-gateway"
        assert gateway.region == "us-central1"
        assert gateway.network == "projects/test-project/global/networks/default"
        assert gateway.type == "compute.vpnGateway"
        assert gateway.project == "test-project"
        assert len(gateway.vpn_interfaces) == 2
        assert gateway.labels == {"env": "test"}

    def test_get_tag(self, sample_vpn_gateway_response):
        """Test the get_tag method."""
        gateway = VPNGateway.from_api_response(sample_vpn_gateway_response)

        assert gateway.get_tag("env") == "test"
        assert gateway.get_tag("missing") == ""
        assert gateway.get_tag("missing", "default") == "default"

    def test_from_api_response_minimal(self):
        """Test creating a VPNGateway from a minimal API response."""
        gateway = VPNGateway.from_api_response({"name": "simple-gw"})

        assert gateway.name == "simple-gw"
        assert gateway.region == ""
        assert gateway.network == ""
        assert gateway.vpn_interfaces is None


class TestVPNTunnelModel:
    """Tests for the VPNTunnel model."""

    def test_from_api_response(self, sample_vpn_tunnel_response):
        """Test creating a VPNTunnel from an API response."""
        tunnel = VPNTunnel.from_api_response(sample_vpn_tunnel_response)

        assert tunnel.id == "987654321"
        assert tunnel.name == "my-vpn-tunnel"
        assert tunnel.region == "us-central1"
        assert tunnel.peer_ip == "203.0.113.1"
        assert tunnel.shared_secret == "my-secret"
        assert tunnel.ike_version == 2
        assert tunnel.status == "ESTABLISHED"
        assert tunnel.detailed_status == "Tunnel is up and running."
        assert tunnel.local_traffic_selector == ["10.0.0.0/24"]
        assert tunnel.remote_traffic_selector == ["192.168.0.0/24"]
        assert tunnel.type == "compute.vpnTunnel"

    def test_from_api_response_minimal(self):
        """Test creating a VPNTunnel from a minimal API response."""
        tunnel = VPNTunnel.from_api_response({"name": "simple-tunnel"})

        assert tunnel.name == "simple-tunnel"
        assert tunnel.peer_ip == ""
        assert tunnel.ike_version == 2
        assert tunnel.status == ""
        assert tunnel.shared_secret is None
