"""Models for Google Cloud Secret Manager resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.secret_manager import get_schema


class Secret(GCPResource):
    """Model for a Google Cloud Secret Manager Secret."""

    replication: Dict[str, Any] = Field(
        default_factory=dict,
        description="The replication policy for the secret",
    )
    expire_time: Optional[datetime] = Field(
        None, description="Optional expiration time for the secret"
    )
    ttl: Optional[str] = Field(
        None, description="Optional TTL duration for the secret"
    )
    rotation: Optional[Dict[str, Any]] = Field(
        None, description="Optional rotation policy for the secret"
    )
    topics: Optional[List[str]] = Field(
        None,
        description="Optional list of Pub/Sub topics for secret event notifications",
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

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("secret")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Secret":
        """Create a Secret from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new Secret instance
        """
        full_name = response.get("name", "")
        secret_name = full_name.split("/")[-1] if full_name else ""

        if not project_id and full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        # Extract topics as a list of topic name strings
        topics = None
        if response.get("topics"):
            topics = [t.get("name", "") for t in response["topics"]]

        instance = cls(
            id=full_name,
            name=secret_name,
            type="secretmanager.secret",
            project=project_id,
            labels=response.get("labels"),
            replication=response.get("replication", {}),
            expire_time=response.get("expireTime"),
            ttl=response.get("ttl"),
            rotation=response.get("rotation"),
            topics=topics,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class SecretVersion(GCPResource):
    """Model for a Google Cloud Secret Manager SecretVersion."""

    secret_name: str = Field(
        ..., description="The name of the parent secret"
    )
    version_id: str = Field(
        ..., description="The version identifier (e.g. '1', '2', 'latest')"
    )
    state: str = Field(
        "ENABLED",
        description="The state of the version: ENABLED, DISABLED, or DESTROYED",
    )
    create_time: Optional[datetime] = Field(
        None, description="When the version was created"
    )
    destroy_time: Optional[datetime] = Field(
        None, description="When the version was destroyed"
    )
    replication_status: Optional[Dict[str, Any]] = Field(
        None, description="The replication status of the secret version"
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

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("version")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "SecretVersion":
        """Create a SecretVersion from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new SecretVersion instance
        """
        # name format: projects/{project}/secrets/{secret}/versions/{version}
        full_name = response.get("name", "")
        parts = full_name.split("/") if full_name else []

        version_id = parts[-1] if len(parts) >= 6 else ""
        secret_name = parts[3] if len(parts) >= 4 else ""

        if not project_id and len(parts) >= 2:
            project_id = parts[1]

        instance = cls(
            id=full_name,
            name=full_name,
            type="secretmanager.version",
            project=project_id,
            secret_name=secret_name,
            version_id=version_id,
            state=response.get("state", "ENABLED"),
            create_time=response.get("createTime"),
            destroy_time=response.get("destroyTime"),
            replication_status=response.get("replicationStatus"),
        )

        return instance
