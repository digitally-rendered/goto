"""Tests for Video Intelligence AI service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.video_ai import VideoAIService
from gcpoto.models.video_ai import VideoAnnotationResult
from gcpoto.exceptions import ResourceNotFoundError, APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_videos = mock.MagicMock()
        mock_service.videos.return_value = mock_videos

        mock_operations = mock.MagicMock()
        mock_service.operations.return_value.projects.return_value.locations.return_value.operations.return_value = (
            mock_operations
        )

        yield mock_service


@pytest.fixture
def sample_annotation_response():
    """Sample Video Intelligence annotation API response."""
    return {
        "inputUri": "gs://my-bucket/video.mp4",
        "segmentLabelAnnotations": [
            {
                "entity": {"entityId": "/m/01yrx", "description": "cat"},
                "segments": [
                    {
                        "segment": {
                            "startTimeOffset": "0s",
                            "endTimeOffset": "10s",
                        },
                        "confidence": 0.95,
                    }
                ],
            }
        ],
        "shotLabelAnnotations": [
            {
                "entity": {"entityId": "/m/01yrx", "description": "cat"},
                "segments": [
                    {
                        "segment": {
                            "startTimeOffset": "0s",
                            "endTimeOffset": "5s",
                        },
                        "confidence": 0.92,
                    }
                ],
            }
        ],
        "shotAnnotations": [
            {
                "startTimeOffset": "0s",
                "endTimeOffset": "5.5s",
            }
        ],
        "explicitAnnotation": {
            "frames": [
                {"timeOffset": "1s", "pornographyLikelihood": "VERY_UNLIKELY"}
            ]
        },
        "textAnnotations": [
            {"text": "HELLO", "segments": []}
        ],
        "objectAnnotations": [
            {
                "entity": {"entityId": "/m/01yrx", "description": "cat"},
                "confidence": 0.88,
            }
        ],
    }


@pytest.fixture
def sample_operation_response():
    """Sample long-running operation response."""
    return {
        "name": "projects/test-project/locations/us-east1/operations/op123",
        "done": False,
        "metadata": {
            "@type": "type.googleapis.com/google.cloud.videointelligence.v1.AnnotateVideoProgress"
        },
    }


# --- Model tests ---


class TestVideoAnnotationResultModel:
    def test_from_api_response(self, sample_annotation_response):
        result = VideoAnnotationResult.from_api_response(
            sample_annotation_response, "test-project"
        )
        assert result.input_uri == "gs://my-bucket/video.mp4"
        assert result.project == "test-project"
        assert result.type == "videointelligence.annotationResult"
        assert len(result.segment_label_annotations) == 1
        assert len(result.shot_label_annotations) == 1
        assert len(result.shot_annotations) == 1
        assert result.explicit_annotation is not None
        assert len(result.text_annotations) == 1
        assert len(result.object_annotations) == 1

    def test_from_api_response_minimal(self):
        result = VideoAnnotationResult.from_api_response({}, "test-project")
        assert result.input_uri is None
        assert result.segment_label_annotations is None
        assert result.shot_label_annotations is None
        assert result.frame_label_annotations is None
        assert result.face_detection_annotations is None
        assert result.shot_annotations is None
        assert result.explicit_annotation is None
        assert result.speech_transcriptions is None
        assert result.text_annotations is None
        assert result.object_annotations is None

    def test_get_tag_default(self, sample_annotation_response):
        result = VideoAnnotationResult.from_api_response(
            sample_annotation_response, "test-project"
        )
        assert result.get_tag("missing") == ""
        assert result.get_tag("missing", "fallback") == "fallback"


# --- Service init tests ---


class TestVideoAIServiceInit:
    def test_init(self, mock_google_client):
        from googleapiclient.discovery import build

        service = VideoAIService(project_id="test-project")
        assert service.project_id == "test-project"
        build.assert_called_once_with(
            "videointelligence", "v1", credentials=None
        )


# --- Annotate video tests ---


class TestAnnotateVideo:
    def test_annotate_video(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        result = service.annotate_video(
            input_uri="gs://my-bucket/video.mp4",
            features=["LABEL_DETECTION", "SHOT_CHANGE_DETECTION"],
        )

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert body["inputUri"] == "gs://my-bucket/video.mp4"
        assert body["features"] == ["LABEL_DETECTION", "SHOT_CHANGE_DETECTION"]
        assert result == sample_operation_response

    def test_annotate_video_with_content(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        result = service.annotate_video(
            input_content="base64encodedcontent",
            features=["LABEL_DETECTION"],
        )

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert body["inputContent"] == "base64encodedcontent"
        assert "inputUri" not in body

    def test_annotate_video_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        service = VideoAIService(project_id="test-project")
        with pytest.raises(APIError):
            service.annotate_video(input_uri="gs://bad/uri")


# --- Detect labels tests ---


class TestDetectLabels:
    def test_detect_labels(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        result = service.detect_labels(input_uri="gs://my-bucket/video.mp4")

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert body["features"] == ["LABEL_DETECTION"]
        assert (
            body["videoContext"]["labelDetectionConfig"]["labelDetectionMode"]
            == "SHOT_AND_FRAME_MODE"
        )
        assert result == sample_operation_response

    def test_detect_labels_custom_mode(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        service.detect_labels(
            input_uri="gs://my-bucket/video.mp4",
            label_detection_mode="SHOT_MODE",
        )

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert (
            body["videoContext"]["labelDetectionConfig"]["labelDetectionMode"]
            == "SHOT_MODE"
        )


# --- Detect shots tests ---


class TestDetectShots:
    def test_detect_shots(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        result = service.detect_shots(input_uri="gs://my-bucket/video.mp4")

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert body["features"] == ["SHOT_CHANGE_DETECTION"]
        assert result == sample_operation_response


# --- Detect explicit content tests ---


class TestDetectExplicitContent:
    def test_detect_explicit_content(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        result = service.detect_explicit_content(
            input_uri="gs://my-bucket/video.mp4"
        )

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert body["features"] == ["EXPLICIT_CONTENT_DETECTION"]
        assert result == sample_operation_response


# --- Detect text tests ---


class TestDetectText:
    def test_detect_text(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        result = service.detect_text(input_uri="gs://my-bucket/video.mp4")

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert body["features"] == ["TEXT_DETECTION"]
        assert result == sample_operation_response


# --- Detect objects tests ---


class TestDetectObjects:
    def test_detect_objects(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        result = service.detect_objects(input_uri="gs://my-bucket/video.mp4")

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert body["features"] == ["OBJECT_TRACKING"]
        assert result == sample_operation_response


# --- Transcribe speech tests ---


class TestTranscribeSpeech:
    def test_transcribe_speech(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        result = service.transcribe_speech(
            input_uri="gs://my-bucket/video.mp4"
        )

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert body["features"] == ["SPEECH_TRANSCRIPTION"]
        assert (
            body["videoContext"]["speechTranscriptionConfig"]["languageCode"]
            == "en-US"
        )
        assert result == sample_operation_response

    def test_transcribe_speech_custom_language(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        service.transcribe_speech(
            input_uri="gs://my-bucket/video.mp4",
            language_code="fr-FR",
        )

        call_args = mock_annotate.call_args
        body = call_args[1]["body"]
        assert (
            body["videoContext"]["speechTranscriptionConfig"]["languageCode"]
            == "fr-FR"
        )

    def test_transcribe_speech_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_annotate = mock_google_client.videos.return_value.annotate
        mock_annotate.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        service = VideoAIService(project_id="test-project")
        with pytest.raises(APIError):
            service.transcribe_speech(input_uri="gs://bad/uri")


# --- Get operation tests ---


class TestGetOperation:
    def test_get_operation(
        self, mock_google_client, sample_operation_response
    ):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.operations.return_value.projects.return_value.locations.return_value.operations.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_operation_response

        service = VideoAIService(project_id="test-project")
        op_name = "projects/test-project/locations/us-east1/operations/op123"
        result = service.get_operation(op_name)

        mock_get.assert_called_once_with(name=op_name)
        assert result == sample_operation_response

    def test_get_operation_not_found(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.operations.return_value.projects.return_value.locations.return_value.operations.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = VideoAIService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_operation("projects/p/locations/l/operations/bad")

    def test_get_operation_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.operations.return_value.projects.return_value.locations.return_value.operations.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = VideoAIService(project_id="test-project")
        with pytest.raises(APIError):
            service.get_operation("projects/p/locations/l/operations/op1")
