"""Tests for Translation service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.translation import TranslationService
from gcpoto.models.translation import Translation, DetectedLanguage
from gcpoto.exceptions import APIError


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

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a TranslationService with mocked client."""
    return TranslationService(project_id="test-project")


@pytest.fixture
def sample_translate_response():
    """Sample Translation API translate response."""
    return {
        "translations": [
            {
                "translatedText": "Bonjour le monde",
                "detectedLanguageCode": "en",
                "model": "projects/test-project/locations/global/models/general/nmt",
            }
        ]
    }


@pytest.fixture
def sample_detect_response():
    """Sample Translation API detect language response."""
    return {
        "languages": [
            {
                "languageCode": "en",
                "confidence": 0.98,
            },
            {
                "languageCode": "de",
                "confidence": 0.01,
            },
        ]
    }


@pytest.fixture
def sample_supported_languages_response():
    """Sample Translation API supported languages response."""
    return {
        "languages": [
            {
                "languageCode": "en",
                "displayName": "English",
                "supportSource": True,
                "supportTarget": True,
            },
            {
                "languageCode": "fr",
                "displayName": "French",
                "supportSource": True,
                "supportTarget": True,
            },
        ]
    }


@pytest.fixture
def sample_batch_translate_response():
    """Sample Translation API batch translate response."""
    return {
        "name": "projects/test-project/locations/global/operations/12345",
        "metadata": {
            "@type": "type.googleapis.com/google.cloud.translation.v3.BatchTranslateMetadata",
            "state": "RUNNING",
        },
    }


def _make_http_error(status_code, reason="error"):
    """Create a mock HttpError with the given status code."""
    resp = mock.MagicMock()
    resp.status = status_code
    return HttpError(
        resp, b'{"error": {"message": "' + reason.encode() + b'"}}'
    )


# ---- Translation Model Tests ----


class TestTranslationModel:
    def test_from_api_response(self, sample_translate_response):
        response = sample_translate_response["translations"][0]
        result = Translation.from_api_response(response)
        assert result.type == "translation.translation"
        assert result.translated_text == "Bonjour le monde"
        assert result.detected_source_language == "en"
        assert result.model is not None

    def test_from_api_response_minimal(self):
        response = {"translatedText": "Hola"}
        result = Translation.from_api_response(response)
        assert result.translated_text == "Hola"
        assert result.detected_source_language is None
        assert result.model is None


# ---- DetectedLanguage Model Tests ----


class TestDetectedLanguageModel:
    def test_from_api_response(self, sample_detect_response):
        response = sample_detect_response["languages"][0]
        result = DetectedLanguage.from_api_response(response)
        assert result.type == "translation.detected_language"
        assert result.language_code == "en"
        assert result.confidence == 0.98

    def test_from_api_response_minimal(self):
        response = {"languageCode": "fr", "confidence": 0.5}
        result = DetectedLanguage.from_api_response(response)
        assert result.language_code == "fr"
        assert result.confidence == 0.5


# ---- TranslationService Translate Tests ----


class TestTranslationServiceTranslate:
    def test_translate_text(self, service, sample_translate_response):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.translateText().execute.return_value = (
            sample_translate_response
        )

        results = service.translate_text(
            contents=["Hello world"],
            target_language="fr",
        )
        assert len(results) == 1
        assert isinstance(results[0], Translation)
        assert results[0].translated_text == "Bonjour le monde"

    def test_translate_text_with_options(
        self, service, sample_translate_response
    ):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.translateText().execute.return_value = (
            sample_translate_response
        )

        results = service.translate_text(
            contents=["Hello world"],
            target_language="fr",
            source_language="en",
            model="projects/test-project/locations/global/models/general/nmt",
            mime_type="text/plain",
        )
        assert len(results) == 1
        assert isinstance(results[0], Translation)

    def test_translate_text_multiple(
        self, service
    ):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.translateText().execute.return_value = {
            "translations": [
                {"translatedText": "Bonjour"},
                {"translatedText": "Au revoir"},
            ]
        }

        results = service.translate_text(
            contents=["Hello", "Goodbye"],
            target_language="fr",
        )
        assert len(results) == 2
        assert results[0].translated_text == "Bonjour"
        assert results[1].translated_text == "Au revoir"

    def test_translate_text_api_error(self, service):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.translateText().execute.side_effect = (
            _make_http_error(400)
        )

        with pytest.raises(APIError):
            service.translate_text(
                contents=["Hello"],
                target_language="fr",
            )


# ---- TranslationService Detect Language Tests ----


class TestTranslationServiceDetectLanguage:
    def test_detect_language(self, service, sample_detect_response):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.detectLanguage().execute.return_value = (
            sample_detect_response
        )

        results = service.detect_language("Hello world")
        assert len(results) == 2
        assert isinstance(results[0], DetectedLanguage)
        assert results[0].language_code == "en"
        assert results[0].confidence == 0.98

    def test_detect_language_api_error(self, service):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.detectLanguage().execute.side_effect = (
            _make_http_error(500)
        )

        with pytest.raises(APIError):
            service.detect_language("Hello")


# ---- TranslationService Supported Languages Tests ----


class TestTranslationServiceSupportedLanguages:
    def test_get_supported_languages(
        self, service, sample_supported_languages_response
    ):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.getSupportedLanguages().execute.return_value = (
            sample_supported_languages_response
        )

        result = service.get_supported_languages()
        assert "languages" in result
        assert len(result["languages"]) == 2

    def test_get_supported_languages_with_display_code(
        self, service, sample_supported_languages_response
    ):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.getSupportedLanguages().execute.return_value = (
            sample_supported_languages_response
        )

        result = service.get_supported_languages(
            display_language_code="en"
        )
        assert "languages" in result

    def test_get_supported_languages_api_error(self, service):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.getSupportedLanguages().execute.side_effect = (
            _make_http_error(500)
        )

        with pytest.raises(APIError):
            service.get_supported_languages()


# ---- TranslationService Batch Translate Tests ----


class TestTranslationServiceBatchTranslate:
    def test_batch_translate_text(
        self, service, sample_batch_translate_response
    ):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.batchTranslateText().execute.return_value = (
            sample_batch_translate_response
        )

        result = service.batch_translate_text(
            source_language="en",
            target_languages=["fr", "de"],
            input_configs=[
                {
                    "gcsSource": {"inputUri": "gs://bucket/input.txt"},
                    "mimeType": "text/plain",
                }
            ],
            output_config={
                "gcsDestination": {
                    "outputUriPrefix": "gs://bucket/output/"
                }
            },
        )
        assert "name" in result
        assert "operations" in result["name"]

    def test_batch_translate_text_api_error(self, service):
        mock_locations = (
            service.service.projects().locations()
        )
        mock_locations.batchTranslateText().execute.side_effect = (
            _make_http_error(400)
        )

        with pytest.raises(APIError):
            service.batch_translate_text(
                source_language="en",
                target_languages=["fr"],
                input_configs=[{"gcsSource": {"inputUri": "gs://b/i.txt"}}],
                output_config={"gcsDestination": {"outputUriPrefix": "gs://b/o/"}},
            )


# ---- Service Initialization Tests ----


class TestTranslationServiceInit:
    def test_service_init(self, service):
        assert service.project_id == "test-project"
        assert service.service_name == "translate"
        assert service.version == "v3"
        assert service.resource_model == Translation

    def test_format_parent(self, service):
        assert service._format_parent() == (
            "projects/test-project/locations/global"
        )
