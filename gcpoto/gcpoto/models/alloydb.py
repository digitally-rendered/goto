"""Models for Google Cloud AlloyDB resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class AlloyDBCluster(GCPResource):
    """Model for a Google Cloud AlloyDB cluster."""

    location: str = Field("", description="The GCP location of the cluster")
    network: str = Field("", description="The VPC network for the cluster")
    state: str = Field("", description="The current state of the cluster")
    database_version: Optional[str] = Field(
        None, description="The database engine version (e.g. POSTGRES_14)"
    )
    automated_backup_policy: Optional[Dict] = Field(
        None, description="The automated backup policy configuration"
    )
    continuous_backup_config: Optional[Dict] = Field(
        None, description="The continuous backup configuration"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "AlloyDBCluster":
        """Create an AlloyDBCluster from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new AlloyDBCluster instance
        """
        name = response.get("name", "")
        # Extract short name from full path:
        # projects/{project}/locations/{location}/clusters/{cluster}
        short_name = name.split("/")[-1] if "/" in name else name
        parts = name.split("/")
        project = parts[1] if len(parts) >= 2 else response.get("project", "")
        location = parts[3] if len(parts) >= 4 else ""
        labels = response.get("labels")

        instance = cls(
            id=short_name,
            name=short_name,
            type="alloydb.cluster",
            project=project,
            location=location,
            network=response.get("network", ""),
            state=response.get("state", ""),
            database_version=response.get("databaseVersion"),
            automated_backup_policy=response.get("automatedBackupPolicy"),
            continuous_backup_config=response.get("continuousBackupConfig"),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class AlloyDBInstance(GCPResource):
    """Model for a Google Cloud AlloyDB instance."""

    cluster_name: str = Field("", description="The AlloyDB cluster name")
    location: str = Field("", description="The GCP location of the instance")
    instance_type: str = Field(
        "", description="The instance type (PRIMARY or READ_POOL)"
    )
    state: str = Field("", description="The current state of the instance")
    machine_config: Optional[Dict] = Field(
        None, description="Machine configuration for the instance"
    )
    availability_type: Optional[str] = Field(
        None, description="Availability type (e.g. REGIONAL, ZONAL)"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "AlloyDBInstance":
        """Create an AlloyDBInstance from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new AlloyDBInstance instance
        """
        name = response.get("name", "")
        # Extract short name from full path:
        # projects/{project}/locations/{location}/clusters/{cluster}/instances/{instance}
        short_name = name.split("/")[-1] if "/" in name else name
        parts = name.split("/")
        project = parts[1] if len(parts) >= 2 else response.get("project", "")
        location = parts[3] if len(parts) >= 4 else ""
        cluster_name = parts[5] if len(parts) >= 6 else ""

        return cls(
            id=short_name,
            name=short_name,
            type="alloydb.instance",
            project=project,
            cluster_name=cluster_name,
            location=location,
            instance_type=response.get("instanceType", ""),
            state=response.get("state", ""),
            machine_config=response.get("machineConfig"),
            availability_type=response.get("availabilityType"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
