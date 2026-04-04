"""Models for Google Cloud Data Fusion resources."""

from typing import Dict, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class DataFusionInstance(GCPResource):
    """Model for a Google Cloud Data Fusion Instance."""

    location: str = Field("", description="The location of the instance")
    type_field: str = Field(
        "", description="Instance type (BASIC, ENTERPRISE, DEVELOPER)"
    )
    description: Optional[str] = Field(
        None, description="Description of the instance"
    )
    enable_stackdriver_logging: bool = Field(
        False, description="Whether Stackdriver logging is enabled"
    )
    enable_stackdriver_monitoring: bool = Field(
        False, description="Whether Stackdriver monitoring is enabled"
    )
    private_instance: bool = Field(
        False, description="Whether the instance is private"
    )
    network_config: Optional[Dict[str, Any]] = Field(
        None, description="Network configuration for the instance"
    )
    state: str = Field("", description="The state of the instance")
    service_endpoint: Optional[str] = Field(
        None, description="The service endpoint URL"
    )
    api_endpoint: Optional[str] = Field(
        None, description="The API endpoint URL"
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
    ) -> "DataFusionInstance":
        """Create a DataFusionInstance from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new DataFusionInstance instance
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
            type="datafusion.instance",
            project=project_id,
            location=location,
            type_field=response.get("type", ""),
            description=response.get("description"),
            enable_stackdriver_logging=response.get(
                "enableStackdriverLogging", False
            ),
            enable_stackdriver_monitoring=response.get(
                "enableStackdriverMonitoring", False
            ),
            private_instance=response.get("privateInstance", False),
            network_config=response.get("networkConfig"),
            state=response.get("state", ""),
            service_endpoint=response.get("serviceEndpoint"),
            api_endpoint=response.get("apiEndpoint"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
