"""Tests for the Interconnect service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.interconnect import InterconnectService
from gcpoto.models.interconnect import Interconnect, InterconnectAttachment
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
def sample_interconnect_response():
    """Sample Interconnect response."""
    return {
        "id": "123456789",
        "name": "my-interconnect",
        "location": "las-vegas-zone1-2",
        "interconnectType": "IT_PRIVATE",
        "linkType": "LINK_TYPE_ETHERNET_10G_LR",
        "requestedLinkCount": 1,
        "state": "ACTIVE",
        "operationalStatus": "OS_ACTIVE",
        "peerIpAddress": "169.254.0.1",
        "googleIpAddress": "169.254.0.2",
        "project": "test-project",
        "labels": {"env": "production"},
        "creationTimestamp": "2024-06-01T10:00:00.000Z",
    }


@pytest.fixture
def sample_attachment_response():
    """Sample Interconnect Attachment response."""
    return {
        "id": "987654321",
        "name": "my-attachment",
        "region": "us-central1",
        "interconnect": "projects/test-project/global/interconnects/my-interconnect",
        "router": "projects/test-project/regions/us-central1/routers/my-router",
        "type": "DEDICATED",
        "state": "ACTIVE",
        "bandwidth": "BPS_1G",
        "vlanTag8021q": 1000,
        "pairingKey": None,
        "project": "test-project",
        "labels": {"env": "test"},
        "creationTimestamp": "2024-06-01T10:00:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create an InterconnectService instance with mocked API client."""
    return InterconnectService(project_id="test-project")


# ------------------------------------------------------------------ #
#  Service init
# ------------------------------------------------------------------ #


class TestInterconnectServiceInit:
    """Tests for InterconnectService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the Interconnect service."""
        from googleapiclient.discovery import build

        svc = InterconnectService(project_id="test-project")

        assert svc.project_id == "test-project"
        assert svc.service_name == "compute"
        assert svc.version == "v1"
        build.assert_called_once_with("compute", "v1", credentials=None)

    def test_init_with_credentials(self, mock_google_client):
        """Test initializing with credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = InterconnectService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert svc.project_id == "test-project"
            mock_creds.assert_called_once()


# ------------------------------------------------------------------ #
#  Interconnect operations
# ------------------------------------------------------------------ #


class TestListInterconnects:
    """Tests for listing interconnects."""

    def test_list_interconnects(
        self, service, sample_interconnect_response
    ):
        """Test listing interconnects."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.list.return_value = mock_request
        mock_request.execute.return_value = {
            "items": [sample_interconnect_response]
        }
        mock_interconnects.list_next.return_value = None

        interconnects = service.list_interconnects()

        mock_interconnects.list.assert_called_once_with(
            project="test-project"
        )
        assert len(interconnects) == 1
        assert isinstance(interconnects[0], Interconnect)
        assert interconnects[0].name == "my-interconnect"
        assert interconnects[0].interconnect_type == "IT_PRIVATE"
        assert interconnects[0].state == "ACTIVE"

    def test_list_interconnects_empty(self, service):
        """Test listing interconnects when none exist."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}
        mock_interconnects.list_next.return_value = None

        interconnects = service.list_interconnects()
        assert len(interconnects) == 0

    def test_list_interconnects_pagination(
        self, service, sample_interconnect_response
    ):
        """Test listing interconnects with pagination."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_interconnects.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "items": [sample_interconnect_response]
        }

        second_ic = dict(sample_interconnect_response)
        second_ic["name"] = "my-interconnect-2"
        second_ic["id"] = "987654321"
        mock_request_page2.execute.return_value = {
            "items": [second_ic]
        }

        mock_interconnects.list_next.side_effect = [
            mock_request_page2,
            None,
        ]

        interconnects = service.list_interconnects()
        assert len(interconnects) == 2


class TestGetInterconnect:
    """Tests for getting an interconnect."""

    def test_get_interconnect(
        self, service, sample_interconnect_response
    ):
        """Test getting a specific interconnect."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.get.return_value = mock_request
        mock_request.execute.return_value = (
            sample_interconnect_response
        )

        interconnect = service.get_interconnect("my-interconnect")

        mock_interconnects.get.assert_called_once_with(
            project="test-project",
            interconnect="my-interconnect",
        )
        assert isinstance(interconnect, Interconnect)
        assert interconnect.name == "my-interconnect"
        assert interconnect.peer_ip_address == "169.254.0.1"
        assert interconnect.google_ip_address == "169.254.0.2"

    def test_get_interconnect_not_found(self, service):
        """Test getting an interconnect that does not exist."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_interconnect("nonexistent")

    def test_get_interconnect_api_error(self, service):
        """Test getting an interconnect with an API error."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_interconnect("my-interconnect")


class TestCreateInterconnect:
    """Tests for creating an interconnect."""

    def test_create_interconnect(
        self, service, sample_interconnect_response
    ):
        """Test creating an interconnect."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.insert.return_value = mock_request
        mock_request.execute.return_value = (
            sample_interconnect_response
        )

        interconnect = service.create_interconnect(
            interconnect_name="my-interconnect",
            interconnect_type="IT_PRIVATE",
            link_type="LINK_TYPE_ETHERNET_10G_LR",
            requested_link_count=1,
            location="las-vegas-zone1-2",
        )

        mock_interconnects.insert.assert_called_once_with(
            project="test-project",
            body={
                "name": "my-interconnect",
                "interconnectType": "IT_PRIVATE",
                "linkType": "LINK_TYPE_ETHERNET_10G_LR",
                "requestedLinkCount": 1,
                "location": "las-vegas-zone1-2",
            },
        )
        assert isinstance(interconnect, Interconnect)
        assert interconnect.name == "my-interconnect"

    def test_create_interconnect_already_exists(self, service):
        """Test creating an interconnect that already exists."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_interconnect(
                interconnect_name="my-interconnect",
                interconnect_type="IT_PRIVATE",
                link_type="LINK_TYPE_ETHERNET_10G_LR",
                requested_link_count=1,
                location="las-vegas-zone1-2",
            )

    def test_create_interconnect_api_error(self, service):
        """Test creating an interconnect with an API error."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_interconnect(
                interconnect_name="my-interconnect",
                interconnect_type="IT_PRIVATE",
                link_type="LINK_TYPE_ETHERNET_10G_LR",
                requested_link_count=1,
                location="las-vegas-zone1-2",
            )


class TestDeleteInterconnect:
    """Tests for deleting an interconnect."""

    def test_delete_interconnect(self, service):
        """Test deleting an interconnect."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_interconnect("my-interconnect")

        mock_interconnects.delete.assert_called_once_with(
            project="test-project",
            interconnect="my-interconnect",
        )
        assert result is True

    def test_delete_interconnect_not_found(self, service):
        """Test deleting an interconnect that does not exist."""
        mock_interconnects = (
            service.service.interconnects.return_value
        )
        mock_request = mock.MagicMock()
        mock_interconnects.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_interconnect("nonexistent")


# ------------------------------------------------------------------ #
#  Attachment operations
# ------------------------------------------------------------------ #


class TestListAttachments:
    """Tests for listing attachments."""

    def test_list_attachments(
        self, service, sample_attachment_response
    ):
        """Test listing interconnect attachments."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.list.return_value = mock_request
        mock_request.execute.return_value = {
            "items": [sample_attachment_response]
        }
        mock_attachments.list_next.return_value = None

        attachments = service.list_attachments("us-central1")

        mock_attachments.list.assert_called_once_with(
            project="test-project", region="us-central1"
        )
        assert len(attachments) == 1
        assert isinstance(attachments[0], InterconnectAttachment)
        assert attachments[0].name == "my-attachment"
        assert attachments[0].type_field == "DEDICATED"
        assert attachments[0].vlan_tag8021q == 1000

    def test_list_attachments_empty(self, service):
        """Test listing attachments when none exist."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}
        mock_attachments.list_next.return_value = None

        attachments = service.list_attachments("us-central1")
        assert len(attachments) == 0


class TestGetAttachment:
    """Tests for getting an attachment."""

    def test_get_attachment(
        self, service, sample_attachment_response
    ):
        """Test getting a specific attachment."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.get.return_value = mock_request
        mock_request.execute.return_value = sample_attachment_response

        attachment = service.get_attachment(
            "us-central1", "my-attachment"
        )

        mock_attachments.get.assert_called_once_with(
            project="test-project",
            region="us-central1",
            interconnectAttachment="my-attachment",
        )
        assert isinstance(attachment, InterconnectAttachment)
        assert attachment.name == "my-attachment"
        assert attachment.bandwidth == "BPS_1G"

    def test_get_attachment_not_found(self, service):
        """Test getting an attachment that does not exist."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_attachment("us-central1", "nonexistent")

    def test_get_attachment_api_error(self, service):
        """Test getting an attachment with an API error."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_attachment("us-central1", "my-attachment")


class TestCreateAttachment:
    """Tests for creating an attachment."""

    def test_create_attachment_dedicated(
        self, service, sample_attachment_response
    ):
        """Test creating a dedicated interconnect attachment."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.insert.return_value = mock_request
        mock_request.execute.return_value = sample_attachment_response

        attachment = service.create_attachment(
            region="us-central1",
            attachment_name="my-attachment",
            router="projects/test-project/regions/us-central1/routers/my-router",
            type_field="DEDICATED",
            interconnect="projects/test-project/global/interconnects/my-interconnect",
            bandwidth="BPS_1G",
        )

        mock_attachments.insert.assert_called_once_with(
            project="test-project",
            region="us-central1",
            body={
                "name": "my-attachment",
                "router": "projects/test-project/regions/us-central1/routers/my-router",
                "type": "DEDICATED",
                "interconnect": "projects/test-project/global/interconnects/my-interconnect",
                "bandwidth": "BPS_1G",
            },
        )
        assert isinstance(attachment, InterconnectAttachment)
        assert attachment.name == "my-attachment"

    def test_create_attachment_partner(
        self, service, sample_attachment_response
    ):
        """Test creating a partner interconnect attachment."""
        partner_response = dict(sample_attachment_response)
        partner_response["type"] = "PARTNER"
        partner_response["pairingKey"] = "abc123/us-central1/1"

        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.insert.return_value = mock_request
        mock_request.execute.return_value = partner_response

        attachment = service.create_attachment(
            region="us-central1",
            attachment_name="my-partner-attachment",
            router="projects/test-project/regions/us-central1/routers/my-router",
            type_field="PARTNER",
        )

        mock_attachments.insert.assert_called_once_with(
            project="test-project",
            region="us-central1",
            body={
                "name": "my-partner-attachment",
                "router": "projects/test-project/regions/us-central1/routers/my-router",
                "type": "PARTNER",
            },
        )
        assert isinstance(attachment, InterconnectAttachment)

    def test_create_attachment_already_exists(self, service):
        """Test creating an attachment that already exists."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_attachment(
                region="us-central1",
                attachment_name="my-attachment",
                router="my-router",
                type_field="DEDICATED",
            )

    def test_create_attachment_api_error(self, service):
        """Test creating an attachment with an API error."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_attachment(
                region="us-central1",
                attachment_name="my-attachment",
                router="my-router",
                type_field="DEDICATED",
            )


class TestDeleteAttachment:
    """Tests for deleting an attachment."""

    def test_delete_attachment(self, service):
        """Test deleting an attachment."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_attachment("us-central1", "my-attachment")

        mock_attachments.delete.assert_called_once_with(
            project="test-project",
            region="us-central1",
            interconnectAttachment="my-attachment",
        )
        assert result is True

    def test_delete_attachment_not_found(self, service):
        """Test deleting an attachment that does not exist."""
        mock_attachments = (
            service.service.interconnectAttachments.return_value
        )
        mock_request = mock.MagicMock()
        mock_attachments.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_attachment("us-central1", "nonexistent")


# ------------------------------------------------------------------ #
#  Location operations
# ------------------------------------------------------------------ #


