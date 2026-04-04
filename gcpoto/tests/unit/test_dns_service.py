"""Tests for Cloud DNS service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.dns import DNSService
from gcpoto.models.dns import ManagedZone, ResourceRecordSet
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

        mock_managed_zones = mock.MagicMock()
        mock_service.managedZones.return_value = mock_managed_zones

        mock_record_sets = mock.MagicMock()
        mock_service.resourceRecordSets.return_value = mock_record_sets

        yield mock_service


@pytest.fixture
def sample_zone_response():
    """Sample Cloud DNS managed zone API response."""
    return {
        "id": "123456789",
        "name": "example-zone",
        "dnsName": "example.com.",
        "description": "Example DNS zone",
        "visibility": "public",
        "nameServers": [
            "ns-cloud-a1.googledomains.com.",
            "ns-cloud-a2.googledomains.com.",
            "ns-cloud-a3.googledomains.com.",
            "ns-cloud-a4.googledomains.com.",
        ],
        "labels": {"env": "test", "team": "platform"},
        "project": "test-project",
        "creationTime": "2024-01-15T10:30:00.000Z",
    }


@pytest.fixture
def sample_record_set_response():
    """Sample Cloud DNS resource record set API response."""
    return {
        "name": "www.example.com.",
        "type": "A",
        "ttl": 300,
        "rrdatas": ["1.2.3.4", "5.6.7.8"],
    }


@pytest.fixture
def service(mock_google_client):
    """Create a DNSService instance with mocked API client."""
    svc = DNSService(project_id="test-project")
    return svc


class TestDNSServiceInit:
    """Tests for DNSService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the DNSService."""
        from googleapiclient.discovery import build

        service = DNSService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "dns"
        assert service.version == "v1"
        build.assert_called_once_with("dns", "v1", credentials=None)

    def test_init_with_credentials(self, mock_google_client):
        """Test initializing the DNSService with credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            service = DNSService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert service.project_id == "test-project"
            mock_creds.assert_called_once()


class TestListZones:
    """Tests for listing managed zones."""

    def test_list_zones(self, service, sample_zone_response):
        """Test listing DNS managed zones."""
        mock_request = mock.MagicMock()
        mock_list = service.service.managedZones.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "managedZones": [sample_zone_response]
        }

        mock_list_next = service.service.managedZones.return_value.list_next
        mock_list_next.return_value = None

        zones = service.list_zones()

        mock_list.assert_called_once_with(project="test-project")
        assert len(zones) == 1
        assert isinstance(zones[0], ManagedZone)
        assert zones[0].name == "example-zone"
        assert zones[0].dns_name == "example.com."
        assert zones[0].visibility == "public"
        assert len(zones[0].name_servers) == 4

    def test_list_zones_empty(self, service):
        """Test listing zones when no zones exist."""
        mock_request = mock.MagicMock()
        mock_list = service.service.managedZones.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"managedZones": []}

        mock_list_next = service.service.managedZones.return_value.list_next
        mock_list_next.return_value = None

        zones = service.list_zones()

        assert len(zones) == 0

    def test_list_zones_pagination(self, service, sample_zone_response):
        """Test listing zones with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = service.service.managedZones.return_value.list
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "managedZones": [sample_zone_response]
        }

        second_zone = dict(sample_zone_response)
        second_zone["name"] = "example-zone-2"
        second_zone["dnsName"] = "example2.com."
        mock_request_page2.execute.return_value = {
            "managedZones": [second_zone]
        }

        mock_list_next = service.service.managedZones.return_value.list_next
        mock_list_next.side_effect = [mock_request_page2, None]

        zones = service.list_zones()

        assert len(zones) == 2
        assert zones[0].name == "example-zone"
        assert zones[1].name == "example-zone-2"


class TestGetZone:
    """Tests for getting a managed zone."""

    def test_get_zone(self, service, sample_zone_response):
        """Test getting a specific DNS managed zone."""
        mock_request = mock.MagicMock()
        mock_get = service.service.managedZones.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_zone_response

        zone = service.get_zone("example-zone")

        mock_get.assert_called_once_with(
            project="test-project", managedZone="example-zone"
        )
        assert isinstance(zone, ManagedZone)
        assert zone.name == "example-zone"
        assert zone.dns_name == "example.com."
        assert zone.description == "Example DNS zone"

    def test_get_zone_not_found(self, service):
        """Test getting a zone that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = service.service.managedZones.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_zone("nonexistent-zone")

    def test_get_zone_api_error(self, service):
        """Test getting a zone with an API error."""
        mock_request = mock.MagicMock()
        mock_get = service.service.managedZones.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_zone("example-zone")


