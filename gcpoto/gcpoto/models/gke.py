"""Models for Google Kubernetes Engine (GKE) resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class GKECluster(GCPResource):
    """Model for a Google Kubernetes Engine cluster."""

    location: str = Field("", description="The location (zone or region) of the cluster")
    description: Optional[str] = Field(
        None, description="An optional description of the cluster"
    )
    initial_node_count: Optional[int] = Field(
        None, description="The initial number of nodes for the cluster"
    )
    node_config: Optional[Dict] = Field(
        None, description="The node configuration for the cluster"
    )
    master_auth: Optional[Dict] = Field(
        None, description="The authentication information for the master"
    )
    network: Optional[str] = Field(
        None, description="The name of the VPC network"
    )
    subnetwork: Optional[str] = Field(
        None, description="The name of the subnetwork"
    )
    cluster_ipv4_cidr: Optional[str] = Field(
        None, description="The IP address range of the container pods"
    )
    endpoint: Optional[str] = Field(
        None, description="The IP address of the cluster master"
    )
    status: str = Field("", description="The current status of the cluster")
    current_master_version: Optional[str] = Field(
        None, description="The current software version of the master"
    )
    current_node_version: Optional[str] = Field(
        None, description="The current version of the node software"
    )
    node_pools: Optional[List[Dict]] = Field(
        None, description="The node pools associated with this cluster"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "GKECluster":
        """Create a GKECluster from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new GKECluster instance
        """
        labels = response.get("resourceLabels")

        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="container.cluster",
            project=response.get("projectId", ""),
            location=response.get("location", ""),
            description=response.get("description"),
            initial_node_count=response.get("initialNodeCount"),
            node_config=response.get("nodeConfig"),
            master_auth=response.get("masterAuth"),
            network=response.get("network"),
            subnetwork=response.get("subnetwork"),
            cluster_ipv4_cidr=response.get("clusterIpv4Cidr"),
            endpoint=response.get("endpoint"),
            status=response.get("status", ""),
            current_master_version=response.get("currentMasterVersion"),
            current_node_version=response.get("currentNodeVersion"),
            node_pools=response.get("nodePools"),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class NodePool(GCPResource):
    """Model for a GKE node pool."""

    cluster_name: str = Field("", description="The name of the parent cluster")
    location: str = Field("", description="The location (zone or region) of the cluster")
    config: Optional[Dict] = Field(
        None, description="The node configuration for this pool"
    )
    initial_node_count: int = Field(
        0, description="The initial node count for the pool"
    )
    autoscaling: Optional[Dict] = Field(
        None, description="Autoscaling configuration for this pool"
    )
    management: Optional[Dict] = Field(
        None, description="Node management configuration for this pool"
    )
    status: str = Field("", description="The current status of the node pool")
    version: Optional[str] = Field(
        None, description="The Kubernetes version of the nodes in this pool"
    )
    instance_group_urls: Optional[List[str]] = Field(
        None, description="The URLs of the instance groups managed by this pool"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "NodePool":
        """Create a NodePool from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new NodePool instance
        """
        config = response.get("config", {})
        labels = config.get("labels") if config else None

        instance = cls(
            id=response.get("name", ""),
            name=response.get("name", ""),
            type="container.nodePool",
            project=response.get("projectId", ""),
            cluster_name=response.get("clusterName", ""),
            location=response.get("location", ""),
            config=config or None,
            initial_node_count=response.get("initialNodeCount", 0),
            autoscaling=response.get("autoscaling"),
            management=response.get("management"),
            status=response.get("status", ""),
            version=response.get("version"),
            instance_group_urls=response.get("instanceGroupUrls"),
            labels=labels,
        )
        if labels:
            instance._tags = labels
        return instance
