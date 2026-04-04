"""Models for Google Cloud Network Connectivity Center resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.network_connectivity import get_schema


class Hub(GCPResource):
    """Model for a Google Cloud Network Connectivity Hub."""

    description: Optional[str] = Field(
        None, description="A description of the hub"
    )
    routing_vpcs: Optional[List[Dict[str, Any]]] = Field(
        None, description="The VPC networks associated with this hub"
    )
    state: str = Field("", description="The current state of the hub")
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("hub")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "Hub":
        """Create a Hub from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Hub instance
        """
        name = response.get("name", "")
        parts = name.split("/")
        project = parts[1] if len(parts) > 1 else ""

        instance = cls(
            id=parts[-1] if parts else "",
            name=name,
            type="networkconnectivity.hub",
            project=project,
            description=response.get("description"),
            routing_vpcs=response.get("routingVpcs"),
            state=response.get("state", ""),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class Spoke(GCPResource):
    """Model for a Google Cloud Network Connectivity Spoke."""

    hub_name: str = Field("", description="The hub this spoke is attached to")
    location: str = Field("", description="The location of the spoke")
    description: Optional[str] = Field(
        None, description="A description of the spoke"
    )
    linked_vpn_tunnels: Optional[Dict[str, Any]] = Field(
        None, description="VPN tunnels linked to this spoke"
    )
    linked_interconnect_attachments: Optional[Dict[str, Any]] = Field(
        None,
        description="Interconnect attachments linked to this spoke",
    )
    linked_router_appliance_instances: Optional[Dict[str, Any]] = Field(
        None,
        description="Router appliance instances linked to this spoke",
    )
    state: str = Field("", description="The current state of the spoke")
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("spoke")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "Spoke":
        """Create a Spoke from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Spoke instance
        """
        name = response.get("name", "")
        parts = name.split("/")
        project = parts[1] if len(parts) > 1 else ""
        location = parts[3] if len(parts) > 3 else ""

        instance = cls(
            id=parts[-1] if parts else "",
            name=name,
            type="networkconnectivity.spoke",
            project=project,
            hub_name=response.get("hub", ""),
            location=location,
            description=response.get("description"),
            linked_vpn_tunnels=response.get("linkedVpnTunnels"),
            linked_interconnect_attachments=response.get(
                "linkedInterconnectAttachments"
            ),
            linked_router_appliance_instances=response.get(
                "linkedRouterApplianceInstances"
            ),
            state=response.get("state", ""),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance
