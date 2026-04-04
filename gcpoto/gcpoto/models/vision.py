"""Models for Google Cloud Vision AI resources."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.vision import get_schema


class AnnotationResult(GCPResource):
    """Model for a Vision AI annotation result."""

    labels: Optional[List[Dict]] = None
    faces: Optional[List[Dict]] = None
    text: Optional[Dict] = None
    objects: Optional[List[Dict]] = None
    logos: Optional[List[Dict]] = None
    landmarks: Optional[List[Dict]] = None
    safe_search: Optional[Dict] = None
    web_detection: Optional[Dict] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("annotation_result")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "AnnotationResult":
        """Create an AnnotationResult from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new AnnotationResult instance
        """
        return cls(
            id=response.get("context", {}).get("uri", ""),
            name=response.get("context", {}).get("uri", ""),
            type="vision.annotation_result",
            project="",
            labels=response.get("labelAnnotations"),
            faces=response.get("faceAnnotations"),
            text=response.get("fullTextAnnotation"),
            objects=response.get("localizedObjectAnnotations"),
            logos=response.get("logoAnnotations"),
            landmarks=response.get("landmarkAnnotations"),
            safe_search=response.get("safeSearchAnnotation"),
            web_detection=response.get("webDetection"),
        )
