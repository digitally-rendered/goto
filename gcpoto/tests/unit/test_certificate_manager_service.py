"""Tests for Certificate Manager service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.certificate_manager import CertificateManagerService
from gcpoto.models.certificate_manager import Certificate, CertificateMap
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
def sample_certificate_response():
    """Sample Certificate Manager certificate API response."""
    return {
        "name": "projects/test-project/locations/global/certificates/my-cert",
        "description": "My TLS certificate",
        "sanDnsnames": ["example.com", "*.example.com"],
        "pemCertificate": "-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----",
        "expireTime": "2025-12-31T23:59:59.000Z",
        "scope": "DEFAULT",
        "managed": {
            "domains": ["example.com", "*.example.com"],
            "state": "ACTIVE",
        },
        "labels": {"env": "production", "team": "platform"},
        "project": "test-project",
        "location": "global",
        "createTime": "2024-01-15T10:30:00.000Z",
        "updateTime": "2024-06-15T12:00:00.000Z",
    }


@pytest.fixture
def sample_certificate_map_response():
    """Sample Certificate Manager certificate map API response."""
    return {
        "name": "projects/test-project/locations/global/certificateMaps/my-map",
        "description": "My certificate map",
        "gclbTargets": [
            {
                "targetHttpsProxy": "projects/test-project/global/targetHttpsProxies/proxy-1",
                "ipConfigs": [
                    {"ipAddress": "34.120.0.1", "ports": [443]},
                ],
            }
        ],
        "labels": {"env": "production"},
        "project": "test-project",
        "location": "global",
        "createTime": "2024-01-15T10:30:00.000Z",
        "updateTime": "2024-06-15T12:00:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a CertificateManagerService instance with mocked API client."""
    svc = CertificateManagerService(project_id="test-project")
    return svc


class TestCertificateManagerServiceInit:
    """Tests for CertificateManagerService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the CertificateManagerService."""
        from googleapiclient.discovery import build

        service = CertificateManagerService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "certificatemanager"
        assert service.version == "v1"
        build.assert_called_once_with(
            "certificatemanager", "v1", credentials=None
        )


class TestListCertificates:
    """Tests for listing certificates."""

    def test_list_certificates(self, service, sample_certificate_response):
        """Test listing certificates."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "certificates": [sample_certificate_response]
        }

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.list_next
        )
        mock_list_next.return_value = None

        certificates = service.list_certificates("global")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(certificates) == 1
        assert isinstance(certificates[0], Certificate)
        assert certificates[0].description == "My TLS certificate"

    def test_list_certificates_empty(self, service):
        """Test listing certificates when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"certificates": []}

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.list_next
        )
        mock_list_next.return_value = None

        certificates = service.list_certificates("global")

        assert len(certificates) == 0


