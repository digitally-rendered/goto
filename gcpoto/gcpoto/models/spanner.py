"""Models for Google Cloud Spanner resources."""

from datetime import datetime
from typing import Dict, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class SpannerInstance(GCPResource):
    """Model for a Google Cloud Spanner instance."""

    display_name: str = Field("", description="The descriptive name for the instance")
    config: str = Field(
        "", description="The instance configuration (e.g. regional-us-central1)"
    )
    node_count: int = Field(0, description="The number of nodes allocated")
    processing_units: Optional[int] = Field(
        None, description="The number of processing units allocated"
    )
    state: str = Field("", description="The current state of the instance")
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
    def from_api_response(cls, response: Dict[str, Any]) -> "SpannerInstance":
        """Create a SpannerInstance from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new SpannerInstance instance
        """
        name = response.get("name", "")
        # Extract short name from full path: projects/{project}/instances/{id}
        short_name = name.split("/")[-1] if "/" in name else name
        # Extract project from full path
        parts = name.split("/")
        project = parts[1] if len(parts) >= 2 else response.get("project", "")
        labels = response.get("labels")

        instance = cls(
            id=short_name,
            name=short_name,
            type="spanner.instance",
            project=project,
            display_name=response.get("displayName", ""),
            config=response.get("config", ""),
            node_count=response.get("nodeCount", 0),
            processing_units=response.get("processingUnits"),
            state=response.get("state", ""),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class SpannerDatabase(GCPResource):
    """Model for a Google Cloud Spanner database."""

    instance_name: str = Field("", description="The Spanner instance name")
    state: str = Field("", description="The current state of the database")
    version_retention_period: Optional[str] = Field(
        None, description="The retention period for database versions"
    )
    earliest_version_time: Optional[datetime] = Field(
        None, description="The earliest version time for the database"
    )
    encryption_config: Optional[Dict] = Field(
        None, description="Encryption configuration for the database"
    )
    database_dialect: Optional[str] = Field(
        None, description="The SQL dialect of the database (e.g. GOOGLE_STANDARD_SQL)"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "SpannerDatabase":
        """Create a SpannerDatabase from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new SpannerDatabase instance
        """
        name = response.get("name", "")
        # Extract short name from full path:
        # projects/{project}/instances/{instance}/databases/{db}
        short_name = name.split("/")[-1] if "/" in name else name
        parts = name.split("/")
        project = parts[1] if len(parts) >= 2 else response.get("project", "")
        instance_name = parts[3] if len(parts) >= 4 else ""

        return cls(
            id=short_name,
            name=short_name,
            type="spanner.database",
            project=project,
            instance_name=instance_name,
            state=response.get("state", ""),
            version_retention_period=response.get("versionRetentionPeriod"),
            earliest_version_time=response.get("earliestVersionTime"),
            encryption_config=response.get("encryptionConfig"),
            database_dialect=response.get("databaseDialect"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
