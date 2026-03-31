"""Tests for Cloud Error Reporting service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.error_reporting import ErrorReportingService
from gcpoto.models.error_reporting import ErrorGroup, ErrorEvent
from gcpoto.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().groupStats() chain
        mock_group_stats = mock.MagicMock()
        mock_service.projects.return_value.groupStats.return_value = (
            mock_group_stats
        )

        # Set up projects().events() chain
        mock_events = mock.MagicMock()
        mock_service.projects.return_value.events.return_value = mock_events

        # Set up projects().groups() chain
        mock_groups = mock.MagicMock()
        mock_service.projects.return_value.groups.return_value = mock_groups

        yield mock_service


@pytest.fixture
def sample_error_group_response():
    """Sample Cloud Error Reporting error group API response."""
    return {
        "name": "projects/test-project/groups/group-abc-123",
        "groupId": "group-abc-123",
        "trackingIssues": [
            {"url": "https://bugs.example.com/123"}
        ],
        "resolutionStatus": "OPEN",
    }


@pytest.fixture
def sample_error_event_response():
    """Sample Cloud Error Reporting error event API response."""
    return {
        "eventTime": "2025-01-15T10:30:00Z",
        "serviceContext": {
            "service": "my-service",
            "version": "v1.0",
        },
        "message": "java.lang.NullPointerException: Something was null\n\tat com.example.App.run(App.java:42)",
        "context": {
            "httpRequest": {
                "method": "GET",
                "url": "/api/users",
                "responseStatusCode": 500,
            },
            "user": "user@example.com",
            "reportLocation": {
                "filePath": "com/example/App.java",
                "lineNumber": 42,
                "functionName": "run",
            },
        },
        "group": {
            "groupId": "group-abc-123",
        },
    }


@pytest.fixture
def sample_group_stats_response():
    """Sample Cloud Error Reporting group stats API response."""
    return {
        "group": {
            "name": "projects/test-project/groups/group-abc-123",
            "groupId": "group-abc-123",
        },
        "count": "42",
        "affectedUsersCount": "5",
        "timedCounts": [
            {"count": "10", "startTime": "2025-01-15T10:00:00Z"},
        ],
        "firstSeenTime": "2025-01-10T08:00:00Z",
        "lastSeenTime": "2025-01-15T10:30:00Z",
    }


# ---- Model Tests ----


class TestErrorGroupModel:
    def test_from_api_response(self, sample_error_group_response):
        """Test creating an ErrorGroup from an API response."""
        group = ErrorGroup.from_api_response(sample_error_group_response)

        assert group.group_id == "group-abc-123"
        assert group.id == "group-abc-123"
        assert group.project == "test-project"
        assert group.type == "clouderrorreporting.errorGroup"
        assert group.resolution_status == "OPEN"
        assert len(group.tracking_issues) == 1
        assert group.tracking_issues[0]["url"] == "https://bugs.example.com/123"

    def test_from_api_response_minimal(self):
        """Test creating an ErrorGroup from a minimal API response."""
        group = ErrorGroup.from_api_response({})

        assert group.group_id == ""
        assert group.tracking_issues is None
        assert group.resolution_status is None


class TestErrorEventModel:
    def test_from_api_response(self, sample_error_event_response):
        """Test creating an ErrorEvent from an API response."""
        event = ErrorEvent.from_api_response(sample_error_event_response)

        assert event.group_id == "group-abc-123"
        assert event.type == "clouderrorreporting.errorEvent"
        assert event.service_context["service"] == "my-service"
        assert event.service_context["version"] == "v1.0"
        assert "NullPointerException" in event.message
        assert event.context["user"] == "user@example.com"
        assert event.event_time == "2025-01-15T10:30:00Z"

    def test_from_api_response_minimal(self):
        """Test creating an ErrorEvent from a minimal API response."""
        event = ErrorEvent.from_api_response({})

        assert event.group_id == ""
        assert event.message == ""
        assert event.service_context == {}
        assert event.context is None
        assert event.event_time is None


# ---- Service Init ----


class TestErrorReportingServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the ErrorReportingService."""
        from googleapiclient.discovery import build

        service = ErrorReportingService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "clouderrorreporting"
        assert service.version == "v1beta1"
        build.assert_called_once_with(
            "clouderrorreporting", "v1beta1", credentials=None
        )


