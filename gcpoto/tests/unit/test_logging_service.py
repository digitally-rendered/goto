"""Tests for Cloud Logging service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.logging_service import LoggingService
from gcpoto.models.logging_service import LogEntry, LogSink, LogMetric
from gcpoto.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up entries() chain
        mock_entries = mock.MagicMock()
        mock_service.entries.return_value = mock_entries

        # Set up projects().logs() chain
        mock_logs = mock.MagicMock()
        mock_service.projects.return_value.logs.return_value = mock_logs

        # Set up projects().sinks() chain
        mock_sinks = mock.MagicMock()
        mock_service.projects.return_value.sinks.return_value = mock_sinks

        # Set up projects().metrics() chain
        mock_metrics = mock.MagicMock()
        mock_service.projects.return_value.metrics.return_value = mock_metrics

        yield mock_service


@pytest.fixture
def sample_log_entry_response():
    """Sample Cloud Logging log entry API response."""
    return {
        "logName": "projects/test-project/logs/my-log",
        "severity": "ERROR",
        "textPayload": "Something went wrong",
        "timestamp": "2025-01-15T10:30:00Z",
        "resource": {
            "type": "gce_instance",
            "labels": {"instance_id": "123456", "zone": "us-central1-a"},
        },
        "insertId": "entry-abc-123",
        "trace": "projects/test-project/traces/abc123",
        "labels": {"env": "production", "component": "api"},
    }


@pytest.fixture
def sample_sink_response():
    """Sample Cloud Logging sink API response."""
    return {
        "name": "projects/test-project/sinks/my-sink",
        "destination": "storage.googleapis.com/my-bucket",
        "filter": 'severity >= "ERROR"',
        "description": "Export error logs to GCS",
        "disabled": False,
        "writerIdentity": "serviceAccount:p123-456@gcp-sa-logging.iam.gserviceaccount.com",
        "includeChildren": False,
        "exclusions": [
            {
                "name": "exclude-debug",
                "filter": 'severity = "DEBUG"',
                "description": "Exclude debug logs",
                "disabled": False,
            }
        ],
        "createTime": "2025-01-10T08:00:00Z",
        "updateTime": "2025-01-12T12:00:00Z",
    }


@pytest.fixture
def sample_metric_response():
    """Sample Cloud Logging metric API response."""
    return {
        "name": "projects/test-project/metrics/error-count",
        "description": "Count of error log entries",
        "filter": 'severity >= "ERROR"',
        "metricDescriptor": {
            "metricKind": "DELTA",
            "valueType": "INT64",
        },
        "valueExtractor": "EXTRACT(jsonPayload.response_code)",
        "labelExtractors": {
            "service": "EXTRACT(resource.labels.service_name)",
        },
        "createTime": "2025-01-10T08:00:00Z",
        "updateTime": "2025-01-12T12:00:00Z",
    }


# ---- Service Init ----


class TestLoggingServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the LoggingService."""
        from googleapiclient.discovery import build

        service = LoggingService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "logging"
        assert service.version == "v2"
        build.assert_called_once_with("logging", "v2", credentials=None)


# ---- Log Entry Model ----


class TestLogEntryModel:
    def test_from_api_response(self, sample_log_entry_response):
        """Test creating a LogEntry from an API response."""
        entry = LogEntry.from_api_response(sample_log_entry_response)

        assert entry.name == "my-log"
        assert entry.project == "test-project"
        assert entry.log_name == "projects/test-project/logs/my-log"
        assert entry.severity == "ERROR"
        assert entry.text_payload == "Something went wrong"
        assert entry.resource_type == "gce_instance"
        assert entry.resource_labels == {
            "instance_id": "123456",
            "zone": "us-central1-a",
        }
        assert entry.insert_id == "entry-abc-123"
        assert entry.trace == "projects/test-project/traces/abc123"
        assert entry.type == "logging.logEntry"

    def test_from_api_response_minimal(self):
        """Test creating a LogEntry from a minimal API response."""
        entry = LogEntry.from_api_response({})

        assert entry.name == ""
        assert entry.severity == "DEFAULT"
        assert entry.text_payload is None
        assert entry.json_payload is None
        assert entry.timestamp is None

    def test_from_api_response_json_payload(self):
        """Test creating a LogEntry with a JSON payload."""
        response = {
            "logName": "projects/test-project/logs/structured-log",
            "severity": "INFO",
            "jsonPayload": {"message": "Hello", "code": 200},
            "insertId": "json-entry-1",
        }
        entry = LogEntry.from_api_response(response)

        assert entry.json_payload == {"message": "Hello", "code": 200}
        assert entry.text_payload is None

    def test_get_tag(self, sample_log_entry_response):
        """Test get_tag on LogEntry."""
        entry = LogEntry.from_api_response(sample_log_entry_response)

        assert entry.get_tag("env") == "production"
        assert entry.get_tag("component") == "api"
        assert entry.get_tag("missing", "default") == "default"


