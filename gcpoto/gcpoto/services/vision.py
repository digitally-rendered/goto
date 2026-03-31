"""Service implementation for Google Cloud Vision AI."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.vision import AnnotationResult
from gcpoto.exceptions import (
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class VisionService(GCPService[AnnotationResult]):
    """Service for interacting with Google Cloud Vision AI."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Vision AI service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="vision",
            version="v1",
            credentials_file=credentials_file,
            resource_model=AnnotationResult,
            **kwargs,
        )

    def _build_image(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build the image object for an annotation request.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content

        Returns:
            A dictionary representing the image source
        """
        image: Dict[str, Any] = {}
        if image_uri is not None:
            image["source"] = {"imageUri": image_uri}
        if image_content is not None:
            image["content"] = image_content
        return image

    def annotate_image(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
        features: Optional[List[Dict[str, Any]]] = None,
    ) -> AnnotationResult:
        """Annotate an image with the specified features.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content
            features: List of feature dicts with 'type' and optional 'maxResults'

        Returns:
            An AnnotationResult instance
        """
        logger.debug(
            "Annotating image for project %s", self.project_id
        )

        image = self._build_image(image_uri, image_content)
        body = {
            "requests": [
                {
                    "image": image,
                    "features": features or [],
                }
            ]
        }

        try:
            request = self.service.images().annotate(body=body)
            response = request.execute()
            results = response.get("responses", [{}])
            return AnnotationResult.from_api_response(results[0])
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def detect_labels(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
        max_results: int = 10,
    ) -> AnnotationResult:
        """Detect labels in an image.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content
            max_results: Maximum number of results to return

        Returns:
            An AnnotationResult instance with label annotations
        """
        logger.debug("Detecting labels for project %s", self.project_id)

        features = [{"type": "LABEL_DETECTION", "maxResults": max_results}]
        return self.annotate_image(
            image_uri=image_uri,
            image_content=image_content,
            features=features,
        )

    def detect_faces(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
        max_results: int = 10,
    ) -> AnnotationResult:
        """Detect faces in an image.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content
            max_results: Maximum number of results to return

        Returns:
            An AnnotationResult instance with face annotations
        """
        logger.debug("Detecting faces for project %s", self.project_id)

        features = [{"type": "FACE_DETECTION", "maxResults": max_results}]
        return self.annotate_image(
            image_uri=image_uri,
            image_content=image_content,
            features=features,
        )

    def detect_text(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
    ) -> AnnotationResult:
        """Detect text in an image.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content

        Returns:
            An AnnotationResult instance with text annotations
        """
        logger.debug("Detecting text for project %s", self.project_id)

        features = [{"type": "DOCUMENT_TEXT_DETECTION"}]
        return self.annotate_image(
            image_uri=image_uri,
            image_content=image_content,
            features=features,
        )

    def detect_objects(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
        max_results: int = 10,
    ) -> AnnotationResult:
        """Detect objects in an image.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content
            max_results: Maximum number of results to return

        Returns:
            An AnnotationResult instance with object annotations
        """
        logger.debug("Detecting objects for project %s", self.project_id)

        features = [
            {"type": "OBJECT_LOCALIZATION", "maxResults": max_results}
        ]
        return self.annotate_image(
            image_uri=image_uri,
            image_content=image_content,
            features=features,
        )

    def detect_logos(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
    ) -> AnnotationResult:
        """Detect logos in an image.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content

        Returns:
            An AnnotationResult instance with logo annotations
        """
        logger.debug("Detecting logos for project %s", self.project_id)

        features = [{"type": "LOGO_DETECTION"}]
        return self.annotate_image(
            image_uri=image_uri,
            image_content=image_content,
            features=features,
        )

    def detect_landmarks(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
    ) -> AnnotationResult:
        """Detect landmarks in an image.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content

        Returns:
            An AnnotationResult instance with landmark annotations
        """
        logger.debug("Detecting landmarks for project %s", self.project_id)

        features = [{"type": "LANDMARK_DETECTION"}]
        return self.annotate_image(
            image_uri=image_uri,
            image_content=image_content,
            features=features,
        )

    def detect_safe_search(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
    ) -> AnnotationResult:
        """Detect safe search annotations in an image.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content

        Returns:
            An AnnotationResult instance with safe search annotations
        """
        logger.debug(
            "Detecting safe search for project %s", self.project_id
        )

        features = [{"type": "SAFE_SEARCH_DETECTION"}]
        return self.annotate_image(
            image_uri=image_uri,
            image_content=image_content,
            features=features,
        )

    def detect_web(
        self,
        image_uri: Optional[str] = None,
        image_content: Optional[str] = None,
    ) -> AnnotationResult:
        """Detect web references for an image.

        Args:
            image_uri: URI of the image (GCS or public URL)
            image_content: Base64-encoded image content

        Returns:
            An AnnotationResult instance with web detection results
        """
        logger.debug(
            "Detecting web references for project %s", self.project_id
        )

        features = [{"type": "WEB_DETECTION"}]
        return self.annotate_image(
            image_uri=image_uri,
            image_content=image_content,
            features=features,
        )