# ---- List Group Stats ----


class TestListGroupStats:
    def test_list_group_stats(
        self, mock_google_client, sample_group_stats_response
    ):
        """Test listing error group statistics."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.groupStats.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "errorGroupStats": [sample_group_stats_response]
        }
        mock_list_next = (
            mock_google_client.projects.return_value.groupStats.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ErrorReportingService(project_id="test-project")
        stats = service.list_group_stats()

        mock_list.assert_called_once_with(
            projectName="projects/test-project"
        )

        assert len(stats) == 1
        assert stats[0]["count"] == "42"

    def test_list_group_stats_with_filter(self, mock_google_client):
        """Test listing group stats with time range and filter."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.groupStats.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"errorGroupStats": []}
        mock_list_next = (
            mock_google_client.projects.return_value.groupStats.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ErrorReportingService(project_id="test-project")
        stats = service.list_group_stats(
            time_range="PERIOD_1_DAY",
            filter_str="serviceContext.service=my-service",
        )

        mock_list.assert_called_once_with(
            projectName="projects/test-project",
            timeRange_period="PERIOD_1_DAY",
            filter="serviceContext.service=my-service",
        )

        assert stats == []

    def test_list_group_stats_empty(self, mock_google_client):
        """Test listing group stats when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.groupStats.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_list_next = (
            mock_google_client.projects.return_value.groupStats.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ErrorReportingService(project_id="test-project")
        stats = service.list_group_stats()

        assert stats == []


# ---- List Events ----


class TestListEvents:
    def test_list_events(
        self, mock_google_client, sample_error_event_response
    ):
        """Test listing error events for a group."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.events.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "errorEvents": [sample_error_event_response]
        }
        mock_list_next = (
            mock_google_client.projects.return_value.events.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ErrorReportingService(project_id="test-project")
        events = service.list_events("group-abc-123")

        mock_list.assert_called_once_with(
            projectName="projects/test-project",
            groupId="group-abc-123",
        )

        assert len(events) == 1
        assert isinstance(events[0], ErrorEvent)
        assert events[0].group_id == "group-abc-123"

    def test_list_events_with_time_range(self, mock_google_client):
        """Test listing events with a time range."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.events.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"errorEvents": []}
        mock_list_next = (
            mock_google_client.projects.return_value.events.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ErrorReportingService(project_id="test-project")
        events = service.list_events(
            "group-abc-123", time_range="PERIOD_1_HOUR"
        )

        mock_list.assert_called_once_with(
            projectName="projects/test-project",
            groupId="group-abc-123",
            timeRange_period="PERIOD_1_HOUR",
        )

        assert events == []

    def test_list_events_empty(self, mock_google_client):
        """Test listing events when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.events.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_list_next = (
            mock_google_client.projects.return_value.events.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ErrorReportingService(project_id="test-project")
        events = service.list_events("group-abc-123")

        assert events == []


# ---- Report Event ----


class TestReportEvent:
    def test_report_event(self, mock_google_client):
        """Test reporting an error event."""
        mock_request = mock.MagicMock()
        mock_report = (
            mock_google_client.projects.return_value.events.return_value.report
        )
        mock_report.return_value = mock_request
        mock_request.execute.return_value = {}

        service = ErrorReportingService(project_id="test-project")
        result = service.report_event(
            service_name="my-service",
            version="v1.0",
            message="Error: something went wrong",
        )

        mock_report.assert_called_once_with(
            projectName="projects/test-project",
            body={
                "serviceContext": {
                    "service": "my-service",
                    "version": "v1.0",
                },
                "message": "Error: something went wrong",
            },
        )

        assert result == {}

    def test_report_event_with_user(self, mock_google_client):
        """Test reporting an error event with user context."""
        mock_request = mock.MagicMock()
        mock_report = (
            mock_google_client.projects.return_value.events.return_value.report
        )
        mock_report.return_value = mock_request
        mock_request.execute.return_value = {}

        service = ErrorReportingService(project_id="test-project")
        result = service.report_event(
            service_name="my-service",
            version="v1.0",
            message="Error: something went wrong",
            user="user@example.com",
        )

        mock_report.assert_called_once_with(
            projectName="projects/test-project",
            body={
                "serviceContext": {
                    "service": "my-service",
                    "version": "v1.0",
                },
                "message": "Error: something went wrong",
                "context": {"user": "user@example.com"},
            },
        )

        assert result == {}


# ---- Get Group ----


class TestGetGroup:
    def test_get_group(
        self, mock_google_client, sample_error_group_response
    ):
        """Test getting a specific error group."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.groups.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_error_group_response

        service = ErrorReportingService(project_id="test-project")
        group = service.get_group("group-abc-123")

        mock_get.assert_called_once_with(
            groupName="projects/test-project/groups/group-abc-123"
        )

        assert isinstance(group, ErrorGroup)
        assert group.group_id == "group-abc-123"
        assert group.resolution_status == "OPEN"

    def test_get_group_full_path(
        self, mock_google_client, sample_error_group_response
    ):
        """Test getting a group with a full resource name."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.groups.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_error_group_response

        service = ErrorReportingService(project_id="test-project")
        service.get_group("projects/test-project/groups/group-abc-123")

        mock_get.assert_called_with(
            groupName="projects/test-project/groups/group-abc-123"
        )

    def test_get_group_not_found(self, mock_google_client):
        """Test getting a group that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.groups.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Group not found"
        )

        service = ErrorReportingService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_group("nonexistent-group")


# ---- Update Group ----


class TestUpdateGroup:
    def test_update_group(
        self, mock_google_client, sample_error_group_response
    ):
        """Test updating an error group."""
        mock_request = mock.MagicMock()
        mock_update = (
            mock_google_client.projects.return_value.groups.return_value.update
        )
        mock_update.return_value = mock_request
        updated_response = dict(sample_error_group_response)
        updated_response["resolutionStatus"] = "RESOLVED"
        mock_request.execute.return_value = updated_response

        service = ErrorReportingService(project_id="test-project")
        group = service.update_group(
            "group-abc-123", resolution_status="RESOLVED"
        )

        mock_update.assert_called_once_with(
            name="projects/test-project/groups/group-abc-123",
            body={
                "name": "projects/test-project/groups/group-abc-123",
                "resolutionStatus": "RESOLVED",
            },
        )

        assert isinstance(group, ErrorGroup)
        assert group.resolution_status == "RESOLVED"

    def test_update_group_full_path(
        self, mock_google_client, sample_error_group_response
    ):
        """Test updating a group with a full resource name."""
        mock_request = mock.MagicMock()
        mock_update = (
            mock_google_client.projects.return_value.groups.return_value.update
        )
        mock_update.return_value = mock_request
        mock_request.execute.return_value = sample_error_group_response

        service = ErrorReportingService(project_id="test-project")
        service.update_group(
            "projects/test-project/groups/group-abc-123",
            resolution_status="ACKNOWLEDGED",
        )

        mock_update.assert_called_with(
            name="projects/test-project/groups/group-abc-123",
            body={
                "name": "projects/test-project/groups/group-abc-123",
                "resolutionStatus": "ACKNOWLEDGED",
            },
        )


# ---- Delete Events ----


class TestDeleteEvents:
    def test_delete_events(self, mock_google_client):
        """Test deleting all error events."""
        mock_request = mock.MagicMock()
        mock_delete = mock_google_client.projects.return_value.deleteEvents
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = ErrorReportingService(project_id="test-project")
        result = service.delete_events()

        mock_delete.assert_called_once_with(
            projectName="projects/test-project"
        )
        assert result is True