class TestCreateZone:
    """Tests for creating a managed zone."""

    def test_create_zone(self, service, sample_zone_response):
        """Test creating a DNS managed zone."""
        mock_request = mock.MagicMock()
        mock_create = service.service.managedZones.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_zone_response

        zone = service.create_zone(
            zone_name="example-zone",
            dns_name="example.com.",
            description="Example DNS zone",
            visibility="public",
            labels={"env": "test", "team": "platform"},
        )

        mock_create.assert_called_once_with(
            project="test-project",
            body={
                "name": "example-zone",
                "dnsName": "example.com.",
                "description": "Example DNS zone",
                "visibility": "public",
                "labels": {"env": "test", "team": "platform"},
            },
        )
        assert isinstance(zone, ManagedZone)
        assert zone.name == "example-zone"
        assert zone.dns_name == "example.com."

    def test_create_zone_minimal(self, service, sample_zone_response):
        """Test creating a zone with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_create = service.service.managedZones.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_zone_response

        zone = service.create_zone(
            zone_name="example-zone",
            dns_name="example.com.",
        )

        mock_create.assert_called_once_with(
            project="test-project",
            body={
                "name": "example-zone",
                "dnsName": "example.com.",
                "description": "",
                "visibility": "public",
            },
        )
        assert isinstance(zone, ManagedZone)

    def test_create_zone_already_exists(self, service):
        """Test creating a zone that already exists."""
        mock_request = mock.MagicMock()
        mock_create = service.service.managedZones.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_zone(
                zone_name="example-zone",
                dns_name="example.com.",
            )

    def test_create_zone_api_error(self, service):
        """Test creating a zone with an API error."""
        mock_request = mock.MagicMock()
        mock_create = service.service.managedZones.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_zone(
                zone_name="example-zone",
                dns_name="example.com.",
            )


class TestDeleteZone:
    """Tests for deleting a managed zone."""

    def test_delete_zone(self, service):
        """Test deleting a DNS managed zone."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.managedZones.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_zone("example-zone")

        mock_delete.assert_called_once_with(
            project="test-project", managedZone="example-zone"
        )
        assert result is True

    def test_delete_zone_not_found(self, service):
        """Test deleting a zone that does not exist."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.managedZones.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_zone("nonexistent-zone")


class TestUpdateZone:
    """Tests for updating a managed zone."""

    def test_update_zone(self, service, sample_zone_response):
        """Test updating a DNS managed zone."""
        mock_request = mock.MagicMock()
        mock_patch = service.service.managedZones.return_value.patch
        mock_patch.return_value = mock_request
        updated_response = dict(sample_zone_response)
        updated_response["description"] = "Updated description"
        mock_request.execute.return_value = updated_response

        zone = service.update_zone(
            zone_name="example-zone",
            description="Updated description",
            labels={"env": "prod"},
        )

        mock_patch.assert_called_once_with(
            project="test-project",
            managedZone="example-zone",
            body={"description": "Updated description", "labels": {"env": "prod"}},
        )
        assert isinstance(zone, ManagedZone)
        assert zone.description == "Updated description"

    def test_update_zone_description_only(self, service, sample_zone_response):
        """Test updating only the description of a zone."""
        mock_request = mock.MagicMock()
        mock_patch = service.service.managedZones.return_value.patch
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_zone_response

        service.update_zone(zone_name="example-zone", description="New desc")

        mock_patch.assert_called_once_with(
            project="test-project",
            managedZone="example-zone",
            body={"description": "New desc"},
        )

    def test_update_zone_not_found(self, service):
        """Test updating a zone that does not exist."""
        mock_request = mock.MagicMock()
        mock_patch = service.service.managedZones.return_value.patch
        mock_patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_zone("nonexistent-zone", description="test")


class TestListRecordSets:
    """Tests for listing resource record sets."""

    def test_list_record_sets(self, service, sample_record_set_response):
        """Test listing record sets in a zone."""
        mock_request = mock.MagicMock()
        mock_list = service.service.resourceRecordSets.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "rrsets": [sample_record_set_response]
        }

        mock_list_next = (
            service.service.resourceRecordSets.return_value.list_next
        )
        mock_list_next.return_value = None

        records = service.list_record_sets("example-zone")

        mock_list.assert_called_once_with(
            project="test-project", managedZone="example-zone"
        )
        assert len(records) == 1
        assert isinstance(records[0], ResourceRecordSet)
        assert records[0].dns_name == "www.example.com."
        assert records[0].record_type == "A"
        assert records[0].ttl == 300
        assert records[0].rrdatas == ["1.2.3.4", "5.6.7.8"]
        assert records[0].zone_name == "example-zone"

    def test_list_record_sets_empty(self, service):
        """Test listing record sets when none exist."""
        mock_request = mock.MagicMock()
        mock_list = service.service.resourceRecordSets.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"rrsets": []}

        mock_list_next = (
            service.service.resourceRecordSets.return_value.list_next
        )
        mock_list_next.return_value = None

        records = service.list_record_sets("example-zone")

        assert len(records) == 0

    def test_list_record_sets_pagination(self, service, sample_record_set_response):
        """Test listing record sets with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = service.service.resourceRecordSets.return_value.list
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "rrsets": [sample_record_set_response]
        }

        second_record = {
            "name": "mail.example.com.",
            "type": "MX",
            "ttl": 3600,
            "rrdatas": ["10 mail.example.com."],
        }
        mock_request_page2.execute.return_value = {
            "rrsets": [second_record]
        }

        mock_list_next = (
            service.service.resourceRecordSets.return_value.list_next
        )
        mock_list_next.side_effect = [mock_request_page2, None]

        records = service.list_record_sets("example-zone")

        assert len(records) == 2
        assert records[0].record_type == "A"
        assert records[1].record_type == "MX"


