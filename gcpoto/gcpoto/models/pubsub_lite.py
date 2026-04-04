"""Models for Google Cloud Pub/Sub Lite resources."""

from typing import Dict, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class LiteTopic(GCPResource):
    """Model for a Google Cloud Pub/Sub Lite Topic."""

    location: str = Field("", description="The location of the topic")
    partition_config: Dict[str, Any] = Field(
        default_factory=dict, description="Partition configuration"
    )
    retention_config: Dict[str, Any] = Field(
        default_factory=dict, description="Retention configuration"
    )
    reservation_config: Optional[Dict[str, Any]] = Field(
        None, description="Reservation configuration"
    )

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "LiteTopic":
        """Create a LiteTopic from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new LiteTopic instance
        """
        name = response.get("name", "")
        # name: projects/{p}/locations/{l}/topics/{id}
        parts = name.split("/")
        topic_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        return cls(
            id=topic_id,
            name=name,
            type="pubsublite.topic",
            project=project_id,
            location=location,
            partition_config=response.get("partitionConfig", {}),
            retention_config=response.get("retentionConfig", {}),
            reservation_config=response.get("reservationConfig"),
        )


class LiteSubscription(GCPResource):
    """Model for a Google Cloud Pub/Sub Lite Subscription."""

    location: str = Field("", description="The location of the subscription")
    topic: str = Field(
        "", description="The topic this subscription is attached to"
    )
    delivery_config: Optional[Dict[str, Any]] = Field(
        None, description="Delivery configuration"
    )

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "LiteSubscription":
        """Create a LiteSubscription from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new LiteSubscription instance
        """
        name = response.get("name", "")
        # name: projects/{p}/locations/{l}/subscriptions/{id}
        parts = name.split("/")
        sub_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        return cls(
            id=sub_id,
            name=name,
            type="pubsublite.subscription",
            project=project_id,
            location=location,
            topic=response.get("topic", ""),
            delivery_config=response.get("deliveryConfig"),
        )