# ---- Log Sink Model ----


class TestLogSinkModel:
    def test_from_api_response(self, sample_sink_response):
        """Test creating a LogSink from an API response."""
        sink = LogSink.from_api_response(sample_sink_response)

        assert sink.name == "my-sink"
        assert sink.project == "test-project"
        assert sink.destination == "storage.googleapis.com/my-bucket"
        assert sink.filter_str == 'severity >= "ERROR"'
        assert sink.description == "Export error logs to GCS"
        assert sink.disabled is False
        assert sink.writer_identity == (
            "serviceAccount:p123-456@gcp-sa-logging.iam.gserviceaccount.com"
        )
        assert sink.include_children is False
        assert len(sink.exclusions) == 1
        assert sink.exclusions[0]["name"] == "exclude-debug"
        assert sink.type == "logging.sink"

    def test_from_api_response_minimal(self):
        """Test creating a LogSink from a minimal API response."""
        sink = LogSink.from_api_response({"name": "simple-sink"})

        assert sink.name == "simple-sink"
        assert sink.destination == ""
        assert sink.filter_str is None
        assert sink.disabled is False
        assert sink.include_children is False
        assert sink.exclusions is None

    def test_from_api_response_short_name(self):
        """Test LogSink with a short name (no project prefix)."""
        sink = LogSink.from_api_response(
            {"name": "my-sink", "destination": "bigquery.googleapis.com/my-dataset"}
        )
        assert sink.name == "my-sink"
        assert sink.project == ""


# ---- Log Metric Model ----


class TestLogMetricModel:
    def test_from_api_response(self, sample_metric_response):
        """Test creating a LogMetric from an API response."""
        metric = LogMetric.from_api_response(sample_metric_response)

        assert metric.name == "error-count"
        assert metric.project == "test-project"
        assert metric.description == "Count of error log entries"
        assert metric.filter_str == 'severity >= "ERROR"'
        assert metric.metric_descriptor == {
            "metricKind": "DELTA",
            "valueType": "INT64",
        }
        assert metric.value_extractor == "EXTRACT(jsonPayload.response_code)"
        assert metric.label_extractors == {
            "service": "EXTRACT(resource.labels.service_name)",
        }
        assert metric.type == "logging.metric"

    def test_from_api_response_minimal(self):
        """Test creating a LogMetric from a minimal API response."""
        metric = LogMetric.from_api_response({"name": "simple-metric"})

        assert metric.name == "simple-metric"
        assert metric.filter_str == ""
        assert metric.description is None
        assert metric.metric_descriptor is None
        assert metric.value_extractor is None
        assert metric.label_extractors is None


# ---- Log Entries Service Methods ----