class TestGetCertificate:
    """Tests for getting a certificate."""

    def test_get_certificate(self, service, sample_certificate_response):
        """Test getting a specific certificate."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_certificate_response

        cert = service.get_certificate("global", "my-cert")

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/global/certificates/my-cert"
        )
        assert isinstance(cert, Certificate)
        assert cert.description == "My TLS certificate"
        assert cert.san_dnsnames == ["example.com", "*.example.com"]

    def test_get_certificate_not_found(self, service):
        """Test getting a certificate that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_certificate("global", "nonexistent-cert")

    def test_get_certificate_api_error(self, service):
        """Test getting a certificate with an API error."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_certificate("global", "my-cert")


class TestCreateCertificate:
    """Tests for creating a certificate."""

    def test_create_managed_certificate(
        self, service, sample_certificate_response
    ):
        """Test creating a managed certificate."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_certificate_response

        cert = service.create_certificate(
            location="global",
            cert_name="my-cert",
            managed={"domains": ["example.com", "*.example.com"]},
            description="My TLS certificate",
            labels={"env": "production", "team": "platform"},
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            certificateId="my-cert",
            body={
                "managed": {"domains": ["example.com", "*.example.com"]},
                "description": "My TLS certificate",
                "labels": {"env": "production", "team": "platform"},
            },
        )
        assert isinstance(cert, Certificate)

    def test_create_self_managed_certificate(
        self, service, sample_certificate_response
    ):
        """Test creating a self-managed certificate."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_certificate_response

        cert = service.create_certificate(
            location="global",
            cert_name="my-cert",
            self_managed={
                "pemCertificate": "-----BEGIN CERTIFICATE-----",
                "pemPrivateKey": "-----BEGIN PRIVATE KEY-----",
            },
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            certificateId="my-cert",
            body={
                "selfManaged": {
                    "pemCertificate": "-----BEGIN CERTIFICATE-----",
                    "pemPrivateKey": "-----BEGIN PRIVATE KEY-----",
                },
            },
        )
        assert isinstance(cert, Certificate)

    def test_create_certificate_already_exists(self, service):
        """Test creating a certificate that already exists."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_certificate(
                location="global",
                cert_name="my-cert",
                managed={"domains": ["example.com"]},
            )

    def test_create_certificate_api_error(self, service):
        """Test creating a certificate with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_certificate(
                location="global",
                cert_name="my-cert",
                managed={"domains": ["example.com"]},
            )


class TestDeleteCertificate:
    """Tests for deleting a certificate."""

    def test_delete_certificate(self, service):
        """Test deleting a certificate."""
        mock_request = mock.MagicMock()
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_certificate("global", "my-cert")

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/global/certificates/my-cert"
        )
        assert result is True

    def test_delete_certificate_not_found(self, service):
        """Test deleting a certificate that does not exist."""
        mock_request = mock.MagicMock()
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .certificates.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_certificate("global", "nonexistent-cert")


class TestListCertificateMaps:
    """Tests for listing certificate maps."""

    def test_list_certificate_maps(
        self, service, sample_certificate_map_response
    ):
        """Test listing certificate maps."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "certificateMaps": [sample_certificate_map_response]
        }

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.list_next
        )
        mock_list_next.return_value = None

        maps = service.list_certificate_maps("global")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(maps) == 1
        assert isinstance(maps[0], CertificateMap)
        assert maps[0].description == "My certificate map"

    def test_list_certificate_maps_empty(self, service):
        """Test listing certificate maps when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"certificateMaps": []}

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.list_next
        )
        mock_list_next.return_value = None

        maps = service.list_certificate_maps("global")

        assert len(maps) == 0


class TestGetCertificateMap:
    """Tests for getting a certificate map."""

    def test_get_certificate_map(
        self, service, sample_certificate_map_response
    ):
        """Test getting a specific certificate map."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_certificate_map_response

        cert_map = service.get_certificate_map("global", "my-map")

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/global/certificateMaps/my-map"
        )
        assert isinstance(cert_map, CertificateMap)
        assert cert_map.description == "My certificate map"
        assert len(cert_map.gclb_targets) == 1

    def test_get_certificate_map_not_found(self, service):
        """Test getting a certificate map that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_certificate_map("global", "nonexistent-map")


class TestCreateCertificateMap:
    """Tests for creating a certificate map."""

    def test_create_certificate_map(
        self, service, sample_certificate_map_response
    ):
        """Test creating a certificate map."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_certificate_map_response

        cert_map = service.create_certificate_map(
            location="global",
            map_name="my-map",
            description="My certificate map",
            labels={"env": "production"},
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            certificateMapId="my-map",
            body={
                "description": "My certificate map",
                "labels": {"env": "production"},
            },
        )
        assert isinstance(cert_map, CertificateMap)

    def test_create_certificate_map_minimal(
        self, service, sample_certificate_map_response
    ):
        """Test creating a certificate map with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_certificate_map_response

        cert_map = service.create_certificate_map(
            location="global",
            map_name="my-map",
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            certificateMapId="my-map",
            body={},
        )
        assert isinstance(cert_map, CertificateMap)

    def test_create_certificate_map_already_exists(self, service):
        """Test creating a certificate map that already exists."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_certificate_map(
                location="global",
                map_name="my-map",
            )

    def test_create_certificate_map_api_error(self, service):
        """Test creating a certificate map with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_certificate_map(
                location="global",
                map_name="my-map",
            )


class TestDeleteCertificateMap:
    """Tests for deleting a certificate map."""

    def test_delete_certificate_map(self, service):
        """Test deleting a certificate map."""
        mock_request = mock.MagicMock()
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_certificate_map("global", "my-map")

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/global/certificateMaps/my-map"
        )
        assert result is True

    def test_delete_certificate_map_not_found(self, service):
        """Test deleting a certificate map that does not exist."""
        mock_request = mock.MagicMock()
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .certificateMaps.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_certificate_map("global", "nonexistent-map")


class TestCertificateModel:
    """Tests for the Certificate model."""

    def test_from_api_response(self, sample_certificate_response):
        """Test creating a Certificate from an API response."""
        cert = Certificate.from_api_response(sample_certificate_response)

        assert cert.id == "my-cert"
        assert cert.name == "projects/test-project/locations/global/certificates/my-cert"
        assert cert.description == "My TLS certificate"
        assert cert.san_dnsnames == ["example.com", "*.example.com"]
        assert cert.scope == "DEFAULT"
        assert cert.managed == {
            "domains": ["example.com", "*.example.com"],
            "state": "ACTIVE",
        }
        assert cert.type == "certificatemanager.certificate"
        assert cert.labels == {"env": "production", "team": "platform"}

    def test_get_tag(self, sample_certificate_response):
        """Test the get_tag method."""
        cert = Certificate.from_api_response(sample_certificate_response)

        assert cert.get_tag("env") == "production"
        assert cert.get_tag("team") == "platform"
        assert cert.get_tag("missing") == ""
        assert cert.get_tag("missing", "default") == "default"

    def test_from_api_response_minimal(self):
        """Test creating a Certificate from a minimal API response."""
        cert = Certificate.from_api_response(
            {"name": "projects/p/locations/global/certificates/c"}
        )

        assert cert.id == "c"
        assert cert.description is None
        assert cert.san_dnsnames is None
        assert cert.managed is None
        assert cert.self_managed is None


class TestCertificateMapModel:
    """Tests for the CertificateMap model."""

    def test_from_api_response(self, sample_certificate_map_response):
        """Test creating a CertificateMap from an API response."""
        cert_map = CertificateMap.from_api_response(
            sample_certificate_map_response
        )

        assert cert_map.id == "my-map"
        assert cert_map.name == "projects/test-project/locations/global/certificateMaps/my-map"
        assert cert_map.description == "My certificate map"
        assert cert_map.type == "certificatemanager.certificateMap"
        assert len(cert_map.gclb_targets) == 1
        assert cert_map.labels == {"env": "production"}

    def test_get_tag(self, sample_certificate_map_response):
        """Test the get_tag method."""
        cert_map = CertificateMap.from_api_response(
            sample_certificate_map_response
        )

        assert cert_map.get_tag("env") == "production"
        assert cert_map.get_tag("missing") == ""

    def test_from_api_response_minimal(self):
        """Test creating a CertificateMap from a minimal API response."""
        cert_map = CertificateMap.from_api_response(
            {"name": "projects/p/locations/global/certificateMaps/m"}
        )

        assert cert_map.id == "m"
        assert cert_map.description is None
        assert cert_map.gclb_targets is None
