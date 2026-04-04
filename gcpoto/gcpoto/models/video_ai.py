"""Models for Google Cloud Video Intelligence AI resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.video_ai import get_schema


class VideoAnnotationResult(GCPResource):
    """Model for a Google Cloud Video Intelligence annotation result."""

    input_uri: Optional[str] = Field(
        None, description="The video input URI"
    )
    segment_label_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Label annotations on video level"
    )
    shot_label_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Label annotations on shot level"
    )
    frame_label_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Label annotations on frame level"
    )
    face_detection_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Face detection annotations"
    )
    shot_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Shot annotations (scene changes)"
    )
    explicit_annotation: Optional[Dict[str, Any]] = Field(
        None, description="Explicit content annotation"
    )
    speech_transcriptions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Speech transcription results"
    )
    text_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="OCR text detection annotations"
    )
    object_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Object tracking annotations"
    )
    _tags: Optional[Dict[str, str]] = None

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("annotation_result")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "VideoAnnotationResult":
        """Create a VideoAnnotationResult from an API response.

        Args:
            response: The API response dictionary (an annotationResult)
            project_id: The GCP project ID

        Returns:
            A new VideoAnnotationResult instance
        """
        input_uri = response.get("inputUri", "")

        instance = cls(
            id=input_uri or "",
            name=input_uri or "",
            type="videointelligence.annotationResult",
            project=project_id,
            input_uri=response.get("inputUri"),
            segment_label_annotations=response.get("segmentLabelAnnotations"),
            shot_label_annotations=response.get("shotLabelAnnotations"),
            frame_label_annotations=response.get("frameLabelAnnotations"),
            face_detection_annotations=response.get("faceDetectionAnnotations"),
            shot_annotations=response.get("shotAnnotations"),
            explicit_annotation=response.get("explicitAnnotation"),
            speech_transcriptions=response.get("speechTranscriptions"),
            text_annotations=response.get("textAnnotations"),
            object_annotations=response.get("objectAnnotations"),
        )

        return instance