class TestListLogEntries:
    def test_list_log_entries(self, mock_google_client, sample_log_entry_response):
        """Test listing log entries."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.entries.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "entries": [sample_log_entry_response, sample_log_entry_response]
        }

        service = LoggingService(project_id="test-project")
        entries = service.list_log_entries()

        mock_list.assert_called_once_with(
            body={
                "resourceNames": ["projects/test-project"],
                "pageSize": 100,
            }
        )

        assert len(entries) == 2
        assert isinstance(entries[0], LogEntry)
        assert entries[0].name == "my-log"
        assert entries[0].severity == "ERROR"

    def test_list_log_entries_with_filter(self, mock_google_client):
        """Test listing log entries with a filter."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.entries.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"entries": []}

        service = LoggingService(project_id="test-project")
        entries = service.list_log_entries(
            filter_str='severity >= "ERROR"',
            order_by="timestamp desc",
            page_size=50,
        )

        mock_list.assert_called_once_with(
            body={
                "resourceNames": ["projects/test-project"],
                "pageSize": 50,
                "filter": 'severity >= "ERROR"',
                "orderBy": "timestamp desc",
            }
        )

        assert entries == []

    def test_list_log_entries_empty(self, mock_google_client):
        """Test listing log entries when none exist."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.entries.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        entries = service.list_log_entries()

        assert entries == []


class TestWriteLogEntry:
    def test_write_log_entry_text(self, mock_google_client):
        """Test writing a text log entry."""
        mock_request = mock.MagicMock()
        mock_write = mock_google_client.entries.return_value.write
        mock_write.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        result = service.write_log_entry(
            log_name="my-log",
            severity="ERROR",
            text_payload="Something went wrong",
        )

        mock_write.assert_called_once_with(
            body={
                "logName": "projects/test-project/logs/my-log",
                "resource": {"type": "global"},
                "entries": [
                    {
                        "logName": "projects/test-project/logs/my-log",
                        "severity": "ERROR",
                        "textPayload": "Something went wrong",
                        "resource": {"type": "global"},
                    }
                ],
            }
        )

        assert result == {}

    def test_write_log_entry_json(self, mock_google_client):
        """Test writing a JSON log entry."""
        mock_request = mock.MagicMock()
        mock_write = mock_google_client.entries.return_value.write
        mock_write.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        result = service.write_log_entry(
            log_name="structured-log",
            severity="INFO",
            json_payload={"message": "Hello", "code": 200},
            resource_type="gce_instance",
            resource_labels={"instance_id": "123"},
            labels={"env": "prod"},
        )

        call_body = mock_write.call_args[1]["body"]
        entry = call_body["entries"][0]

        assert entry["jsonPayload"] == {"message": "Hello", "code": 200}
        assert entry["resource"]["type"] == "gce_instance"
        assert entry["resource"]["labels"] == {"instance_id": "123"}
        assert entry["labels"] == {"env": "prod"}
        assert "textPayload" not in entry

    def test_write_log_entry_full_path(self, mock_google_client):
        """Test writing with a fully qualified log name."""
        mock_request = mock.MagicMock()
        mock_write = mock_google_client.entries.return_value.write
        mock_write.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        service.write_log_entry(
            log_name="projects/test-project/logs/my-log",
            severity="INFO",
            text_payload="test",
        )

        call_body = mock_write.call_args[1]["body"]
        assert call_body["logName"] == "projects/test-project/logs/my-log"


class TestDeleteLog:
    def test_delete_log(self, mock_google_client):
        """Test deleting a log."""
        mock_request = mock.MagicMock()
        mock_delete = mock_google_client.projects.return_value.logs.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        result = service.delete_log("my-log")

        mock_delete.assert_called_once_with(
            logName="projects/test-project/logs/my-log"
        )
        assert result is True

    def test_delete_log_full_path(self, mock_google_client):
        """Test deleting a log with a full path."""
        mock_request = mock.MagicMock()
        mock_delete = mock_google_client.projects.return_value.logs.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        service.delete_log("projects/test-project/logs/my-log")

        mock_delete.assert_called_with(
            logName="projects/test-project/logs/my-log"
        )


class TestListLogs:
    def test_list_logs(self, mock_google_client):
        """Test listing log names."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.projects.return_value.logs.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "logNames": [
                "projects/test-project/logs/log-a",
                "projects/test-project/logs/log-b",
            ]
        }

        service = LoggingService(project_id="test-project")
        logs = service.list_logs()

        mock_list.assert_called_once_with(parent="projects/test-project")

        assert len(logs) == 2
        assert logs[0] == "projects/test-project/logs/log-a"

    def test_list_logs_empty(self, mock_google_client):
        """Test listing logs when none exist."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.projects.return_value.logs.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        logs = service.list_logs()

        assert logs == []


# ---- Sinks Service Methods ----


class TestListSinks:
    def test_list_sinks(self, mock_google_client, sample_sink_response):
        """Test listing log sinks."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.projects.return_value.sinks.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "sinks": [sample_sink_response]
        }

        service = LoggingService(project_id="test-project")
        sinks = service.list_sinks()

        mock_list.assert_called_once_with(parent="projects/test-project")

        assert len(sinks) == 1
        assert isinstance(sinks[0], LogSink)
        assert sinks[0].name == "my-sink"
        assert sinks[0].destination == "storage.googleapis.com/my-bucket"

    def test_list_sinks_empty(self, mock_google_client):
        """Test listing sinks when none exist."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.projects.return_value.sinks.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        sinks = service.list_sinks()

        assert sinks == []


class TestGetSink:
    def test_get_sink(self, mock_google_client, sample_sink_response):
        """Test getting a specific sink."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.projects.return_value.sinks.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_sink_response

        service = LoggingService(project_id="test-project")
        sink = service.get_sink("my-sink")

        mock_get.assert_called_once_with(
            sinkName="projects/test-project/sinks/my-sink"
        )

        assert isinstance(sink, LogSink)
        assert sink.name == "my-sink"
        assert sink.destination == "storage.googleapis.com/my-bucket"

    def test_get_sink_full_path(self, mock_google_client, sample_sink_response):
        """Test getting a sink with a full path."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.projects.return_value.sinks.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_sink_response

        service = LoggingService(project_id="test-project")
        service.get_sink("projects/test-project/sinks/my-sink")

        mock_get.assert_called_with(
            sinkName="projects/test-project/sinks/my-sink"
        )

    def test_get_sink_not_found(self, mock_google_client):
        """Test getting a sink that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.projects.return_value.sinks.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Sink not found"
        )

        service = LoggingService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_sink("nonexistent-sink")


