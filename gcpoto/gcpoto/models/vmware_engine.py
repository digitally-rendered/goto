"""Models for Google Cloud VMware Engine resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class PrivateCloud(GCPResource):
    """Model for a VMware Engine private cloud."""

    location: str = Field("", description="The location of the private cloud")
    description: Optional[str] = Field(
        None, description="An optional description of the private cloud"
    )
    state: str = Field("", description="The current state of the private cloud")
    network_config: Optional[Dict] = Field(
        None, description="Network configuration for the private cloud"
    )
    management_cluster: Optional[Dict] = Field(
        None, description="Management cluster configuration"
    )
    hcx: Optional[Dict] = Field(
        None, description="HCX appliance configuration"
    )
    nsx: Optional[Dict] = Field(
        None, description="NSX appliance configuration"
    )
    vcenter: Optional[Dict] = Field(
        None, description="vCenter appliance configuration"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "PrivateCloud":
        """Create a PrivateCloud from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new PrivateCloud instance
        """
        labels = response.get("labels")

        instance = cls(
            id=response.get("uid", ""),
            name=response.get("name", ""),
            type="vmwareengine.privateCloud",
            project=response.get("projectId", ""),
            location=response.get("location", ""),
            description=response.get("description"),
            state=response.get("state", ""),
            network_config=response.get("networkConfig"),
            management_cluster=response.get("managementCluster"),
            hcx=response.get("hcx"),
            nsx=response.get("nsx"),
            vcenter=response.get("vcenter"),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class Cluster(GCPResource):
    """Model for a VMware Engine cluster."""

    private_cloud_name: str = Field(
        "", description="The name of the parent private cloud"
    )
    location: str = Field("", description="The location of the cluster")
    node_type_configs: Optional[Dict] = Field(
        None, description="Node type configurations for the cluster"
    )
    state: str = Field("", description="The current state of the cluster")
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
    def from_api_response(cls, response: Dict[str, Any]) -> "Cluster":
        """Create a Cluster from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Cluster instance
        """
        labels = response.get("labels")

        instance = cls(
            id=response.get("uid", ""),
            name=response.get("name", ""),
            type="vmwareengine.cluster",
            project=response.get("projectId", ""),
            private_cloud_name=response.get("privateCloudName", ""),
            location=response.get("location", ""),
            node_type_configs=response.get("nodeTypeConfigs"),
            state=response.get("state", ""),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance
