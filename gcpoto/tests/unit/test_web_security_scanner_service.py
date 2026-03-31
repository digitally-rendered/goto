"""Tests for Web Security Scanner service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.web_security_scanner import WebSecurityScannerService
from gcpoto.models.web_security_scanner import ScanConfig, ScanRun
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
def sample_scan_config_response():
    """Sample Web Security Scanner scan config API response."""
    return {
        "name": "projects/test-project/scanConfigs/config-1",
        "displayName": "My Web App Scan",
        "startingUrls": ["https://example.com"],
        "maxQps": 15,
        "authentication": {
            "googleAccount": {
                "username": "user@example.com",
                "password": "secret",
            }
        },
        "userAgent": "CHROME_LINUX",
        "blacklistPatterns": ["https://example.com/admin/*"],
        "schedule": {
            "scheduleTime": "2024-02-01T00:00:00Z",
            "intervalDurationDays": 7,
        },
        "targetPlatforms": ["COMPUTE"],
        "createTime": "2024-01-10T08:00:00.000Z",
        "updateTime": "2024-01-15T10:30:00.000Z",
    }


@pytest.fixture
def sample_scan_run_response():
    """Sample Web Security Scanner scan run API response."""
    return {
        "name": "projects/test-project/scanConfigs/config-1/scanRuns/run-1",
        "executionState": "FINISHED",
        "resultState": "SUCCESS",
        "startTime": "2024-01-15T10:00:00.000Z",
        "endTime": "2024-01-15T11:30:00.000Z",
        "urlsCrawledCount": 150,
        "urlsTestedCount": 120,
    }


@pytest.fixture
def sample_finding_response():
    """Sample Web Security Scanner finding API response."""
    return {
        "name": "projects/test-project/scanConfigs/config-1/scanRuns/run-1/findings/finding-1",
        "findingType": "XSS",
        "severity": "HIGH",
        "httpMethod": "GET",
        "fuzzedUrl": "https://example.com/page?q=<script>alert(1)</script>",
        "body": "XSS vulnerability found",
        "description": "Cross-site scripting vulnerability",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a WebSecurityScannerService instance with mocked API client."""
    svc = WebSecurityScannerService(project_id="test-project")
    return svc


class TestWebSecurityScannerServiceInit:
    """Tests for WebSecurityScannerService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the WebSecurityScannerService."""
        from googleapiclient.discovery import build

        service = WebSecurityScannerService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "websecurityscanner"
        assert service.version == "v1"
        build.assert_called_once_with(
            "websecurityscanner", "v1", credentials=None
        )


class TestListScanConfigs:
    """Tests for listing scan configs."""

    def test_list_scan_configs(self, service, sample_scan_config_response):
        """Test listing scan configs."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .scanConfigs.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "scanConfigs": [sample_scan_config_response]
        }

        mock_list_next = (
            service.service.projects.return_value
            .scanConfigs.return_value.list_next
        )
        mock_list_next.return_value = None

        configs = service.list_scan_configs()

        mock_list.assert_called_once_with(parent="projects/test-project")
        assert len(configs) == 1
        assert isinstance(configs[0], ScanConfig)
        assert configs[0].display_name == "My Web App Scan"

    def test_list_scan_configs_empty(self, service):
        """Test listing scan configs when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .scanConfigs.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"scanConfigs": []}

        mock_list_next = (
            service.service.projects.return_value
            .scanConfigs.return_value.list_next
        )
        mock_list_next.return_value = None

        configs = service.list_scan_configs()

        assert len(configs) == 0


class TestGetScanConfig:
    """Tests for getting a scan config."""

    def test_get_scan_config(self, service, sample_scan_config_response):
        """Test getting a specific scan config."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .scanConfigs.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_scan_config_response

        config = service.get_scan_config("config-1")

        mock_get.assert_called_once_with(
            name="projects/test-project/scanConfigs/config-1"
        )
        assert isinstance(config, ScanConfig)
        assert config.display_name == "My Web App Scan"
        assert config.starting_urls == ["https://example.com"]

    def test_get_scan_config_not_found(self, service):
        """Test getting a scan config that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .scanConfigs.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_scan_config("missing-config")


