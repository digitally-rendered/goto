"""Models for Google Cloud Pub/Sub resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.pubsub import get_schema


class MessageStoragePolicy(BaseModel):
    """Message storage policy for a Pub/Sub topic."""

    allowed_persistence_regions: List[str] = Field(
        default_factory=list, description="List of regions where messages can be stored"
    )


class SchemaSettings(BaseModel):
    """Schema settings for a Pub/Sub topic."""

    schema: str = Field(
        ...,
        description="The name of the schema that messages should be validated against",
    )
    encoding: str = Field(
        ..., description="The encoding of the messages validated against the schema"
    )


class PubSubTopic(GCPResource):
    """Model for a Google Cloud Pub/Sub Topic."""

    kms_key_name: Optional[str] = Field(
        None,
        description="The KMS key used to protect access to messages published on this topic",
    )
    message_storage_policy: Optional[MessageStoragePolicy] = Field(
        None, description="Policy constraining the regions where messages can be stored"
    )
    schema_settings: Optional[SchemaSettings] = Field(
        None,
        description="Settings for schema validation of messages published to the topic",
    )
    message_retention_duration: Optional[str] = Field(
        None,
        description="The duration for which messages are retained (in ISO 8601 duration format)",
    )
    satisfies_pzs: Optional[bool] = Field(
        None,
        description="Whether this topic satisfies the requirements for Assured Workloads",
    )
    _tags: Optional[Dict[str, str]] = None

    def get_tag(self, key: str, default: Any = None) -> Any:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        # First check explicit tags, then fall back to labels
        if self._tags and key in self._tags:
            return self._tags[key]
        elif self.labels and key in self.labels:
            return self.labels[key]
        else:
            return default

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("topic")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "PubSubTopic":
        """Create a PubSubTopic from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new PubSubTopic instance
        """
        # The API returns the full topic name in the format: projects/{project}/topics/{topic}
        # We need to extract just the topic name part
        full_name = response.get("name", "")
        topic_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID from the name if not provided
        if not project_id and full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        # Extract message storage policy if present
        message_storage_policy = None
        if response.get("messageStoragePolicy"):
            regions = response.get("messageStoragePolicy", {}).get(
                "allowedPersistenceRegions", []
            )
            message_storage_policy = MessageStoragePolicy(
                allowed_persistence_regions=regions
            )

        # Extract schema settings if present
        schema_settings = None
        if response.get("schemaSettings"):
            schema = response.get("schemaSettings", {}).get("schema", "")
            encoding = response.get("schemaSettings", {}).get("encoding", "")
            if schema and encoding:
                schema_settings = SchemaSettings(schema=schema, encoding=encoding)

        instance = cls(
            id=full_name,  # Use the full name as ID for uniqueness
            name=topic_name,
            type="pubsub.topic",
            project=project_id,
            labels=response.get("labels"),
            kms_key_name=response.get("kmsKeyName"),
            message_storage_policy=message_storage_policy,
            schema_settings=schema_settings,
            message_retention_duration=response.get("messageRetentionDuration"),
            satisfies_pzs=response.get("satisfiesPzs"),
            created=response.get("created"),
            updated=response.get("updated"),
        )

        # Initialize _tags from labels if present
        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class PushConfig(BaseModel):
    """Push configuration for a Pub/Sub subscription."""

    push_endpoint: str = Field(
        ..., description="URL of the endpoint to push messages to"
    )
    attributes: Optional[Dict[str, str]] = Field(
        None, description="Endpoint configuration attributes"
    )
    oidc_token: Optional[Dict[str, str]] = Field(
        None, description="OIDC token configuration for authentication"
    )


class DeadLetterPolicy(BaseModel):
    """Dead letter policy for a Pub/Sub subscription."""

    dead_letter_topic: str = Field(
        ...,
        description="The name of the topic to which dead letter messages are published",
    )
    max_delivery_attempts: Optional[int] = Field(
        None, description="Maximum number of delivery attempts for any message"
    )


class RetryPolicy(BaseModel):
    """Retry policy for a Pub/Sub subscription."""

    minimum_backoff: Optional[str] = Field(
        None,
        description="Minimum backoff time between retries (in ISO 8601 duration format)",
    )
    maximum_backoff: Optional[str] = Field(
        None,
        description="Maximum backoff time between retries (in ISO 8601 duration format)",
    )


class ExpirationPolicy(BaseModel):
    """Expiration policy for a Pub/Sub subscription."""

    ttl: str = Field(
        ..., description="TTL duration after which the subscription expires"
    )


class PubSubSubscription(GCPResource):
    """Model for a Google Cloud Pub/Sub Subscription."""

    topic: str = Field(
        ..., description="The name of the topic this subscription is attached to"
    )
    push_config: Optional[PushConfig] = Field(
        None, description="Configuration for push delivery"
    )
    ack_deadline_seconds: Optional[int] = Field(
        None,
        description="The maximum time in seconds after receiving a message before it must be acknowledged",
    )
    retain_acked_messages: Optional[bool] = Field(
        None, description="Whether to retain acknowledged messages"
    )
    message_retention_duration: Optional[str] = Field(
        None,
        description="How long to retain unacknowledged messages (in ISO 8601 duration format)",
    )
    expiration_policy: Optional[ExpirationPolicy] = Field(
        None, description="Policy for subscription expiration"
    )
    filter: Optional[str] = Field(
        None, description="Expression to filter messages delivered to this subscription"
    )
    dead_letter_policy: Optional[DeadLetterPolicy] = Field(
        None, description="Dead letter policy for the subscription"
    )
    retry_policy: Optional[RetryPolicy] = Field(
        None, description="Retry policy for the subscription"
    )
    detached: Optional[bool] = Field(
        None, description="Whether the subscription is detached from its topic"
    )
    enable_message_ordering: Optional[bool] = Field(
        None, description="Whether to enable message ordering for this subscription"
    )
    _tags: Optional[Dict[str, str]] = None

    def get_tag(self, key: str, default: Any = None) -> Any:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        # First check explicit tags, then fall back to labels
        if self._tags and key in self._tags:
            return self._tags[key]
        elif self.labels and key in self.labels:
            return self.labels[key]
        else:
            return default

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("subscription")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "PubSubSubscription":
        """Create a PubSubSubscription from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new PubSubSubscription instance
        """
        # The API returns full names in the format: projects/{project}/subscriptions/{subscription}
        # and topics in the format: projects/{project}/topics/{topic}
        full_name = response.get("name", "")
        subscription_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID from the name if not provided
        if not project_id and full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        # Get the topic name (we just need the short name for the model)
        full_topic = response.get("topic", "")
        topic_name = full_topic.split("/")[-1] if full_topic else ""

        # Process push config if present
        push_config = None
        if response.get("pushConfig"):
            push_config_data = response.get("pushConfig")
            push_endpoint = push_config_data.get("pushEndpoint")
            if push_endpoint:
                push_config = PushConfig(
                    push_endpoint=push_endpoint,
                    attributes=push_config_data.get("attributes"),
                    oidc_token=push_config_data.get("oidcToken"),
                )

        # Process dead letter policy if present
        dead_letter_policy = None
        if response.get("deadLetterPolicy"):
            dlp_data = response.get("deadLetterPolicy")
            dead_letter_topic = dlp_data.get("deadLetterTopic")
            if dead_letter_topic:
                dead_letter_policy = DeadLetterPolicy(
                    dead_letter_topic=dead_letter_topic.split("/")[
                        -1
                    ],  # Get just the name
                    max_delivery_attempts=dlp_data.get("maxDeliveryAttempts"),
                )

        # Process retry policy if present
        retry_policy = None
        if response.get("retryPolicy"):
            rp_data = response.get("retryPolicy")
            min_backoff = rp_data.get("minimumBackoff")
            max_backoff = rp_data.get("maximumBackoff")
            if min_backoff or max_backoff:
                retry_policy = RetryPolicy(
                    minimum_backoff=min_backoff, maximum_backoff=max_backoff
                )

        # Process expiration policy if present
        expiration_policy = None
        if response.get("expirationPolicy"):
            exp_data = response.get("expirationPolicy")
            ttl = exp_data.get("ttl")
            if ttl:
                expiration_policy = ExpirationPolicy(ttl=ttl)

        instance = cls(
            id=full_name,  # Use the full name as ID for uniqueness
            name=subscription_name,
            type="pubsub.subscription",
            project=project_id,
            topic=topic_name,
            labels=response.get("labels"),
            push_config=push_config,
            ack_deadline_seconds=response.get("ackDeadlineSeconds"),
            retain_acked_messages=response.get("retainAckedMessages"),
            message_retention_duration=response.get("messageRetentionDuration"),
            expiration_policy=expiration_policy,
            filter=response.get("filter"),
            dead_letter_policy=dead_letter_policy,
            retry_policy=retry_policy,
            detached=response.get("detached"),
            enable_message_ordering=response.get("enableMessageOrdering"),
            created=response.get("created"),
            updated=response.get("updated"),
        )

        # Initialize _tags from labels if present
        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
