"""Tests for Security Command Center service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.security_center import SecurityCenterService
from gcpoto.models.security_center import Finding, Source
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
def sample_finding_response():
    """Sample SCC finding API response."""
    return {
        "name": "organizations/123/sources/456/findings/finding-1",
        "category": "OPEN_FIREWALL",
        "state": "ACTIVE",
        "severity": "HIGH",
        "sourceProperties": {"scannerName": "FIREWALL_SCANNER"},
        "securityMarks": {"marks": {"priority": "high"}},
        "eventTime": "2024-01-15T10:30:00.000Z",
        "resourceName": "//compute.googleapis.com/projects/test-project/global/firewalls/allow-all",
        "externalUri": "https://console.cloud.google.com/security",
        "createTime": "2024-01-15T10:30:00.000Z",
        "updateTime": "2024-01-16T12:00:00.000Z",
    }


@pytest.fixture
def sample_source_response():
    """Sample SCC source API response."""
    return {
        "name": "organizations/123/sources/456",
        "displayName": "Custom Source",
        "description": "A custom security source",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a SecurityCenterService instance with mocked API client."""
    svc = SecurityCenterService(project_id="test-project")
    return svc


class TestSecurityCenterServiceInit:
    """Tests for SecurityCenterService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the SecurityCenterService."""
        from googleapiclient.discovery import build

        service = SecurityCenterService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "securitycenter"
        assert service.version == "v1"
        build.assert_called_once_with("securitycenter", "v1", credentials=None)


class TestListSources:
    """Tests for listing SCC sources."""

    def test_list_sources(self, service, sample_source_response):
        """Test listing SCC sources."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.organizations.return_value.sources.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "sources": [sample_source_response]
        }

        mock_list_next = (
            service.service.organizations.return_value.sources.return_value.list_next
        )
        mock_list_next.return_value = None

        sources = service.list_sources("123")

        mock_list.assert_called_once_with(parent="organizations/123")
        assert len(sources) == 1
        assert isinstance(sources[0], Source)
        assert sources[0].display_name == "Custom Source"

    def test_list_sources_empty(self, service):
        """Test listing sources when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.organizations.return_value.sources.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"sources": []}

        mock_list_next = (
            service.service.organizations.return_value.sources.return_value.list_next
        )
        mock_list_next.return_value = None

        sources = service.list_sources("123")

        assert len(sources) == 0


class TestGetSource:
    """Tests for getting an SCC source."""

    def test_get_source(self, service, sample_source_response):
        """Test getting a specific SCC source."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.organizations.return_value.sources.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_source_response

        source = service.get_source("organizations/123/sources/456")

        mock_get.assert_called_once_with(name="organizations/123/sources/456")
        assert isinstance(source, Source)
        assert source.display_name == "Custom Source"

    def test_get_source_not_found(self, service):
        """Test getting a source that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.organizations.return_value.sources.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_source("organizations/123/sources/999")


class TestListFindings:
    """Tests for listing findings."""

    def test_list_findings(self, service, sample_finding_response):
        """Test listing findings for a source."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "listFindingsResults": [{"finding": sample_finding_response}]
        }

        mock_list_next = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.list_next
        )
        mock_list_next.return_value = None

        findings = service.list_findings("organizations/123/sources/456")

        mock_list.assert_called_once_with(
            parent="organizations/123/sources/456"
        )
        assert len(findings) == 1
        assert isinstance(findings[0], Finding)
        assert findings[0].category == "OPEN_FIREWALL"
        assert findings[0].state == "ACTIVE"
        assert findings[0].severity == "HIGH"

    def test_list_findings_with_filter(self, service, sample_finding_response):
        """Test listing findings with a filter."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "listFindingsResults": [{"finding": sample_finding_response}]
        }

        mock_list_next = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.list_next
        )
        mock_list_next.return_value = None

        findings = service.list_findings(
            "organizations/123/sources/456",
            filter_str='state="ACTIVE"',
        )

        mock_list.assert_called_once_with(
            parent="organizations/123/sources/456",
            filter='state="ACTIVE"',
        )
        assert len(findings) == 1

    def test_list_findings_empty(self, service):
        """Test listing findings when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"listFindingsResults": []}

        mock_list_next = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.list_next
        )
        mock_list_next.return_value = None

        findings = service.list_findings("organizations/123/sources/456")

        assert len(findings) == 0


class TestGetFinding:
    """Tests for getting a finding."""

    def test_get_finding(self, service, sample_finding_response):
        """Test getting a specific finding."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_finding_response

        finding = service.get_finding(
            "organizations/123/sources/456/findings/finding-1"
        )

        mock_get.assert_called_once_with(
            name="organizations/123/sources/456/findings/finding-1"
        )
        assert isinstance(finding, Finding)
        assert finding.category == "OPEN_FIREWALL"

    def test_get_finding_not_found(self, service):
        """Test getting a finding that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_finding(
                "organizations/123/sources/456/findings/missing"
            )


class TestSetFindingState:
    """Tests for setting finding state."""

    def test_set_finding_state(self, service, sample_finding_response):
        """Test setting a finding's state."""
        mock_request = mock.MagicMock()
        inactive_response = dict(sample_finding_response)
        inactive_response["state"] = "INACTIVE"
        mock_set_state = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.setState
        )
        mock_set_state.return_value = mock_request
        mock_request.execute.return_value = inactive_response

        finding = service.set_finding_state(
            "organizations/123/sources/456/findings/finding-1",
            "INACTIVE",
        )

        mock_set_state.assert_called_once_with(
            name="organizations/123/sources/456/findings/finding-1",
            body={"state": "INACTIVE"},
        )
        assert isinstance(finding, Finding)
        assert finding.state == "INACTIVE"

    def test_set_finding_state_not_found(self, service):
        """Test setting state on a finding that does not exist."""
        mock_request = mock.MagicMock()
        mock_set_state = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.setState
        )
        mock_set_state.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.set_finding_state(
                "organizations/123/sources/456/findings/missing",
                "INACTIVE",
            )


