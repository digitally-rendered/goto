"""Tests for Document AI service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.document_ai import DocumentAIService
from gcpoto.models.document_ai import Processor, ProcessorVersion, ProcessResult
from gcpoto.exceptions import ResourceNotFoundError, APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects

        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations

        mock_processors = mock.MagicMock()
        mock_locations.processors.return_value = mock_processors

        mock_processor_versions = mock.MagicMock()
        mock_processors.processorVersions.return_value = mock_processor_versions

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a DocumentAIService with mocked client."""
    return DocumentAIService(project_id="test-project")


@pytest.fixture
def sample_processor_response():
    """Sample Document AI processor API response."""
    return {
        "name": "projects/test-project/locations/us/processors/abc123",
        "displayName": "test-processor",
        "type": "OCR_PROCESSOR",
        "state": "ENABLED",
        "defaultProcessorVersion": "projects/test-project/locations/us/processors/abc123/processorVersions/pretrained-ocr-v1",
        "labels": {"env": "test"},
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-02T00:00:00Z",
    }


@pytest.fixture
def sample_processor_version_response():
    """Sample Document AI processor version API response."""
    return {
        "name": "projects/test-project/locations/us/processors/abc123/processorVersions/v1",
        "displayName": "v1",
        "state": "DEPLOYED",
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-02T00:00:00Z",
    }


@pytest.fixture
def sample_process_result_response():
    """Sample Document AI process result API response."""
    return {
        "document": {
            "text": "Hello World",
            "pages": [{"pageNumber": 1}],
        },
        "humanReviewStatus": {
            "state": "SKIPPED",
            "stateMessage": "Skipped by request",
        },
    }


def _make_http_error(status_code, reason="error"):
    """Create a mock HttpError with the given status code."""
    resp = mock.MagicMock()
    resp.status = status_code
    return HttpError(resp, b'{"error": {"message": "' + reason.encode() + b'"}}')


# ---- Processor Model Tests ----


class TestProcessorModel:
    def test_from_api_response(self, sample_processor_response):
        processor = Processor.from_api_response(sample_processor_response)
        assert processor.id == "abc123"
        assert processor.display_name == "test-processor"
        assert processor.location == "us"
        assert processor.project == "test-project"
        assert processor.type == "documentai.processor"
        assert processor.processor_type == "OCR_PROCESSOR"
        assert processor.state == "ENABLED"
        assert processor.default_processor_version is not None

    def test_from_api_response_minimal(self):
        response = {
            "name": "projects/p/locations/us/processors/1",
            "displayName": "minimal",
            "type": "FORM_PARSER_PROCESSOR",
            "state": "ENABLED",
        }
        processor = Processor.from_api_response(response)
        assert processor.id == "1"
        assert processor.display_name == "minimal"
        assert processor.default_processor_version is None

    def test_get_tag(self, sample_processor_response):
        processor = Processor.from_api_response(sample_processor_response)
        assert processor.get_tag("env") == "test"
        assert processor.get_tag("missing", "default") == "default"


class TestProcessorVersionModel:
    def test_from_api_response(self, sample_processor_version_response):
        version = ProcessorVersion.from_api_response(
            sample_processor_version_response
        )
        assert version.id == "v1"
        assert version.display_name == "v1"
        assert version.state == "DEPLOYED"
        assert version.location == "us"
        assert version.processor_name == "projects/test-project/locations/us/processors/abc123"

    def test_from_api_response_minimal(self):
        response = {
            "name": "projects/p/locations/eu/processors/x/processorVersions/v2",
            "state": "UNDEPLOYED",
        }
        version = ProcessorVersion.from_api_response(response)
        assert version.id == "v2"
        assert version.state == "UNDEPLOYED"
        assert version.display_name is None


class TestProcessResultModel:
    def test_from_api_response(self, sample_process_result_response):
        result = ProcessResult.from_api_response(sample_process_result_response)
        assert result.document["text"] == "Hello World"
        assert result.human_review_status["state"] == "SKIPPED"

    def test_from_api_response_minimal(self):
        response = {"document": {"text": "test"}}
        result = ProcessResult.from_api_response(response)
        assert result.document["text"] == "test"
        assert result.human_review_status is None


# ---- Processor Service Tests ----


