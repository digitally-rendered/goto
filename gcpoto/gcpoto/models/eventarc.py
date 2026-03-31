"""Models for Google Cloud Eventarc resources."""

from typing import Dict, List, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class EventarcTrigger(GCPResource):
    """Model for a Google Cloud Eventarc Trigger."""

    location: str = Field("", description="The location of the trigger")
    event_filters: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Event filters for matching events",
    )
    destination: Dict[str, Any] = Field(
        default_factory=dict,
        description="Destination for matched events",
    )
    transport: Optional[Dict[str, Any]] = Field(
        None, description="Transport configuration for the trigger"
    )
    service_account: Optional[str] = Field(
        None,
        description="The IAM service account email associated with the trigger",
    )
    channel: Optional[str] = Field(
        None, description="The channel associated with the trigger"
    )
    conditions: Optional[Dict[str, Any]] = Field(
        None, description="Conditions for the trigger"
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
    ) -> "EventarcTrigger":
        """Create an EventarcTrigger from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new EventarcTrigger instance
        """
        full_name = response.get("name", "")
        trigger_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID and location from the name
        # Format: projects/{project}/locations/{location}/triggers/{trigger}
        location = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 4:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]

        instance = cls(
            id=full_name,
            name=trigger_name,
            type="eventarc.trigger",
            project=project_id,
            location=location,
            event_filters=response.get("eventFilters", []),
            destination=response.get("destination", {}),
            transport=response.get("transport"),
            service_account=response.get("serviceAccount"),
            channel=response.get("channel"),
            conditions=response.get("conditions"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
