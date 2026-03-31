"""Models for Google Cloud Filestore resources."""

from typing import Dict, List, Optional, Any
from pydantic import ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.filestore import get_schema


class FilestoreInstance(GCPResource):
    """Model for a Google Cloud Filestore Instance."""

    location: str = Field("", description="The location of the instance")
    description: Optional[str] = Field(
        None, description="A description of the instance"
    )
    tier: str = Field(
        "",
        description="The service tier (BASIC_HDD, BASIC_SSD, HIGH_SCALE_SSD, ENTERPRISE)",
    )
    state: str = Field("", description="The current state of the instance")
    status_message: Optional[str] = Field(
        None, description="Additional status information about the instance"
    )
    file_shares: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="File shares configured on the instance",
    )
    networks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="VPC networks connected to the instance",
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("instance")}

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
    ) -> "FilestoreInstance":
        """Create a FilestoreInstance from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new FilestoreInstance instance
        """
        full_name = response.get("name", "")
        # Format: projects/{project}/locations/{location}/instances/{instance}
        parts = full_name.split("/")
        instance_name = parts[-1] if parts else ""
        location = ""

        if len(parts) >= 4:
            if not project_id:
                project_id = parts[1]
            location = parts[3]

        instance = cls(
            id=full_name,
            name=instance_name,
            type="filestore.instance",
            project=project_id,
            labels=response.get("labels"),
            location=location,
            description=response.get("description"),
            tier=response.get("tier", ""),
            state=response.get("state", ""),
            status_message=response.get("statusMessage"),
            file_shares=response.get("fileShares", []),
            networks=response.get("networks", []),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
