"""Models for Google Cloud Profiler resources."""

from typing import Dict, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class Profile(GCPResource):
    """Model for a Google Cloud Profiler profile."""

    profile_type: str = Field(
        "",
        description="The type of profile (CPU, HEAP, THREADS, CONTENTION, WALL)",
    )
    deployment: Optional[Dict[str, Any]] = Field(
        None, description="Deployment information for the profile"
    )
    duration: Optional[str] = Field(
        None, description="Duration of the profile (e.g., '10s')"
    )
    profile_bytes: Optional[str] = Field(
        None, description="Base64-encoded profile data"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "Profile":
        """Create a Profile from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Profile instance
        """
        full_name = response.get("name", "")
        profile_name = (
            full_name.split("/")[-1] if "/" in full_name else full_name
        )

        # Extract project from name: projects/{project}/profiles/{profile_id}
        project_id = ""
        if "/" in full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        instance = cls(
            id=full_name or profile_name,
            name=profile_name,
            type="cloudprofiler.profile",
            project=project_id,
            profile_type=response.get("profileType", ""),
            deployment=response.get("deployment"),
            duration=response.get("duration"),
            profile_bytes=response.get("profileBytes"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
