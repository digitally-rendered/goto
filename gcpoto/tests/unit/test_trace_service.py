"""Tests for Cloud Trace service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.trace import TraceService
from gcpoto.models.trace import Trace, TraceSpan
from gcpoto.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().traces() chain
        mock_traces = mock.MagicMock()
        mock_service.projects.return_value.traces.return_value = mock_traces

        yield mock_service


@pytest.fixture
def sample_span_response():
    """Sample Cloud Trace span API response."""
    return {
        "name": "projects/test-project/traces/abc123/spans/span-001",
        "spanId": "span-001",
        "parentSpanId": None,
        "displayName": {"value": "GET /api/users"},
        "startTime": "2025-01-15T10:30:00Z",
        "endTime": "2025-01-15T10:30:01Z",
        "status": {"code": 0},
        "attributes": {
            "attributeMap": {
                "http.method": {"stringValue": {"value": "GET"}},
            }
        },
    }


# ---- Model Tests ----


class TestTraceModel:
    def test_from_api_response(self):
        """Test creating a Trace from an API response."""
        response = {
            "traceId": "abc123",
            "spans": [
                {
                    "name": "projects/test-project/traces/abc123/spans/span-001",
                    "spanId": "span-001",
                }
            ],
        }
        trace = Trace.from_api_response(response)

        assert trace.trace_id == "abc123"
        assert trace.id == "abc123"
        assert trace.project == "test-project"
        assert trace.type == "cloudtrace.trace"
        assert len(trace.spans) == 1

    def test_from_api_response_minimal(self):
        """Test creating a Trace from a minimal API response."""
        trace = Trace.from_api_response({})

        assert trace.trace_id == ""
        assert trace.spans == []
        assert trace.project == ""


class TestTraceSpanModel:
    def test_from_api_response(self, sample_span_response):
        """Test creating a TraceSpan from an API response."""
        span = TraceSpan.from_api_response(sample_span_response)

        assert span.span_id == "span-001"
        assert span.trace_id == "abc123"
        assert span.project == "test-project"
        assert span.display_name == "GET /api/users"
        assert span.type == "cloudtrace.span"
        assert span.status == {"code": 0}
        assert span.parent_span_id is None

    def test_from_api_response_minimal(self):
        """Test creating a TraceSpan from a minimal API response."""
        span = TraceSpan.from_api_response({})

        assert span.span_id == ""
        assert span.trace_id == ""
        assert span.display_name == ""

    def test_from_api_response_string_display_name(self):
        """Test creating a TraceSpan with a string displayName."""
        response = {
            "name": "projects/test-project/traces/abc/spans/s1",
            "spanId": "s1",
            "displayName": "simple-name",
        }
        span = TraceSpan.from_api_response(response)

        assert span.display_name == "simple-name"


# ---- Service Init ----


class TestTraceServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the TraceService."""
        from googleapiclient.discovery import build

        service = TraceService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "cloudtrace"
        assert service.version == "v2"
        build.assert_called_once_with("cloudtrace", "v2", credentials=None)


# ---- List Traces ----


class TestListTraces:
    def test_list_traces(self, mock_google_client, sample_span_response):
        """Test listing traces."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.traces.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "spans": [sample_span_response]
        }
        mock_list_next = (
            mock_google_client.projects.return_value.traces.return_value.list_next
        )
        mock_list_next.return_value = None

        service = TraceService(project_id="test-project")
        spans = service.list_traces()

        mock_list.assert_called_once_with(parent="projects/test-project")

        assert len(spans) == 1
        assert isinstance(spans[0], TraceSpan)
        assert spans[0].span_id == "span-001"

    def test_list_traces_with_filter(self, mock_google_client):
        """Test listing traces with a filter."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.traces.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"spans": []}
        mock_list_next = (
            mock_google_client.projects.return_value.traces.return_value.list_next
        )
        mock_list_next.return_value = None

        service = TraceService(project_id="test-project")
        spans = service.list_traces(
            filter_str='+span:"/api"',
            start_time="2025-01-15T00:00:00Z",
            end_time="2025-01-16T00:00:00Z",
        )

        mock_list.assert_called_once_with(
            parent="projects/test-project",
            filter='+span:"/api"',
            startTime="2025-01-15T00:00:00Z",
            endTime="2025-01-16T00:00:00Z",
        )

        assert spans == []

    def test_list_traces_empty(self, mock_google_client):
        """Test listing traces when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.traces.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_list_next = (
            mock_google_client.projects.return_value.traces.return_value.list_next
        )
        mock_list_next.return_value = None

        service = TraceService(project_id="test-project")
        spans = service.list_traces()

        assert spans == []


# ---- Get Trace ----


class TestGetTrace:
    def test_get_trace(self, mock_google_client, sample_span_response):
        """Test getting a specific trace."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.traces.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "spans": [sample_span_response]
        }

        service = TraceService(project_id="test-project")
        spans = service.get_trace("abc123")

        mock_list.assert_called_once_with(
            parent="projects/test-project",
            filter='+traceId:"abc123"',
        )

        assert len(spans) == 1
        assert isinstance(spans[0], TraceSpan)
        assert spans[0].span_id == "span-001"

    def test_get_trace_not_found(self, mock_google_client):
        """Test getting a trace that does not exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.traces.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Trace not found"
        )

        service = TraceService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_trace("nonexistent-trace")


# ---- Batch Write Spans ----


class TestBatchWriteSpans:
    def test_batch_write_spans(self, mock_google_client):
        """Test batch writing spans."""
        mock_request = mock.MagicMock()
        mock_batch_write = (
            mock_google_client.projects.return_value.traces.return_value.batchWrite
        )
        mock_batch_write.return_value = mock_request
        mock_request.execute.return_value = {}

        service = TraceService(project_id="test-project")
        spans = [
            {
                "name": "projects/test-project/traces/abc123/spans/span-001",
                "spanId": "span-001",
                "displayName": {"value": "GET /api/users"},
                "startTime": "2025-01-15T10:30:00Z",
                "endTime": "2025-01-15T10:30:01Z",
            }
        ]
        result = service.batch_write_spans(spans)

        mock_batch_write.assert_called_once_with(
            name="projects/test-project",
            body={"spans": spans},
        )
        assert result is True
