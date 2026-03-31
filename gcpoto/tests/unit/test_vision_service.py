"""Tests for Vision AI service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.vision import VisionService
from gcpoto.models.vision import AnnotationResult
from gcpoto.exceptions import APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_images = mock.MagicMock()
        mock_service.images.return_value = mock_images

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a VisionService with mocked client."""
    return VisionService(project_id="test-project")


@pytest.fixture
def sample_annotate_response():
    """Sample Vision AI annotate API response."""
    return {
        "responses": [
            {
                "labelAnnotations": [
                    {
                        "mid": "/m/01yrx",
                        "description": "cat",
                        "score": 0.99,
                        "topicality": 0.99,
                    }
                ],
                "faceAnnotations": [
                    {
                        "boundingPoly": {"vertices": [{"x": 1, "y": 1}]},
                        "detectionConfidence": 0.95,
                        "joyLikelihood": "VERY_LIKELY",
                    }
                ],
                "fullTextAnnotation": {
                    "text": "Hello World",
                    "pages": [],
                },
                "localizedObjectAnnotations": [
                    {
                        "mid": "/m/01yrx",
                        "name": "Cat",
                        "score": 0.97,
                        "boundingPoly": {},
                    }
                ],
                "logoAnnotations": [
                    {
                        "mid": "/m/045c7b",
                        "description": "Google",
                        "score": 0.85,
                        "boundingPoly": {},
                    }
                ],
                "landmarkAnnotations": [
                    {
                        "mid": "/m/02j81",
                        "description": "Eiffel Tower",
                        "score": 0.92,
                        "locations": [
                            {
                                "latLng": {
                                    "latitude": 48.8584,
                                    "longitude": 2.2945,
                                }
                            }
                        ],
                    }
                ],
                "safeSearchAnnotation": {
                    "adult": "VERY_UNLIKELY",
                    "spoof": "UNLIKELY",
                    "medical": "VERY_UNLIKELY",
                    "violence": "VERY_UNLIKELY",
                    "racy": "VERY_UNLIKELY",
                },
                "webDetection": {
                    "webEntities": [
                        {
                            "entityId": "/m/01yrx",
                            "score": 0.88,
                            "description": "Cat",
                        }
                    ],
                    "fullMatchingImages": [],
                    "pagesWithMatchingImages": [],
                },
            }
        ]
    }


def _make_http_error(status_code, reason="error"):
    """Create a mock HttpError with the given status code."""
    resp = mock.MagicMock()
    resp.status = status_code
    return HttpError(
        resp, b'{"error": {"message": "' + reason.encode() + b'"}}'
    )


# ---- AnnotationResult Model Tests ----


class TestAnnotationResultModel:
    def test_from_api_response(self, sample_annotate_response):
        response = sample_annotate_response["responses"][0]
        result = AnnotationResult.from_api_response(response)
        assert result.type == "vision.annotation_result"
        assert result.labels is not None
        assert len(result.labels) == 1
        assert result.labels[0]["description"] == "cat"
        assert result.faces is not None
        assert len(result.faces) == 1
        assert result.text is not None
        assert result.text["text"] == "Hello World"
        assert result.objects is not None
        assert result.logos is not None
        assert result.landmarks is not None
        assert result.safe_search is not None
        assert result.web_detection is not None

    def test_from_api_response_minimal(self):
        response = {}
        result = AnnotationResult.from_api_response(response)
        assert result.type == "vision.annotation_result"
        assert result.labels is None
        assert result.faces is None
        assert result.text is None
        assert result.objects is None


# ---- VisionService Tests ----


class TestVisionServiceAnnotate:
    def test_annotate_image(self, service, sample_annotate_response):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.annotate_image(
            image_uri="gs://bucket/image.jpg",
            features=[{"type": "LABEL_DETECTION", "maxResults": 5}],
        )
        assert isinstance(result, AnnotationResult)
        assert result.labels is not None
        assert result.labels[0]["description"] == "cat"

    def test_annotate_image_with_content(
        self, service, sample_annotate_response
    ):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.annotate_image(
            image_content="base64encodedcontent",
            features=[{"type": "LABEL_DETECTION"}],
        )
        assert isinstance(result, AnnotationResult)

    def test_annotate_image_api_error(self, service):
        mock_images = service.service.images()
        mock_images.annotate().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.annotate_image(
                image_uri="gs://bucket/image.jpg",
                features=[{"type": "LABEL_DETECTION"}],
            )


class TestVisionServiceDetectLabels:
    def test_detect_labels(self, service, sample_annotate_response):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.detect_labels(image_uri="gs://bucket/image.jpg")
        assert isinstance(result, AnnotationResult)
        assert result.labels is not None

    def test_detect_labels_with_max_results(
        self, service, sample_annotate_response
    ):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.detect_labels(
            image_uri="gs://bucket/image.jpg", max_results=5
        )
        assert isinstance(result, AnnotationResult)


class TestVisionServiceDetectFaces:
    def test_detect_faces(self, service, sample_annotate_response):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.detect_faces(image_uri="gs://bucket/image.jpg")
        assert isinstance(result, AnnotationResult)
        assert result.faces is not None


class TestVisionServiceDetectText:
    def test_detect_text(self, service, sample_annotate_response):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.detect_text(image_uri="gs://bucket/image.jpg")
        assert isinstance(result, AnnotationResult)
        assert result.text is not None


class TestVisionServiceDetectObjects:
    def test_detect_objects(self, service, sample_annotate_response):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.detect_objects(image_uri="gs://bucket/image.jpg")
        assert isinstance(result, AnnotationResult)
        assert result.objects is not None


class TestVisionServiceDetectLogos:
    def test_detect_logos(self, service, sample_annotate_response):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.detect_logos(image_uri="gs://bucket/image.jpg")
        assert isinstance(result, AnnotationResult)
        assert result.logos is not None


class TestVisionServiceDetectLandmarks:
    def test_detect_landmarks(self, service, sample_annotate_response):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.detect_landmarks(image_uri="gs://bucket/image.jpg")
        assert isinstance(result, AnnotationResult)
        assert result.landmarks is not None


class TestVisionServiceDetectSafeSearch:
    def test_detect_safe_search(self, service, sample_annotate_response):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.detect_safe_search(
            image_uri="gs://bucket/image.jpg"
        )
        assert isinstance(result, AnnotationResult)
        assert result.safe_search is not None


class TestVisionServiceDetectWeb:
    def test_detect_web(self, service, sample_annotate_response):
        mock_images = service.service.images()
        mock_images.annotate().execute.return_value = (
            sample_annotate_response
        )

        result = service.detect_web(image_uri="gs://bucket/image.jpg")
        assert isinstance(result, AnnotationResult)
        assert result.web_detection is not None


class TestVisionServiceInit:
    def test_service_init(self, service):
        assert service.project_id == "test-project"
        assert service.service_name == "vision"
        assert service.version == "v1"
        assert service.resource_model == AnnotationResult