class TestCreateScanConfig:
    """Tests for creating a scan config."""

    def test_create_scan_config(self, service, sample_scan_config_response):
        """Test creating a scan config."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .scanConfigs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_scan_config_response

        config = service.create_scan_config(
            display_name="My Web App Scan",
            starting_urls=["https://example.com"],
            max_qps=15,
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "displayName": "My Web App Scan",
                "startingUrls": ["https://example.com"],
                "maxQps": 15,
            },
        )
        assert isinstance(config, ScanConfig)
        assert config.display_name == "My Web App Scan"

    def test_create_scan_config_minimal(
        self, service, sample_scan_config_response
    ):
        """Test creating a scan config with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .scanConfigs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_scan_config_response

        config = service.create_scan_config(
            display_name="My Web App Scan",
            starting_urls=["https://example.com"],
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "displayName": "My Web App Scan",
                "startingUrls": ["https://example.com"],
            },
        )
        assert isinstance(config, ScanConfig)

    def test_create_scan_config_api_error(self, service):
        """Test creating a scan config with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .scanConfigs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_scan_config(
                display_name="Test",
                starting_urls=["https://example.com"],
            )


class TestUpdateScanConfig:
    """Tests for updating a scan config."""

    def test_update_scan_config(self, service, sample_scan_config_response):
        """Test updating a scan config."""
        mock_request = mock.MagicMock()
        mock_patch = (
            service.service.projects.return_value
            .scanConfigs.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_scan_config_response

        config = service.update_scan_config(
            config_id="config-1",
            update_mask="displayName,maxQps",
            update_fields={
                "displayName": "Updated Scan",
                "maxQps": 20,
            },
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/scanConfigs/config-1",
            updateMask="displayName,maxQps",
            body={
                "displayName": "Updated Scan",
                "maxQps": 20,
            },
        )
        assert isinstance(config, ScanConfig)

    def test_update_scan_config_not_found(self, service):
        """Test updating a scan config that does not exist."""
        mock_request = mock.MagicMock()
        mock_patch = (
            service.service.projects.return_value
            .scanConfigs.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_scan_config(
                config_id="missing",
                update_mask="displayName",
                update_fields={"displayName": "Test"},
            )


class TestDeleteScanConfig:
    """Tests for deleting a scan config."""

    def test_delete_scan_config(self, service):
        """Test deleting a scan config."""
        mock_request = mock.MagicMock()
        mock_delete = (
            service.service.projects.return_value
            .scanConfigs.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_scan_config("config-1")

        mock_delete.assert_called_once_with(
            name="projects/test-project/scanConfigs/config-1"
        )
        assert result is True

    def test_delete_scan_config_not_found(self, service):
        """Test deleting a scan config that does not exist."""
        mock_request = mock.MagicMock()
        mock_delete = (
            service.service.projects.return_value
            .scanConfigs.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_scan_config("missing-config")


class TestStartScan:
    """Tests for starting a scan."""

    def test_start_scan(self, service, sample_scan_run_response):
        """Test starting a scan."""
        mock_request = mock.MagicMock()
        mock_start = (
            service.service.projects.return_value
            .scanConfigs.return_value.start
        )
        mock_start.return_value = mock_request
        mock_request.execute.return_value = sample_scan_run_response

        run = service.start_scan("config-1")

        mock_start.assert_called_once_with(
            name="projects/test-project/scanConfigs/config-1",
            body={},
        )
        assert isinstance(run, ScanRun)
        assert run.execution_state == "FINISHED"

    def test_start_scan_not_found(self, service):
        """Test starting a scan for a config that does not exist."""
        mock_request = mock.MagicMock()
        mock_start = (
            service.service.projects.return_value
            .scanConfigs.return_value.start
        )
        mock_start.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.start_scan("missing-config")


class TestListScanRuns:
    """Tests for listing scan runs."""

    def test_list_scan_runs(self, service, sample_scan_run_response):
        """Test listing scan runs."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "scanRuns": [sample_scan_run_response]
        }

        mock_list_next = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value.list_next
        )
        mock_list_next.return_value = None

        runs = service.list_scan_runs("config-1")

        mock_list.assert_called_once_with(
            parent="projects/test-project/scanConfigs/config-1"
        )
        assert len(runs) == 1
        assert isinstance(runs[0], ScanRun)
        assert runs[0].execution_state == "FINISHED"

    def test_list_scan_runs_empty(self, service):
        """Test listing scan runs when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"scanRuns": []}

        mock_list_next = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value.list_next
        )
        mock_list_next.return_value = None

        runs = service.list_scan_runs("config-1")

        assert len(runs) == 0


class TestGetScanRun:
    """Tests for getting a scan run."""

    def test_get_scan_run(self, service, sample_scan_run_response):
        """Test getting a specific scan run."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_scan_run_response

        run = service.get_scan_run("config-1", "run-1")

        mock_get.assert_called_once_with(
            name="projects/test-project/scanConfigs/config-1/scanRuns/run-1"
        )
        assert isinstance(run, ScanRun)
        assert run.execution_state == "FINISHED"
        assert run.result_state == "SUCCESS"

    def test_get_scan_run_not_found(self, service):
        """Test getting a scan run that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_scan_run("config-1", "missing-run")


class TestListFindingsForRun:
    """Tests for listing findings for a scan run."""

    def test_list_findings_for_run(self, service, sample_finding_response):
        """Test listing findings for a scan run."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value
            .findings.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "findings": [sample_finding_response]
        }

        mock_list_next = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value
            .findings.return_value.list_next
        )
        mock_list_next.return_value = None

        findings = service.list_findings_for_run("config-1", "run-1")

        mock_list.assert_called_once_with(
            parent="projects/test-project/scanConfigs/config-1/scanRuns/run-1"
        )
        assert len(findings) == 1
        assert findings[0]["findingType"] == "XSS"

    def test_list_findings_for_run_with_filter(
        self, service, sample_finding_response
    ):
        """Test listing findings with a filter."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value
            .findings.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "findings": [sample_finding_response]
        }

        mock_list_next = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value
            .findings.return_value.list_next
        )
        mock_list_next.return_value = None

        findings = service.list_findings_for_run(
            "config-1", "run-1", filter_str='finding_type="XSS"'
        )

        mock_list.assert_called_once_with(
            parent="projects/test-project/scanConfigs/config-1/scanRuns/run-1",
            filter='finding_type="XSS"',
        )
        assert len(findings) == 1

    def test_list_findings_for_run_empty(self, service):
        """Test listing findings when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value
            .findings.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"findings": []}

        mock_list_next = (
            service.service.projects.return_value
            .scanConfigs.return_value
            .scanRuns.return_value
            .findings.return_value.list_next
        )
        mock_list_next.return_value = None

        findings = service.list_findings_for_run("config-1", "run-1")

        assert len(findings) == 0