class TestDocumentAIServiceProcessors:
    def test_list_processors(self, service, sample_processor_response):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.list().execute.return_value = {
            "processors": [sample_processor_response]
        }
        mock_processors.list_next.return_value = None

        results = service.list_processors("us")
        assert len(results) == 1
        assert results[0].display_name == "test-processor"
        assert isinstance(results[0], Processor)

    def test_list_processors_empty(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.list().execute.return_value = {}
        mock_processors.list_next.return_value = None

        results = service.list_processors("us")
        assert len(results) == 0

    def test_list_processors_pagination(
        self, service, sample_processor_response
    ):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        second_response = sample_processor_response.copy()
        second_response["name"] = (
            "projects/test-project/locations/us/processors/def456"
        )
        second_response["displayName"] = "test-processor-2"

        mock_processors.list().execute.return_value = {
            "processors": [sample_processor_response]
        }
        next_request = mock.MagicMock()
        next_request.execute.return_value = {
            "processors": [second_response]
        }
        mock_processors.list_next.side_effect = [next_request, None]

        results = service.list_processors("us")
        assert len(results) == 2
        assert results[0].display_name == "test-processor"
        assert results[1].display_name == "test-processor-2"

    def test_get_processor(self, service, sample_processor_response):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.get().execute.return_value = sample_processor_response

        result = service.get_processor("us", "abc123")
        assert result.display_name == "test-processor"
        assert result.id == "abc123"

    def test_get_processor_not_found(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.get().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.get_processor("us", "nonexistent")

    def test_get_processor_api_error(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.get().execute.side_effect = _make_http_error(500)

        with pytest.raises(APIError):
            service.get_processor("us", "abc123")

    def test_create_processor(self, service, sample_processor_response):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.create().execute.return_value = (
            sample_processor_response
        )

        result = service.create_processor(
            location="us",
            display_name="test-processor",
            processor_type="OCR_PROCESSOR",
        )
        assert result.display_name == "test-processor"
        assert isinstance(result, Processor)

    def test_create_processor_api_error(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.create().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.create_processor(
                location="us",
                display_name="bad",
                processor_type="INVALID",
            )

    def test_delete_processor(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.delete().execute.return_value = {}

        assert service.delete_processor("us", "abc123") is True

    def test_delete_processor_not_found(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.delete().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.delete_processor("us", "nonexistent")

    def test_enable_processor(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.enable().execute.return_value = {
            "name": "projects/test-project/locations/us/operations/op1"
        }

        result = service.enable_processor("us", "abc123")
        assert "name" in result

    def test_enable_processor_not_found(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.enable().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.enable_processor("us", "nonexistent")

    def test_disable_processor(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.disable().execute.return_value = {
            "name": "projects/test-project/locations/us/operations/op2"
        }

        result = service.disable_processor("us", "abc123")
        assert "name" in result

    def test_disable_processor_not_found(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.disable().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.disable_processor("us", "nonexistent")

    def test_process_document_raw(
        self, service, sample_process_result_response
    ):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.process().execute.return_value = (
            sample_process_result_response
        )

        result = service.process_document(
            location="us",
            processor_id="abc123",
            raw_document={"content": "base64data", "mimeType": "application/pdf"},
        )
        assert isinstance(result, ProcessResult)
        assert result.document["text"] == "Hello World"

    def test_process_document_gcs(
        self, service, sample_process_result_response
    ):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.process().execute.return_value = (
            sample_process_result_response
        )

        result = service.process_document(
            location="us",
            processor_id="abc123",
            gcs_document={"gcsUri": "gs://bucket/doc.pdf", "mimeType": "application/pdf"},
            skip_human_review=True,
        )
        assert isinstance(result, ProcessResult)

    def test_process_document_not_found(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.process().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.process_document(
                location="us",
                processor_id="nonexistent",
                raw_document={"content": "data", "mimeType": "application/pdf"},
            )

    def test_batch_process_documents(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.batchProcess().execute.return_value = {
            "name": "projects/test-project/locations/us/operations/op3"
        }

        result = service.batch_process_documents(
            location="us",
            processor_id="abc123",
            input_documents={
                "gcsDocuments": {
                    "documents": [
                        {"gcsUri": "gs://bucket/doc1.pdf", "mimeType": "application/pdf"}
                    ]
                }
            },
            output_gcs_destination="gs://bucket/output/",
        )
        assert "name" in result

    def test_batch_process_documents_not_found(self, service):
        mock_processors = (
            service.service.projects()
            .locations()
            .processors()
        )
        mock_processors.batchProcess().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.batch_process_documents(
                location="us",
                processor_id="nonexistent",
                input_documents={"gcsDocuments": {"documents": []}},
                output_gcs_destination="gs://bucket/output/",
            )


# ---- Processor Version Service Tests ----


class TestDocumentAIServiceProcessorVersions:
    def test_list_processor_versions(
        self, service, sample_processor_version_response
    ):
        mock_versions = (
            service.service.projects()
            .locations()
            .processors()
            .processorVersions()
        )
        mock_versions.list().execute.return_value = {
            "processorVersions": [sample_processor_version_response]
        }
        mock_versions.list_next.return_value = None

        results = service.list_processor_versions("us", "abc123")
        assert len(results) == 1
        assert results[0].display_name == "v1"
        assert isinstance(results[0], ProcessorVersion)

    def test_list_processor_versions_empty(self, service):
        mock_versions = (
            service.service.projects()
            .locations()
            .processors()
            .processorVersions()
        )
        mock_versions.list().execute.return_value = {}
        mock_versions.list_next.return_value = None

        results = service.list_processor_versions("us", "abc123")
        assert len(results) == 0


# ---- Path Formatting Tests ----


class TestDocumentAIServicePathFormatting:
    def test_format_parent(self, service):
        assert service._format_parent("us") == (
            "projects/test-project/locations/us"
        )

    def test_format_processor_name(self, service):
        assert service._format_processor_name("us", "abc123") == (
            "projects/test-project/locations/us/processors/abc123"
        )

    def test_format_processor_name_full_path(self, service):
        full_path = "projects/other/locations/eu/processors/xyz"
        assert service._format_processor_name("us", full_path) == full_path


# ---- Service Initialization Tests ----


class TestDocumentAIServiceInit:
    def test_service_init(self, service):
        assert service.project_id == "test-project"
        assert service.service_name == "documentai"
        assert service.version == "v1"
        assert service.resource_model == Processor
