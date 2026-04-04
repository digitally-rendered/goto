"""Models for Google Cloud Composer resources."""

from typing import Dict, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class ComposerEnvironment(GCPResource):
    """Model for a Google Cloud Composer Environment."""

    location: str = Field("", description="The location of the environment")
    state: str = Field("", description="The state of the environment")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Environment configuration"
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

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "ComposerEnvironment":
        """Create a ComposerEnvironment from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new ComposerEnvironment instance
        """
        name = response.get("name", "")
        # name: projects/{p}/locations/{l}/environments/{id}
        parts = name.split("/")
        env_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        instance = cls(
            id=env_id,
            name=name,
            type="composer.environment",
            project=project_id,
            location=location,
            state=response.get("state", ""),
            config=response.get("config", {}),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
