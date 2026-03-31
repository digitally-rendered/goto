"""Models for Google Cloud Natural Language resources."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.natural_language import get_schema


class NLResult(GCPResource):
    """Model for a Natural Language analysis result."""

    sentences: Optional[List[Dict]] = None
    tokens: Optional[List[Dict]] = None
    entities: Optional[List[Dict]] = None
    sentiment: Optional[Dict] = None
    categories: Optional[List[Dict]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("nl_result")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "NLResult":
        """Create an NLResult from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new NLResult instance
        """
        return cls(
            id="",
            name="",
            type="natural_language.result",
            project="",
            sentences=response.get("sentences"),
            tokens=response.get("tokens"),
            entities=response.get("entities"),
            sentiment=response.get("documentSentiment"),
            categories=response.get("categories"),
        )
