"""Models for Google Cloud Speech-to-Text resources."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.speech import get_schema


class RecognitionConfig(BaseModel):
    """Configuration for speech recognition requests."""

    encoding: str = "LINEAR16"
    sample_rate_hertz: int = 16000
    language_code: str = "en-US"
    model: Optional[str] = None
    use_enhanced: bool = False


class RecognitionResult(GCPResource):
    """Model for a Speech-to-Text recognition result."""

    alternatives: List[Dict] = Field(default_factory=list)
    channel_tag: Optional[int] = None
    result_end_time: Optional[str] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("recognition_result")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "RecognitionResult":
        """Create a RecognitionResult from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new RecognitionResult instance
        """
        return cls(
            id="",
            name="",
            type="speech.recognition_result",
            project="",
            alternatives=response.get("alternatives", []),
            channel_tag=response.get("channelTag"),
            result_end_time=response.get("resultEndTime"),
        )
