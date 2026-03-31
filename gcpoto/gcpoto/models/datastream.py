"""Models for Google Cloud Datastream resources."""

from typing import Dict, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class ConnectionProfile(GCPResource):
    """Model for a Google Cloud Datastream Connection Profile."""

    location: str = Field("", description="The location of the connection profile")
    display_name: str = Field("", description="Display name of the connection profile")
    oracle_profile: Optional[Dict[str, Any]] = Field(
        None, description="Oracle connection profile configuration"
    )
    mysql_profile: Optional[Dict[str, Any]] = Field(
        None, description="MySQL connection profile configuration"
    )
    postgresql_profile: Optional[Dict[str, Any]] = Field(
        None, description="PostgreSQL connection profile configuration"
    )
    gcs_profile: Optional[Dict[str, Any]] = Field(
        None, description="GCS connection profile configuration"
    )
    bigquery_profile: Optional[Dict[str, Any]] = Field(
        None, description="BigQuery connection profile configuration"
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
    ) -> "ConnectionProfile":
        """Create a ConnectionProfile from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new ConnectionProfile instance
        """
        name = response.get("name", "")
        # name: projects/{p}/locations/{l}/connectionProfiles/{id}
        parts = name.split("/")
        profile_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        instance = cls(
            id=profile_id,
            name=name,
            type="datastream.connectionProfile",
            project=project_id,
            location=location,
            display_name=response.get("displayName", ""),
            oracle_profile=response.get("oracleProfile"),
            mysql_profile=response.get("mysqlProfile"),
            postgresql_profile=response.get("postgresqlProfile"),
            gcs_profile=response.get("gcsProfile"),
            bigquery_profile=response.get("bigqueryProfile"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class Stream(GCPResource):
    """Model for a Google Cloud Datastream Stream."""

    location: str = Field("", description="The location of the stream")
    display_name: str = Field("", description="Display name of the stream")
    source_config: Dict[str, Any] = Field(
        default_factory=dict, description="Source connection configuration"
    )
    destination_config: Dict[str, Any] = Field(
        default_factory=dict, description="Destination connection configuration"
    )
    state: str = Field("", description="The state of the stream")
    backfill_all: Optional[Dict[str, Any]] = Field(
        None, description="Backfill all objects configuration"
    )
    backfill_none: Optional[Dict[str, Any]] = Field(
        None, description="No backfill configuration"
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
    ) -> "Stream":
        """Create a Stream from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new Stream instance
        """
        name = response.get("name", "")
        # name: projects/{p}/locations/{l}/streams/{id}
        parts = name.split("/")
        stream_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        instance = cls(
            id=stream_id,
            name=name,
            type="datastream.stream",
            project=project_id,
            location=location,
            display_name=response.get("displayName", ""),
            source_config=response.get("sourceConfig", {}),
            destination_config=response.get("destinationConfig", {}),
            state=response.get("state", ""),
            backfill_all=response.get("backfillAll"),
            backfill_none=response.get("backfillNone"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
