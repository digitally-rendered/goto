"""Service implementation for Google Cloud Video Intelligence AI."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.video_ai import VideoAnnotationResult
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class VideoAIService(GCPService[VideoAnnotationResult]):
    """Service for interacting with Google Cloud Video Intelligence AI."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Video Intelligence AI service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="videointelligence",
            version="v1",
            credentials_file=credentials_file,
            resource_model=VideoAnnotationResult,
            **kwargs,
        )

    def annotate_video(
        self,
        input_uri: Optional[str] = None,
        input_content: Optional[str] = None,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Annotate a video with specified features.

        Args:
            input_uri: Cloud Storage URI of the video (gs://...)
            input_content: Base64-encoded video content
            features: List of feature strings (e.g. LABEL_DETECTION,
                SHOT_CHANGE_DETECTION, EXPLICIT_CONTENT_DETECTION,
                TEXT_DETECTION, OBJECT_TRACKING, SPEECH_TRANSCRIPTION)

        Returns:
            The long-running operation response dict

        Raises:
            APIError: If the API call fails
        """
        logger.debug(
            "Annotating video with features %s in project %s",
            features,
            self.project_id,
        )

        body: Dict[str, Any] = {}
        if input_uri is not None:
            body["inputUri"] = input_uri
        if input_content is not None:
            body["inputContent"] = input_content
        if features is not None:
            body["features"] = features

        try:
            request = self.service.videos().annotate(body=body)
            return request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e)) from e

    def detect_labels(
        self,
        input_uri: Optional[str] = None,
        input_content: Optional[str] = None,
        label_detection_mode: str = "SHOT_AND_FRAME_MODE",
    ) -> Dict[str, Any]:
        """Detect labels in a video.

        Args:
            input_uri: Cloud Storage URI of the video
            input_content: Base64-encoded video content
            label_detection_mode: Detection mode (SHOT_MODE, FRAME_MODE,
                or SHOT_AND_FRAME_MODE)

        Returns:
            The long-running operation response dict

        Raises:
            APIError: If the API call fails
        """
        logger.debug(
            "Detecting labels with mode %s in project %s",
            label_detection_mode,
            self.project_id,
        )

        body: Dict[str, Any] = {
            "features": ["LABEL_DETECTION"],
            "videoContext": {
                "labelDetectionConfig": {
                    "labelDetectionMode": label_detection_mode,
                },
            },
        }
        if input_uri is not None:
            body["inputUri"] = input_uri
        if input_content is not None:
            body["inputContent"] = input_content

        try:
            request = self.service.videos().annotate(body=body)
            return request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e)) from e

    def detect_shots(
        self,
        input_uri: Optional[str] = None,
        input_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Detect shot changes in a video.

        Args:
            input_uri: Cloud Storage URI of the video
            input_content: Base64-encoded video content

        Returns:
            The long-running operation response dict

        Raises:
            APIError: If the API call fails
        """
        logger.debug("Detecting shots in project %s", self.project_id)

        body: Dict[str, Any] = {"features": ["SHOT_CHANGE_DETECTION"]}
        if input_uri is not None:
            body["inputUri"] = input_uri
        if input_content is not None:
            body["inputContent"] = input_content

        try:
            request = self.service.videos().annotate(body=body)
            return request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e)) from e

    def detect_explicit_content(
        self,
        input_uri: Optional[str] = None,
        input_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Detect explicit content in a video.

        Args:
            input_uri: Cloud Storage URI of the video
            input_content: Base64-encoded video content

        Returns:
            The long-running operation response dict

        Raises:
            APIError: If the API call fails
        """
        logger.debug(
            "Detecting explicit content in project %s", self.project_id
        )

        body: Dict[str, Any] = {"features": ["EXPLICIT_CONTENT_DETECTION"]}
        if input_uri is not None:
            body["inputUri"] = input_uri
        if input_content is not None:
            body["inputContent"] = input_content

        try:
            request = self.service.videos().annotate(body=body)
            return request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e)) from e

    def detect_text(
        self,
        input_uri: Optional[str] = None,
        input_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Detect text (OCR) in a video.

        Args:
            input_uri: Cloud Storage URI of the video
            input_content: Base64-encoded video content

        Returns:
            The long-running operation response dict

        Raises:
            APIError: If the API call fails
        """
        logger.debug("Detecting text in project %s", self.project_id)

        body: Dict[str, Any] = {"features": ["TEXT_DETECTION"]}
        if input_uri is not None:
            body["inputUri"] = input_uri
        if input_content is not None:
            body["inputContent"] = input_content

        try:
            request = self.service.videos().annotate(body=body)
            return request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e)) from e

    def detect_objects(
        self,
        input_uri: Optional[str] = None,
        input_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Detect and track objects in a video.

        Args:
            input_uri: Cloud Storage URI of the video
            input_content: Base64-encoded video content

        Returns:
            The long-running operation response dict

        Raises:
            APIError: If the API call fails
        """
        logger.debug("Detecting objects in project %s", self.project_id)

        body: Dict[str, Any] = {"features": ["OBJECT_TRACKING"]}
        if input_uri is not None:
            body["inputUri"] = input_uri
        if input_content is not None:
            body["inputContent"] = input_content

        try:
            request = self.service.videos().annotate(body=body)
            return request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e)) from e

    def transcribe_speech(
        self,
        input_uri: Optional[str] = None,
        input_content: Optional[str] = None,
        language_code: str = "en-US",
    ) -> Dict[str, Any]:
        """Transcribe speech in a video.

        Args:
            input_uri: Cloud Storage URI of the video
            input_content: Base64-encoded video content
            language_code: BCP-47 language code for transcription

        Returns:
            The long-running operation response dict

        Raises:
            APIError: If the API call fails
        """
        logger.debug(
            "Transcribing speech with language %s in project %s",
            language_code,
            self.project_id,
        )

        body: Dict[str, Any] = {
            "features": ["SPEECH_TRANSCRIPTION"],
            "videoContext": {
                "speechTranscriptionConfig": {
                    "languageCode": language_code,
                },
            },
        }
        if input_uri is not None:
            body["inputUri"] = input_uri
        if input_content is not None:
            body["inputContent"] = input_content

        try:
            request = self.service.videos().annotate(body=body)
            return request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e)) from e

    def get_operation(self, operation_name: str) -> Dict[str, Any]:
        """Get the status of a long-running operation.

        Args:
            operation_name: The operation resource name

        Returns:
            The operation response dict

        Raises:
            ResourceNotFoundError: If the operation does not exist
            APIError: If the API call fails
        """
        logger.debug("Getting operation %s", operation_name)

        try:
            request = self.service.operations().projects().locations().operations().get(
                name=operation_name
            )
            return request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "videointelligence.operation", operation_name
                ) from e
            raise APIError(e.resp.status, str(e)) from e