class TestUpdateSecurityMarks:
    """Tests for updating security marks."""

    def test_update_security_marks(self, service, sample_finding_response):
        """Test updating security marks on a finding."""
        mock_request = mock.MagicMock()
        mock_update = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.updateSecurityMarks
        )
        mock_update.return_value = mock_request
        mock_request.execute.return_value = sample_finding_response

        finding = service.update_security_marks(
            "organizations/123/sources/456/findings/finding-1",
            {"priority": "critical", "team": "security"},
        )

        mock_update.assert_called_once_with(
            name="organizations/123/sources/456/findings/finding-1/securityMarks",
            body={
                "securityMarks": {
                    "marks": {"priority": "critical", "team": "security"}
                }
            },
        )
        assert isinstance(finding, Finding)

    def test_update_security_marks_not_found(self, service):
        """Test updating marks on a finding that does not exist."""
        mock_request = mock.MagicMock()
        mock_update = (
            service.service.organizations.return_value
            .sources.return_value
            .findings.return_value.updateSecurityMarks
        )
        mock_update.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_security_marks(
                "organizations/123/sources/456/findings/missing",
                {"priority": "high"},
            )


class TestCreateSource:
    """Tests for creating an SCC source."""

    def test_create_source(self, service, sample_source_response):
        """Test creating an SCC source."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.organizations.return_value.sources.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_source_response

        source = service.create_source(
            organization_id="123",
            display_name="Custom Source",
            description="A custom security source",
        )

        mock_create.assert_called_once_with(
            parent="organizations/123",
            body={
                "displayName": "Custom Source",
                "description": "A custom security source",
            },
        )
        assert isinstance(source, Source)
        assert source.display_name == "Custom Source"

    def test_create_source_minimal(self, service, sample_source_response):
        """Test creating a source with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.organizations.return_value.sources.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_source_response

        source = service.create_source(
            organization_id="123",
            display_name="Custom Source",
        )

        mock_create.assert_called_once_with(
            parent="organizations/123",
            body={"displayName": "Custom Source"},
        )
        assert isinstance(source, Source)

    def test_create_source_api_error(self, service):
        """Test creating a source with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.organizations.return_value.sources.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_source(
                organization_id="123",
                display_name="Custom Source",
            )


class TestFindingModel:
    """Tests for the Finding model."""

    def test_from_api_response(self, sample_finding_response):
        """Test creating a Finding from an API response."""
        finding = Finding.from_api_response(sample_finding_response)

        assert finding.name == "organizations/123/sources/456/findings/finding-1"
        assert finding.category == "OPEN_FIREWALL"
        assert finding.state == "ACTIVE"
        assert finding.severity == "HIGH"
        assert finding.source_properties == {"scannerName": "FIREWALL_SCANNER"}
        assert finding.security_marks == {"priority": "high"}
        assert finding.external_uri == "https://console.cloud.google.com/security"
        assert finding.type == "securitycenter.finding"

    def test_from_api_response_minimal(self):
        """Test creating a Finding from a minimal API response."""
        finding = Finding.from_api_response({"name": "organizations/123/sources/456/findings/f1"})

        assert finding.name == "organizations/123/sources/456/findings/f1"
        assert finding.category == ""
        assert finding.state == "ACTIVE"
        assert finding.severity == ""


class TestSourceModel:
    """Tests for the Source model."""

    def test_from_api_response(self, sample_source_response):
        """Test creating a Source from an API response."""
        source = Source.from_api_response(sample_source_response)

        assert source.name == "organizations/123/sources/456"
        assert source.display_name == "Custom Source"
        assert source.description == "A custom security source"
        assert source.type == "securitycenter.source"

    def test_from_api_response_minimal(self):
        """Test creating a Source from a minimal API response."""
        source = Source.from_api_response({"name": "organizations/123/sources/1"})

        assert source.display_name == ""
        assert source.description is None
