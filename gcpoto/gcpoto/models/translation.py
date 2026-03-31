"""Models for Google Cloud Translation resources."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.translation import get_schema


class Translation(GCPResource):
    """Model for a Translation result."""

    translated_text: str = ""
    detected_source_language: Optional[str] = None
    model: Optional[str] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("translation")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "Translation":
        """Create a Translation from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Translation instance
        """
        return cls(
            id="",
            name="",
            type="translation.translation",
            project="",
            translated_text=response.get("translatedText", ""),
            detected_source_language=response.get("detectedLanguageCode"),
            model=response.get("model"),
        )


class DetectedLanguage(GCPResource):
    """Model for a detected language result."""

    language_code: str = ""
    confidence: float = 0.0

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("detected_language")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "DetectedLanguage":
        """Create a DetectedLanguage from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new DetectedLanguage instance
        """
        return cls(
            id="",
            name="",
            type="translation.detected_language",
            project="",
            language_code=response.get("languageCode", ""),
            confidence=response.get("confidence", 0.0),
        )
