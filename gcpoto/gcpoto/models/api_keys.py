"""Models for Google Cloud API Keys resources."""

from typing import Dict, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.api_keys import get_schema


class APIKey(GCPResource):
    """Model for a Google Cloud API Key."""

    location: str = Field("", description="The location of the API key")
    display_name: Optional[str] = Field(
        None, description="Human-readable display name of the key"
    )
    key_string: Optional[str] = Field(
        None, description="The API key string (only returned on creation)"
    )
    restrictions: Optional[Dict] = Field(
        None, description="Key restrictions"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("api_key")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "APIKey":
        """Create an APIKey from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new APIKey instance
        """
        name = response.get("name", "")
        # Extract the key ID from the full resource name
        # Format: projects/{project}/locations/{location}/keys/{key_id}
        key_id = name.rsplit("/", 1)[-1] if "/" in name else name

        instance = cls(
            id=response.get("uid", key_id),
            name=name,
            type="apikeys.key",
            project=response.get("project", ""),
            location=response.get("location", ""),
            display_name=response.get("displayName"),
            key_string=response.get("keyString"),
            restrictions=response.get("restrictions"),
            labels=response.get("annotations"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("annotations"):
            instance._tags = response["annotations"]
        return instance

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
