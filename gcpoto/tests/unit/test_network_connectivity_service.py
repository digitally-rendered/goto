"""Tests for Network Connectivity Center service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.network_connectivity import NetworkConnectivityService
from gcpoto.models.network_connectivity import Hub, Spoke
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
        yield mock_service


@pytest.fixture
def sample_hub_response():
    """Sample Hub API response."""
    return {
        "name": "projects/test-project/locations/global/hubs/my-hub",
        "description": "Test hub",
        "routingVpcs": [
            {"uri": "projects/test-project/global/networks/my-network"}
        ],
        "state": "ACTIVE",
        "labels": {"env": "test"},
        "createTime": "2024-01-15T10:30:00.000Z",
        "updateTime": "2024-01-16T12:00:00.000Z",
    }


@pytest.fixture
def sample_spoke_response():
    """Sample Spoke API response."""
    return {
        "name": "projects/test-project/locations/us-central1/spokes/my-spoke",
        "hub": "projects/test-project/locations/global/hubs/my-hub",
        "description": "Test spoke",
        "linkedVpnTunnels": {
            "uris": [
                "projects/test-project/regions/us-central1/vpnTunnels/tunnel-1"
            ],
            "siteToSiteDataTransfer": False,
        },
        "state": "ACTIVE",
        "labels": {"team": "networking"},
        "createTime": "2024-01-15T10:30:00.000Z",
        "updateTime": "2024-01-16T12:00:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a NetworkConnectivityService instance with mocked API client."""
    svc = NetworkConnectivityService(project_id="test-project")
    return svc


class TestNetworkConnectivityServiceInit:
    """Tests for NetworkConnectivityService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the NetworkConnectivityService."""
        from googleapiclient.discovery import build

        service = NetworkConnectivityService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "networkconnectivity"
        assert service.version == "v1"
        build.assert_called_once_with(
            "networkconnectivity", "v1", credentials=None
        )


class TestListHubs:
    """Tests for listing hubs."""

    def test_list_hubs(self, service, sample_hub_response):
        """Test listing hubs."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "hubs": [sample_hub_response]
        }

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.list_next
        )
        mock_list_next.return_value = None

        hubs = service.list_hubs()

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(hubs) == 1
        assert isinstance(hubs[0], Hub)
        assert hubs[0].state == "ACTIVE"

    def test_list_hubs_empty(self, service):
        """Test listing hubs when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"hubs": []}

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.list_next
        )
        mock_list_next.return_value = None

        hubs = service.list_hubs()

        assert len(hubs) == 0


class TestGetHub:
    """Tests for getting a hub."""

    def test_get_hub(self, service, sample_hub_response):
        """Test getting a specific hub."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_hub_response

        hub = service.get_hub("my-hub")

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/global/hubs/my-hub"
        )
        assert isinstance(hub, Hub)
        assert hub.description == "Test hub"

    def test_get_hub_not_found(self, service):
        """Test getting a hub that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_hub("missing-hub")