class TestScanConfigModel:
    """Tests for the ScanConfig model."""

    def test_from_api_response(self, sample_scan_config_response):
        """Test creating a ScanConfig from an API response."""
        config = ScanConfig.from_api_response(sample_scan_config_response)

        assert config.name == "projects/test-project/scanConfigs/config-1"
        assert config.display_name == "My Web App Scan"
        assert config.starting_urls == ["https://example.com"]
        assert config.max_qps == 15
        assert config.user_agent == "CHROME_LINUX"
        assert config.blacklist_patterns == ["https://example.com/admin/*"]
        assert config.target_platforms == ["COMPUTE"]
        assert config.type == "websecurityscanner.scanconfig"

    def test_from_api_response_minimal(self):
        """Test creating a ScanConfig from a minimal API response."""
        config = ScanConfig.from_api_response(
            {"name": "projects/test-project/scanConfigs/c1"}
        )

        assert config.display_name == ""
        assert config.starting_urls == []
        assert config.max_qps is None
        assert config.authentication is None


class TestScanRunModel:
    """Tests for the ScanRun model."""

    def test_from_api_response(self, sample_scan_run_response):
        """Test creating a ScanRun from an API response."""
        run = ScanRun.from_api_response(sample_scan_run_response)

        assert (
            run.name
            == "projects/test-project/scanConfigs/config-1/scanRuns/run-1"
        )
        assert run.execution_state == "FINISHED"
        assert run.result_state == "SUCCESS"
        assert run.urls_crawled_count == 150
        assert run.urls_tested_count == 120
        assert run.type == "websecurityscanner.scanrun"
        assert (
            run.scan_config_name
            == "projects/test-project/scanConfigs/config-1"
        )

    def test_from_api_response_minimal(self):
        """Test creating a ScanRun from a minimal API response."""
        run = ScanRun.from_api_response(
            {
                "name": "projects/test-project/scanConfigs/c1/scanRuns/r1",
                "executionState": "QUEUED",
            }
        )

        assert run.execution_state == "QUEUED"
        assert run.result_state is None
        assert run.urls_crawled_count is None
