"""Tests for Speech-to-Text service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.speech import SpeechService
from gcpoto.models.speech import RecognitionResult, RecognitionConfig
from gcpoto.exceptions import APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_speech = mock.MagicMock()
        mock_service.speech.return_value = mock_speech

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a SpeechService with mocked client."""
    return SpeechService(project_id="test-project")


@pytest.fixture
def sample_recognize_response():
    """Sample Speech-to-Text recognize API response."""
    return {
        "results": [
            {
                "alternatives": [
                    {
                        "transcript": "hello world",
                        "confidence": 0.98,
                        "words": [
                            {
                                "startTime": "0s",
                                "endTime": "0.5s",
                                "word": "hello",
                            },
                            {
                                "startTime": "0.5s",
                                "endTime": "1s",
                                "word": "world",
                            },
                        ],
                    }
                ],
                "channelTag": 1,
                "resultEndTime": "1.5s",
            }
        ]
    }


@pytest.fixture
def sample_long_running_response():
    """Sample Speech-to-Text long-running recognize API response."""
    return {
        "name": "operations/12345",
        "metadata": {
            "@type": "type.googleapis.com/google.cloud.speech.v1.LongRunningRecognizeMetadata",
            "progressPercent": 100,
        },
        "done": True,
        "response": {
            "results": [
                {
                    "alternatives": [
                        {
                            "transcript": "hello world",
                            "confidence": 0.98,
                        }
                    ]
                }
            ]
        },
    }


def _make_http_error(status_code, reason="error"):
    """Create a mock HttpError with the given status code."""
    resp = mock.MagicMock()
    resp.status = status_code
    return HttpError(
        resp, b'{"error": {"message": "' + reason.encode() + b'"}}'
    )


# ---- RecognitionResult Model Tests ----


class TestRecognitionResultModel:
    def test_from_api_response(self, sample_recognize_response):
        response = sample_recognize_response["results"][0]
        result = RecognitionResult.from_api_response(response)
        assert result.type == "speech.recognition_result"
        assert len(result.alternatives) == 1
        assert result.alternatives[0]["transcript"] == "hello world"
        assert result.alternatives[0]["confidence"] == 0.98
        assert result.channel_tag == 1
        assert result.result_end_time == "1.5s"

    def test_from_api_response_minimal(self):
        response = {"alternatives": [{"transcript": "test"}]}
        result = RecognitionResult.from_api_response(response)
        assert result.type == "speech.recognition_result"
        assert len(result.alternatives) == 1
        assert result.channel_tag is None
        assert result.result_end_time is None


# ---- RecognitionConfig Model Tests ----


class TestRecognitionConfigModel:
    def test_default_config(self):
        config = RecognitionConfig()
        assert config.encoding == "LINEAR16"
        assert config.sample_rate_hertz == 16000
        assert config.language_code == "en-US"
        assert config.model is None
        assert config.use_enhanced is False

    def test_custom_config(self):
        config = RecognitionConfig(
            encoding="FLAC",
            sample_rate_hertz=44100,
            language_code="fr-FR",
            model="phone_call",
            use_enhanced=True,
        )
        assert config.encoding == "FLAC"
        assert config.sample_rate_hertz == 44100
        assert config.language_code == "fr-FR"
        assert config.model == "phone_call"
        assert config.use_enhanced is True


# ---- SpeechService Recognize Tests ----


class TestSpeechServiceRecognize:
    def test_recognize_with_uri(self, service, sample_recognize_response):
        mock_speech = service.service.speech()
        mock_speech.recognize().execute.return_value = (
            sample_recognize_response
        )

        results = service.recognize(
            audio_uri="gs://bucket/audio.wav",
        )
        assert len(results) == 1
        assert isinstance(results[0], RecognitionResult)
        assert results[0].alternatives[0]["transcript"] == "hello world"

    def test_recognize_with_content(self, service, sample_recognize_response):
        mock_speech = service.service.speech()
        mock_speech.recognize().execute.return_value = (
            sample_recognize_response
        )

        results = service.recognize(
            audio_content="base64encodedaudio",
            encoding="FLAC",
            sample_rate_hertz=44100,
            language_code="fr-FR",
        )
        assert len(results) == 1
        assert isinstance(results[0], RecognitionResult)

    def test_recognize_with_config(self, service, sample_recognize_response):
        mock_speech = service.service.speech()
        mock_speech.recognize().execute.return_value = (
            sample_recognize_response
        )

        config = RecognitionConfig(
            encoding="FLAC",
            sample_rate_hertz=44100,
            language_code="de-DE",
            model="phone_call",
            use_enhanced=True,
        )
        results = service.recognize(
            audio_uri="gs://bucket/audio.flac",
            config=config,
        )
        assert len(results) == 1

    def test_recognize_empty_results(self, service):
        mock_speech = service.service.speech()
        mock_speech.recognize().execute.return_value = {}

        results = service.recognize(audio_uri="gs://bucket/silence.wav")
        assert len(results) == 0

    def test_recognize_api_error(self, service):
        mock_speech = service.service.speech()
        mock_speech.recognize().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.recognize(audio_uri="gs://bucket/audio.wav")


# ---- SpeechService Long Running Recognize Tests ----


class TestSpeechServiceLongRunningRecognize:
    def test_long_running_recognize(
        self, service, sample_long_running_response
    ):
        mock_speech = service.service.speech()
        mock_speech.longrunningrecognize().execute.return_value = (
            sample_long_running_response
        )

        result = service.long_running_recognize(
            audio_uri="gs://bucket/long-audio.wav",
        )
        assert result["name"] == "operations/12345"
        assert result["done"] is True

    def test_long_running_recognize_with_config(
        self, service, sample_long_running_response
    ):
        mock_speech = service.service.speech()
        mock_speech.longrunningrecognize().execute.return_value = (
            sample_long_running_response
        )

        config = RecognitionConfig(
            encoding="FLAC",
            sample_rate_hertz=44100,
            language_code="ja-JP",
        )
        result = service.long_running_recognize(
            audio_uri="gs://bucket/long-audio.flac",
            config=config,
        )
        assert isinstance(result, dict)

    def test_long_running_recognize_api_error(self, service):
        mock_speech = service.service.speech()
        mock_speech.longrunningrecognize().execute.side_effect = (
            _make_http_error(500)
        )

        with pytest.raises(APIError):
            service.long_running_recognize(
                audio_uri="gs://bucket/audio.wav"
            )


# ---- Service Initialization Tests ----


class TestSpeechServiceInit:
    def test_service_init(self, service):
        assert service.project_id == "test-project"
        assert service.service_name == "speech"
        assert service.version == "v1"
        assert service.resource_model == RecognitionResult