class TestCreateHub:
    """Tests for creating a hub."""

    def test_create_hub(self, service, sample_hub_response):
        """Test creating a hub."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_hub_response

        hub = service.create_hub(
            hub_name="my-hub",
            description="Test hub",
            labels={"env": "test"},
        )

        assert isinstance(hub, Hub)
        assert hub.state == "ACTIVE"

    def test_create_hub_minimal(self, service, sample_hub_response):
        """Test creating a hub with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_hub_response

        hub = service.create_hub(hub_name="my-hub")

        assert isinstance(hub, Hub)

    def test_create_hub_api_error(self, service):
        """Test creating a hub with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_hub(hub_name="my-hub")


class TestUpdateHub:
    """Tests for updating a hub."""

    def test_update_hub(self, service, sample_hub_response):
        """Test updating a hub."""
        mock_request = mock.MagicMock()
        updated_response = dict(sample_hub_response)
        updated_response["description"] = "Updated hub"
        mock_patch = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = updated_response

        hub = service.update_hub(
            hub_name="my-hub",
            update_mask="description",
            update_fields={"description": "Updated hub"},
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/locations/global/hubs/my-hub",
            updateMask="description",
            body={"description": "Updated hub"},
        )
        assert isinstance(hub, Hub)

    def test_update_hub_not_found(self, service):
        """Test updating a hub that does not exist."""
        mock_request = mock.MagicMock()
        mock_patch = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_hub(
                hub_name="missing-hub",
                update_mask="description",
                update_fields={"description": "Updated"},
            )


class TestDeleteHub:
    """Tests for deleting a hub."""

    def test_delete_hub(self, service):
        """Test deleting a hub."""
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.delete
        )
        mock_delete.return_value.execute.return_value = {}

        result = service.delete_hub("my-hub")

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/global/hubs/my-hub"
        )
        assert result is True

    def test_delete_hub_not_found(self, service):
        """Test deleting a hub that does not exist."""
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .global_.return_value
            .hubs.return_value.delete
        )
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_hub("missing-hub")


class TestListSpokes:
    """Tests for listing spokes."""

    def test_list_spokes(self, service, sample_spoke_response):
        """Test listing spokes."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "spokes": [sample_spoke_response]
        }

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.list_next
        )
        mock_list_next.return_value = None

        spokes = service.list_spokes("us-central1")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(spokes) == 1
        assert isinstance(spokes[0], Spoke)
        assert spokes[0].state == "ACTIVE"

    def test_list_spokes_empty(self, service):
        """Test listing spokes when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"spokes": []}

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.list_next
        )
        mock_list_next.return_value = None

        spokes = service.list_spokes("us-central1")

        assert len(spokes) == 0


class TestGetSpoke:
    """Tests for getting a spoke."""

    def test_get_spoke(self, service, sample_spoke_response):
        """Test getting a specific spoke."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_spoke_response

        spoke = service.get_spoke("us-central1", "my-spoke")

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/spokes/my-spoke"
        )
        assert isinstance(spoke, Spoke)
        assert spoke.description == "Test spoke"

    def test_get_spoke_not_found(self, service):
        """Test getting a spoke that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_spoke("us-central1", "missing-spoke")


class TestCreateSpoke:
    """Tests for creating a spoke."""

    def test_create_spoke(self, service, sample_spoke_response):
        """Test creating a spoke."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_spoke_response

        spoke = service.create_spoke(
            location="us-central1",
            spoke_name="my-spoke",
            hub="projects/test-project/locations/global/hubs/my-hub",
            linked_vpn_tunnels={
                "uris": [
                    "projects/test-project/regions/us-central1/vpnTunnels/tunnel-1"
                ],
                "siteToSiteDataTransfer": False,
            },
        )

        assert isinstance(spoke, Spoke)
        assert spoke.state == "ACTIVE"

    def test_create_spoke_api_error(self, service):
        """Test creating a spoke with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_spoke(
                location="us-central1",
                spoke_name="my-spoke",
                hub="projects/test-project/locations/global/hubs/my-hub",
            )


class TestUpdateSpoke:
    """Tests for updating a spoke."""

    def test_update_spoke(self, service, sample_spoke_response):
        """Test updating a spoke."""
        mock_request = mock.MagicMock()
        updated_response = dict(sample_spoke_response)
        updated_response["description"] = "Updated spoke"
        mock_patch = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = updated_response

        spoke = service.update_spoke(
            location="us-central1",
            spoke_name="my-spoke",
            update_mask="description",
            update_fields={"description": "Updated spoke"},
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/spokes/my-spoke",
            updateMask="description",
            body={"description": "Updated spoke"},
        )
        assert isinstance(spoke, Spoke)

    def test_update_spoke_not_found(self, service):
        """Test updating a spoke that does not exist."""
        mock_request = mock.MagicMock()
        mock_patch = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_spoke(
                location="us-central1",
                spoke_name="missing-spoke",
                update_mask="description",
                update_fields={"description": "Updated"},
            )


class TestDeleteSpoke:
    """Tests for deleting a spoke."""

    def test_delete_spoke(self, service):
        """Test deleting a spoke."""
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.delete
        )
        mock_delete.return_value.execute.return_value = {}

        result = service.delete_spoke("us-central1", "my-spoke")

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/spokes/my-spoke"
        )
        assert result is True

    def test_delete_spoke_not_found(self, service):
        """Test deleting a spoke that does not exist."""
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .spokes.return_value.delete
        )
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_spoke("us-central1", "missing-spoke")


class TestHubModel:
    """Tests for the Hub model."""

    def test_from_api_response(self, sample_hub_response):
        """Test creating a Hub from an API response."""
        hub = Hub.from_api_response(sample_hub_response)

        assert hub.name == "projects/test-project/locations/global/hubs/my-hub"
        assert hub.description == "Test hub"
        assert hub.state == "ACTIVE"
        assert hub.routing_vpcs is not None
        assert len(hub.routing_vpcs) == 1
        assert hub.type == "networkconnectivity.hub"

    def test_from_api_response_minimal(self):
        """Test creating a Hub from a minimal API response."""
        hub = Hub.from_api_response(
            {"name": "projects/test/locations/global/hubs/h1"}
        )

        assert hub.state == ""
        assert hub.routing_vpcs is None
        assert hub.description is None

    def test_get_tag(self, sample_hub_response):
        """Test get_tag method."""
        hub = Hub.from_api_response(sample_hub_response)

        assert hub.get_tag("env") == "test"
        assert hub.get_tag("missing", "default") == "default"


class TestSpokeModel:
    """Tests for the Spoke model."""

    def test_from_api_response(self, sample_spoke_response):
        """Test creating a Spoke from an API response."""
        spoke = Spoke.from_api_response(sample_spoke_response)

        assert spoke.name == "projects/test-project/locations/us-central1/spokes/my-spoke"
        assert spoke.hub_name == "projects/test-project/locations/global/hubs/my-hub"
        assert spoke.description == "Test spoke"
        assert spoke.state == "ACTIVE"
        assert spoke.linked_vpn_tunnels is not None
        assert spoke.location == "us-central1"
        assert spoke.type == "networkconnectivity.spoke"

    def test_from_api_response_minimal(self):
        """Test creating a Spoke from a minimal API response."""
        spoke = Spoke.from_api_response(
            {"name": "projects/test/locations/us-east1/spokes/s1"}
        )

        assert spoke.hub_name == ""
        assert spoke.state == ""
        assert spoke.linked_vpn_tunnels is None

    def test_get_tag(self, sample_spoke_response):
        """Test get_tag method."""
        spoke = Spoke.from_api_response(sample_spoke_response)

        assert spoke.get_tag("team") == "networking"
        assert spoke.get_tag("missing", "default") == "default"