class TestGetRecordSet:
    """Tests for getting a resource record set."""

    def test_get_record_set(self, service, sample_record_set_response):
        """Test getting a specific record set."""
        mock_request = mock.MagicMock()
        mock_get = service.service.resourceRecordSets.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_record_set_response

        record = service.get_record_set(
            "example-zone", "www.example.com.", "A"
        )

        mock_get.assert_called_once_with(
            project="test-project",
            managedZone="example-zone",
            name="www.example.com.",
            type="A",
        )
        assert isinstance(record, ResourceRecordSet)
        assert record.dns_name == "www.example.com."
        assert record.record_type == "A"
        assert record.ttl == 300
        assert record.rrdatas == ["1.2.3.4", "5.6.7.8"]

    def test_get_record_set_not_found(self, service):
        """Test getting a record set that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = service.service.resourceRecordSets.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_record_set("example-zone", "missing.example.com.", "A")


class TestCreateRecordSet:
    """Tests for creating a resource record set."""

    def test_create_record_set(self, service, sample_record_set_response):
        """Test creating a record set."""
        mock_request = mock.MagicMock()
        mock_create = service.service.resourceRecordSets.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_record_set_response

        record = service.create_record_set(
            zone_name="example-zone",
            name="www.example.com.",
            type="A",
            ttl=300,
            rrdatas=["1.2.3.4", "5.6.7.8"],
        )

        mock_create.assert_called_once_with(
            project="test-project",
            managedZone="example-zone",
            body={
                "name": "www.example.com.",
                "type": "A",
                "ttl": 300,
                "rrdatas": ["1.2.3.4", "5.6.7.8"],
            },
        )
        assert isinstance(record, ResourceRecordSet)
        assert record.dns_name == "www.example.com."
        assert record.record_type == "A"

    def test_create_record_set_cname(self, service):
        """Test creating a CNAME record set."""
        cname_response = {
            "name": "alias.example.com.",
            "type": "CNAME",
            "ttl": 600,
            "rrdatas": ["www.example.com."],
        }
        mock_request = mock.MagicMock()
        mock_create = service.service.resourceRecordSets.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.return_value = cname_response

        record = service.create_record_set(
            zone_name="example-zone",
            name="alias.example.com.",
            type="CNAME",
            ttl=600,
            rrdatas=["www.example.com."],
        )

        assert record.record_type == "CNAME"
        assert record.rrdatas == ["www.example.com."]

    def test_create_record_set_already_exists(self, service):
        """Test creating a record set that already exists."""
        mock_request = mock.MagicMock()
        mock_create = service.service.resourceRecordSets.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_record_set(
                zone_name="example-zone",
                name="www.example.com.",
                type="A",
                ttl=300,
                rrdatas=["1.2.3.4"],
            )

    def test_create_record_set_api_error(self, service):
        """Test creating a record set with an API error."""
        mock_request = mock.MagicMock()
        mock_create = service.service.resourceRecordSets.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_record_set(
                zone_name="example-zone",
                name="www.example.com.",
                type="A",
                ttl=300,
                rrdatas=["1.2.3.4"],
            )


class TestDeleteRecordSet:
    """Tests for deleting a resource record set."""

    def test_delete_record_set(self, service):
        """Test deleting a record set."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.resourceRecordSets.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_record_set(
            "example-zone", "www.example.com.", "A"
        )

        mock_delete.assert_called_once_with(
            project="test-project",
            managedZone="example-zone",
            name="www.example.com.",
            type="A",
        )
        assert result is True

    def test_delete_record_set_not_found(self, service):
        """Test deleting a record set that does not exist."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.resourceRecordSets.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_record_set(
                "example-zone", "missing.example.com.", "A"
            )


class TestUpdateRecordSet:
    """Tests for updating a resource record set."""

    def test_update_record_set(self, service):
        """Test updating a record set."""
        updated_response = {
            "name": "www.example.com.",
            "type": "A",
            "ttl": 600,
            "rrdatas": ["9.8.7.6"],
        }
        mock_request = mock.MagicMock()
        mock_patch = service.service.resourceRecordSets.return_value.patch
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = updated_response

        record = service.update_record_set(
            zone_name="example-zone",
            name="www.example.com.",
            type="A",
            ttl=600,
            rrdatas=["9.8.7.6"],
        )

        mock_patch.assert_called_once_with(
            project="test-project",
            managedZone="example-zone",
            name="www.example.com.",
            type="A",
            body={
                "name": "www.example.com.",
                "type": "A",
                "ttl": 600,
                "rrdatas": ["9.8.7.6"],
            },
        )
        assert isinstance(record, ResourceRecordSet)
        assert record.ttl == 600
        assert record.rrdatas == ["9.8.7.6"]

    def test_update_record_set_ttl_only(self, service, sample_record_set_response):
        """Test updating only the TTL of a record set."""
        mock_request = mock.MagicMock()
        mock_patch = service.service.resourceRecordSets.return_value.patch
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_record_set_response

        service.update_record_set(
            zone_name="example-zone",
            name="www.example.com.",
            type="A",
            ttl=900,
        )

        mock_patch.assert_called_once_with(
            project="test-project",
            managedZone="example-zone",
            name="www.example.com.",
            type="A",
            body={
                "name": "www.example.com.",
                "type": "A",
                "ttl": 900,
            },
        )

    def test_update_record_set_not_found(self, service):
        """Test updating a record set that does not exist."""
        mock_request = mock.MagicMock()
        mock_patch = service.service.resourceRecordSets.return_value.patch
        mock_patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_record_set(
                zone_name="example-zone",
                name="missing.example.com.",
                type="A",
                ttl=300,
            )


class TestManagedZoneModel:
    """Tests for the ManagedZone model."""

    def test_from_api_response(self, sample_zone_response):
        """Test creating a ManagedZone from an API response."""
        zone = ManagedZone.from_api_response(sample_zone_response)

        assert zone.id == "123456789"
        assert zone.name == "example-zone"
        assert zone.dns_name == "example.com."
        assert zone.description == "Example DNS zone"
        assert zone.visibility == "public"
        assert zone.type == "dns.managedZone"
        assert zone.project == "test-project"
        assert len(zone.name_servers) == 4
        assert zone.labels == {"env": "test", "team": "platform"}

    def test_get_tag(self, sample_zone_response):
        """Test the get_tag method."""
        zone = ManagedZone.from_api_response(sample_zone_response)

        assert zone.get_tag("env") == "test"
        assert zone.get_tag("team") == "platform"
        assert zone.get_tag("missing") == ""
        assert zone.get_tag("missing", "default") == "default"

    def test_from_api_response_minimal(self):
        """Test creating a ManagedZone from a minimal API response."""
        zone = ManagedZone.from_api_response({"name": "simple-zone"})

        assert zone.name == "simple-zone"
        assert zone.dns_name == ""
        assert zone.visibility == "public"
        assert zone.name_servers == []


class TestResourceRecordSetModel:
    """Tests for the ResourceRecordSet model."""

    def test_from_api_response(self, sample_record_set_response):
        """Test creating a ResourceRecordSet from an API response."""
        record = ResourceRecordSet.from_api_response(
            sample_record_set_response, "example-zone"
        )

        assert record.dns_name == "www.example.com."
        assert record.record_type == "A"
        assert record.ttl == 300
        assert record.rrdatas == ["1.2.3.4", "5.6.7.8"]
        assert record.zone_name == "example-zone"
        assert record.type == "dns.resourceRecordSet"
        assert record.id == "www.example.com./A"

    def test_from_api_response_mx(self):
        """Test creating an MX record from an API response."""
        response = {
            "name": "example.com.",
            "type": "MX",
            "ttl": 3600,
            "rrdatas": ["10 mail1.example.com.", "20 mail2.example.com."],
        }

        record = ResourceRecordSet.from_api_response(response, "example-zone")

        assert record.record_type == "MX"
        assert len(record.rrdatas) == 2

    def test_from_api_response_txt(self):
        """Test creating a TXT record from an API response."""
        response = {
            "name": "example.com.",
            "type": "TXT",
            "ttl": 300,
            "rrdatas": ['"v=spf1 include:_spf.google.com ~all"'],
        }

        record = ResourceRecordSet.from_api_response(response, "example-zone")

        assert record.record_type == "TXT"
        assert record.rrdatas == ['"v=spf1 include:_spf.google.com ~all"']

    def test_from_api_response_minimal(self):
        """Test creating a ResourceRecordSet from a minimal response."""
        record = ResourceRecordSet.from_api_response({"name": "test.com."})

        assert record.dns_name == "test.com."
        assert record.record_type == ""
        assert record.ttl == 0
        assert record.rrdatas == []
