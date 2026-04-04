"""Models for Google Cloud Bigtable resources."""

from typing import Dict, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class BigtableInstance(GCPResource):
    """Model for a Google Cloud Bigtable instance."""

    display_name: str = Field("", description="The descriptive name for the instance")
    instance_type: str = Field(
        "", description="The type of the instance (PRODUCTION or DEVELOPMENT)"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "BigtableInstance":
        """Create a BigtableInstance from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new BigtableInstance instance
        """
        name = response.get("name", "")
        # Extract short name from full path like projects/{project}/instances/{id}
        short_name = name.split("/")[-1] if "/" in name else name
        project = ""
        if "/" in name:
            parts = name.split("/")
            if len(parts) >= 2:
                project = parts[1]

        labels = response.get("labels")

        instance = cls(
            id=short_name,
            name=short_name,
            type="bigtable.instance",
            project=project,
            display_name=response.get("displayName", ""),
            instance_type=response.get("type", ""),
            state=response.get("state", ""),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class BigtableCluster(GCPResource):
    """Model for a Google Cloud Bigtable cluster."""

    instance_name: str = Field("", description="The Bigtable instance name")
    location: str = Field("", description="The location of the cluster")
    serve_nodes: int = Field(0, description="The number of nodes in the cluster")
    default_storage_type: str = Field(
        "", description="The storage type for the cluster (SSD or HDD)"
    )
    state: str = Field("", description="The current state of the cluster")

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "BigtableCluster":
        """Create a BigtableCluster from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new BigtableCluster instance
        """
        name = response.get("name", "")
        # Extract short name from full path like
        # projects/{project}/instances/{instance}/clusters/{cluster}
        short_name = name.split("/")[-1] if "/" in name else name
        project = ""
        instance_name = ""
        if "/" in name:
            parts = name.split("/")
            if len(parts) >= 4:
                project = parts[1]
                instance_name = parts[3]

        location = response.get("location", "")
        # Extract location short name from full path
        if "/" in location:
            location = location.split("/")[-1]

        return cls(
            id=short_name,
            name=short_name,
            type="bigtable.cluster",
            project=project,
            instance_name=instance_name,
            location=location,
            serve_nodes=response.get("serveNodes", 0),
            default_storage_type=response.get("defaultStorageType", ""),
            state=response.get("state", ""),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )


class BigtableTable(GCPResource):
    """Model for a Google Cloud Bigtable table."""

    instance_name: str = Field("", description="The Bigtable instance name")
    column_families: Dict[str, Dict] = Field(
        default_factory=dict,
        description="The column families configured for the table",
    )
    granularity: Optional[str] = Field(
        None, description="The granularity of timestamps in the table"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "BigtableTable":
        """Create a BigtableTable from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new BigtableTable instance
        """
        name = response.get("name", "")
        # Extract short name from full path like
        # projects/{project}/instances/{instance}/tables/{table}
        short_name = name.split("/")[-1] if "/" in name else name
        project = ""
        instance_name = ""
        if "/" in name:
            parts = name.split("/")
            if len(parts) >= 4:
                project = parts[1]
                instance_name = parts[3]

        return cls(
            id=short_name,
            name=short_name,
            type="bigtable.table",
            project=project,
            instance_name=instance_name,
            column_families=response.get("columnFamilies", {}),
            granularity=response.get("granularity"),
        )
