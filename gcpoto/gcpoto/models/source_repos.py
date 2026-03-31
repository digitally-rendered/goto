"""Models for Google Cloud Source Repositories resources."""

from typing import Dict, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.source_repos import get_schema


class Repo(GCPResource):
    """Model for a Google Cloud Source Repository."""

    size: Optional[int] = Field(
        None, description="The disk usage of the repo in bytes"
    )
    url: Optional[str] = Field(
        None, description="URL to clone the repository"
    )
    mirror_config: Optional[Dict[str, Any]] = Field(
        None, description="Mirror configuration for the repository"
    )
    pubsub_configs: Optional[Dict[str, Any]] = Field(
        None,
        description="Pub/Sub notification configurations",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("repo")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Repo":
        """Create a Repo from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Repo instance
        """
        name = response.get("name", "")
        parts = name.split("/")
        project = parts[1] if len(parts) > 1 else ""

        return cls(
            id=parts[-1] if parts else "",
            name=name,
            type="sourcerepo.repo",
            project=project,
            size=response.get("size"),
            url=response.get("url"),
            mirror_config=response.get("mirrorConfig"),
            pubsub_configs=response.get("pubsubConfigs"),
        )