class TestCreateSink:
    def test_create_sink(self, mock_google_client, sample_sink_response):
        """Test creating a log sink."""
        mock_request = mock.MagicMock()
        mock_create = mock_google_client.projects.return_value.sinks.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_sink_response

        service = LoggingService(project_id="test-project")
        sink = service.create_sink(
            sink_name="my-sink",
            destination="storage.googleapis.com/my-bucket",
            filter_str='severity >= "ERROR"',
            description="Export error logs to GCS",
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "name": "my-sink",
                "destination": "storage.googleapis.com/my-bucket",
                "filter": 'severity >= "ERROR"',
                "description": "Export error logs to GCS",
            },
        )

        assert isinstance(sink, LogSink)
        assert sink.name == "my-sink"

    def test_create_sink_minimal(self, mock_google_client, sample_sink_response):
        """Test creating a sink with minimal arguments."""
        mock_request = mock.MagicMock()
        mock_create = mock_google_client.projects.return_value.sinks.return_value.create
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_sink_response

        service = LoggingService(project_id="test-project")
        service.create_sink(
            sink_name="my-sink",
            destination="storage.googleapis.com/my-bucket",
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "name": "my-sink",
                "destination": "storage.googleapis.com/my-bucket",
            },
        )


class TestUpdateSink:
    def test_update_sink(self, mock_google_client, sample_sink_response):
        """Test updating a log sink."""
        mock_request = mock.MagicMock()
        mock_update = mock_google_client.projects.return_value.sinks.return_value.update
        mock_update.return_value = mock_request
        mock_request.execute.return_value = sample_sink_response

        service = LoggingService(project_id="test-project")
        sink = service.update_sink(
            sink_name="my-sink",
            destination="bigquery.googleapis.com/my-dataset",
            filter_str='severity >= "WARNING"',
            description="Updated description",
        )

        mock_update.assert_called_once_with(
            sinkName="projects/test-project/sinks/my-sink",
            body={
                "destination": "bigquery.googleapis.com/my-dataset",
                "filter": 'severity >= "WARNING"',
                "description": "Updated description",
            },
        )

        assert isinstance(sink, LogSink)

    def test_update_sink_partial(self, mock_google_client, sample_sink_response):
        """Test partially updating a log sink."""
        mock_request = mock.MagicMock()
        mock_update = mock_google_client.projects.return_value.sinks.return_value.update
        mock_update.return_value = mock_request
        mock_request.execute.return_value = sample_sink_response

        service = LoggingService(project_id="test-project")
        service.update_sink(
            sink_name="my-sink",
            description="Only updating description",
        )

        mock_update.assert_called_once_with(
            sinkName="projects/test-project/sinks/my-sink",
            body={"description": "Only updating description"},
        )


class TestDeleteSink:
    def test_delete_sink(self, mock_google_client):
        """Test deleting a log sink."""
        mock_request = mock.MagicMock()
        mock_delete = mock_google_client.projects.return_value.sinks.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        result = service.delete_sink("my-sink")

        mock_delete.assert_called_once_with(
            sinkName="projects/test-project/sinks/my-sink"
        )
        assert result is True

    def test_delete_sink_full_path(self, mock_google_client):
        """Test deleting a sink with a full path."""
        mock_request = mock.MagicMock()
        mock_delete = mock_google_client.projects.return_value.sinks.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        service.delete_sink("projects/test-project/sinks/my-sink")

        mock_delete.assert_called_with(
            sinkName="projects/test-project/sinks/my-sink"
        )


# ---- Metrics Service Methods ----