class TestListLocations:
    """Tests for listing interconnect locations."""

    def test_list_locations(self, service):
        """Test listing interconnect locations."""
        mock_locations = (
            service.service.interconnectLocations.return_value
        )
        mock_request = mock.MagicMock()
        mock_locations.list.return_value = mock_request
        mock_request.execute.return_value = {
            "items": [
                {
                    "name": "las-vegas-zone1-2",
                    "description": "Las Vegas Zone 1",
                    "facilityProvider": "Equinix",
                },
                {
                    "name": "chicago-zone1-2",
                    "description": "Chicago Zone 1",
                    "facilityProvider": "CoreSite",
                },
            ]
        }
        mock_locations.list_next.return_value = None

        locations = service.list_locations()

        mock_locations.list.assert_called_once_with(
            project="test-project"
        )
        assert len(locations) == 2
        assert locations[0]["name"] == "las-vegas-zone1-2"
        assert locations[1]["name"] == "chicago-zone1-2"

    def test_list_locations_empty(self, service):
        """Test listing locations when none are returned."""
        mock_locations = (
            service.service.interconnectLocations.return_value
        )
        mock_request = mock.MagicMock()
        mock_locations.list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}
        mock_locations.list_next.return_value = None

        locations = service.list_locations()
        assert len(locations) == 0


# ------------------------------------------------------------------ #
#  Model tests
# ------------------------------------------------------------------ #


class TestInterconnectModel:
    """Tests for the Interconnect model."""

    def test_from_api_response(self, sample_interconnect_response):
        """Test creating an Interconnect from an API response."""
        interconnect = Interconnect.from_api_response(
            sample_interconnect_response
        )

        assert interconnect.id == "123456789"
        assert interconnect.name == "my-interconnect"
        assert interconnect.type == "compute.interconnect"
        assert interconnect.location == "las-vegas-zone1-2"
        assert interconnect.interconnect_type == "IT_PRIVATE"
        assert interconnect.link_type == "LINK_TYPE_ETHERNET_10G_LR"
        assert interconnect.requested_link_count == 1
        assert interconnect.state == "ACTIVE"
        assert interconnect.operational_status == "OS_ACTIVE"
        assert interconnect.peer_ip_address == "169.254.0.1"
        assert interconnect.google_ip_address == "169.254.0.2"
        assert interconnect.labels == {"env": "production"}

    def test_from_api_response_minimal(self):
        """Test creating an Interconnect from a minimal response."""
        interconnect = Interconnect.from_api_response(
            {"name": "simple-ic"}
        )

        assert interconnect.id == "simple-ic"
        assert interconnect.name == "simple-ic"
        assert interconnect.interconnect_type == ""
        assert interconnect.state == ""
        assert interconnect.operational_status is None
        assert interconnect.peer_ip_address is None

    def test_get_tag(self, sample_interconnect_response):
        """Test the get_tag method."""
        interconnect = Interconnect.from_api_response(
            sample_interconnect_response
        )

        assert interconnect.get_tag("env") == "production"
        assert interconnect.get_tag("missing") == ""
        assert interconnect.get_tag("missing", "default") == "default"


class TestInterconnectAttachmentModel:
    """Tests for the InterconnectAttachment model."""

    def test_from_api_response(self, sample_attachment_response):
        """Test creating an InterconnectAttachment from an API response."""
        attachment = InterconnectAttachment.from_api_response(
            sample_attachment_response
        )

        assert attachment.id == "987654321"
        assert attachment.name == "my-attachment"
        assert attachment.type == "compute.interconnectAttachment"
        assert attachment.region == "us-central1"
        assert attachment.router == "projects/test-project/regions/us-central1/routers/my-router"
        assert attachment.type_field == "DEDICATED"
        assert attachment.state == "ACTIVE"
        assert attachment.bandwidth == "BPS_1G"
        assert attachment.vlan_tag8021q == 1000
        assert attachment.pairing_key is None
        assert attachment.labels == {"env": "test"}

    def test_from_api_response_minimal(self):
        """Test creating an InterconnectAttachment from a minimal response."""
        attachment = InterconnectAttachment.from_api_response(
            {"name": "simple-att"}
        )

        assert attachment.id == "simple-att"
        assert attachment.name == "simple-att"
        assert attachment.type_field == ""
        assert attachment.state == ""
        assert attachment.bandwidth is None
        assert attachment.vlan_tag8021q is None
        assert attachment.pairing_key is None

    def test_get_tag(self, sample_attachment_response):
        """Test the get_tag method."""
        attachment = InterconnectAttachment.from_api_response(
            sample_attachment_response
        )

        assert attachment.get_tag("env") == "test"
        assert attachment.get_tag("missing") == ""
        assert attachment.get_tag("missing", "default") == "default"
