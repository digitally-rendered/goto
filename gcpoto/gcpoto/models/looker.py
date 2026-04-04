"""Models for Google Cloud Looker resources."""

from typing import Dict, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class LookerInstance(GCPResource):
    """Model for a Google Cloud Looker Instance."""

    location: str = Field("", description="The location of the instance")
    platform_edition: str = Field(
        "", description="Platform edition (STANDARD, ADVANCED, ELITE)"
    )
    state: str = Field("", description="The state of the instance")
    looker_uri: Optional[str] = Field(
        None, description="The Looker instance URI"
    )
    admin_settings: Optional[Dict[str, Any]] = Field(
        None, description="Admin settings for the instance"
    )
    maintenance_window: Optional[Dict[str, Any]] = Field(
        None, description="Maintenance window configuration"
    )
    deny_maintenance_period: Optional[Dict[str, Any]] = Field(
        None, description="Deny maintenance period configuration"
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
    ) -> "LookerInstance":
        """Create a LookerInstance from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new LookerInstance instance
        """
        name = response.get("name", "")
        # name: projects/{p}/locations/{l}/instances/{id}
        parts = name.split("/")
        instance_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        instance = cls(
            id=instance_id,
            name=name,
            type="looker.instance",
            project=project_id,
            location=location,
            platform_edition=response.get("platformEdition", ""),
            state=response.get("state", ""),
            looker_uri=response.get("lookerUri"),
            admin_settings=response.get("adminSettings"),
            maintenance_window=response.get("maintenanceWindow"),
            deny_maintenance_period=response.get(
                "denyMaintenancePeriod"
            ),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