class TestListMetrics:
    def test_list_metrics(self, mock_google_client, sample_metric_response):
        """Test listing log-based metrics."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.projects.return_value.metrics.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "metrics": [sample_metric_response]
        }

        service = LoggingService(project_id="test-project")
        metrics = service.list_metrics()

        mock_list.assert_called_once_with(parent="projects/test-project")

        assert len(metrics) == 1
        assert isinstance(metrics[0], LogMetric)
        assert metrics[0].name == "error-count"
        assert metrics[0].filter_str == 'severity >= "ERROR"'

    def test_list_metrics_empty(self, mock_google_client):
        """Test listing metrics when none exist."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.projects.return_value.metrics.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        metrics = service.list_metrics()

        assert metrics == []


class TestGetMetric:
    def test_get_metric(self, mock_google_client, sample_metric_response):
        """Test getting a specific metric."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.projects.return_value.metrics.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_metric_response

        service = LoggingService(project_id="test-project")
        metric = service.get_metric("error-count")

        mock_get.assert_called_once_with(
            metricName="projects/test-project/metrics/error-count"
        )

        assert isinstance(metric, LogMetric)
        assert metric.name == "error-count"

    def test_get_metric_full_path(self, mock_google_client, sample_metric_response):
        """Test getting a metric with a full path."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.projects.return_value.metrics.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_metric_response

        service = LoggingService(project_id="test-project")
        service.get_metric("projects/test-project/metrics/error-count")

        mock_get.assert_called_with(
            metricName="projects/test-project/metrics/error-count"
        )

    def test_get_metric_not_found(self, mock_google_client):
        """Test getting a metric that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.projects.return_value.metrics.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Metric not found"
        )

        service = LoggingService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_metric("nonexistent-metric")


class TestCreateMetric:
    def test_create_metric(self, mock_google_client, sample_metric_response):
        """Test creating a log-based metric."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.metrics.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_metric_response

        service = LoggingService(project_id="test-project")
        metric = service.create_metric(
            metric_name="error-count",
            filter_str='severity >= "ERROR"',
            description="Count of error log entries",
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "name": "error-count",
                "filter": 'severity >= "ERROR"',
                "description": "Count of error log entries",
            },
        )

        assert isinstance(metric, LogMetric)
        assert metric.name == "error-count"

    def test_create_metric_minimal(self, mock_google_client, sample_metric_response):
        """Test creating a metric with minimal arguments."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.metrics.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_metric_response

        service = LoggingService(project_id="test-project")
        service.create_metric(
            metric_name="error-count",
            filter_str='severity >= "ERROR"',
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "name": "error-count",
                "filter": 'severity >= "ERROR"',
            },
        )


class TestUpdateMetric:
    def test_update_metric(self, mock_google_client, sample_metric_response):
        """Test updating a log-based metric."""
        mock_request = mock.MagicMock()
        mock_update = (
            mock_google_client.projects.return_value.metrics.return_value.update
        )
        mock_update.return_value = mock_request
        mock_request.execute.return_value = sample_metric_response

        service = LoggingService(project_id="test-project")
        metric = service.update_metric(
            metric_name="error-count",
            filter_str='severity >= "WARNING"',
            description="Updated description",
        )

        mock_update.assert_called_once_with(
            metricName="projects/test-project/metrics/error-count",
            body={
                "filter": 'severity >= "WARNING"',
                "description": "Updated description",
            },
        )

        assert isinstance(metric, LogMetric)

    def test_update_metric_partial(self, mock_google_client, sample_metric_response):
        """Test partially updating a log-based metric."""
        mock_request = mock.MagicMock()
        mock_update = (
            mock_google_client.projects.return_value.metrics.return_value.update
        )
        mock_update.return_value = mock_request
        mock_request.execute.return_value = sample_metric_response

        service = LoggingService(project_id="test-project")
        service.update_metric(
            metric_name="error-count",
            description="Only updating description",
        )

        mock_update.assert_called_once_with(
            metricName="projects/test-project/metrics/error-count",
            body={"description": "Only updating description"},
        )


class TestDeleteMetric:
    def test_delete_metric(self, mock_google_client):
        """Test deleting a log-based metric."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.metrics.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        result = service.delete_metric("error-count")

        mock_delete.assert_called_once_with(
            metricName="projects/test-project/metrics/error-count"
        )
        assert result is True

    def test_delete_metric_full_path(self, mock_google_client):
        """Test deleting a metric with a full path."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.metrics.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = LoggingService(project_id="test-project")
        service.delete_metric("projects/test-project/metrics/error-count")

        mock_delete.assert_called_with(
            metricName="projects/test-project/metrics/error-count"
        )
