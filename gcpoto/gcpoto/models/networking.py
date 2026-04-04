"""Models for Google Cloud VPC / Networking resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.networking import get_schema


class VPCNetwork(GCPResource):
    """Model for a Google Cloud VPC Network."""

    auto_create_subnetworks: bool = Field(
        True, description="Whether subnets are created automatically"
    )
    routing_mode: str = Field(
        "REGIONAL",
        description="The network-wide routing mode (REGIONAL or GLOBAL)",
    )
    mtu: Optional[int] = Field(
        None, description="Maximum Transmission Unit in bytes"
    )
    description: Optional[str] = Field(
        None, description="A description of the VPC network"
    )
    peerings: Optional[List[Dict]] = Field(
        None, description="List of network peerings"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("network")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "VPCNetwork":
        """Create a VPCNetwork from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new VPCNetwork instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.network",
            project=response.get("project", ""),
            auto_create_subnetworks=response.get("autoCreateSubnetworks", True),
            routing_mode=response.get("routingConfig", {}).get("routingMode", "REGIONAL"),
            mtu=response.get("mtu"),
            description=response.get("description"),
            peerings=response.get("peerings"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class Subnet(GCPResource):
    """Model for a Google Cloud VPC Subnet."""

    network: str = Field("", description="The URL of the network this subnet belongs to")
    region: str = Field("", description="The region of the subnet")
    ip_cidr_range: str = Field("", description="The IPv4 CIDR range of the subnet")
    gateway_address: Optional[str] = Field(
        None, description="The gateway address for the subnet"
    )
    private_ip_google_access: bool = Field(
        False,
        description="Whether VMs can access Google services without external IP",
    )
    secondary_ip_ranges: Optional[List[Dict]] = Field(
        None, description="Secondary IP ranges for the subnet"
    )
    purpose: Optional[str] = Field(
        None, description="The purpose of the subnet (e.g. PRIVATE, INTERNAL_HTTPS_LOAD_BALANCER)"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("subnet")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "Subnet":
        """Create a Subnet from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Subnet instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.subnetwork",
            project=response.get("project", ""),
            network=response.get("network", ""),
            region=response.get("region", "").split("/")[-1],
            ip_cidr_range=response.get("ipCidrRange", ""),
            gateway_address=response.get("gatewayAddress"),
            private_ip_google_access=response.get("privateIpGoogleAccess", False),
            secondary_ip_ranges=response.get("secondaryIpRanges"),
            purpose=response.get("purpose"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class FirewallRule(GCPResource):
    """Model for a Google Cloud VPC Firewall Rule."""

    network: str = Field("", description="The URL of the network this rule applies to")
    direction: str = Field(
        "INGRESS", description="Direction of traffic (INGRESS or EGRESS)"
    )
    priority: int = Field(1000, description="Priority of the rule (0-65535)")
    allowed: Optional[List[Dict]] = Field(
        None, description="List of allowed protocols and ports"
    )
    denied: Optional[List[Dict]] = Field(
        None, description="List of denied protocols and ports"
    )
    source_ranges: Optional[List[str]] = Field(
        None, description="Source IP CIDR ranges"
    )
    destination_ranges: Optional[List[str]] = Field(
        None, description="Destination IP CIDR ranges"
    )
    source_tags: Optional[List[str]] = Field(
        None, description="Source instance tags"
    )
    target_tags: Optional[List[str]] = Field(
        None, description="Target instance tags"
    )
    disabled: bool = Field(False, description="Whether the rule is disabled")
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("firewall")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "FirewallRule":
        """Create a FirewallRule from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new FirewallRule instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.firewall",
            project=response.get("project", ""),
            network=response.get("network", ""),
            direction=response.get("direction", "INGRESS"),
            priority=response.get("priority", 1000),
            allowed=response.get("allowed"),
            denied=response.get("denied"),
            source_ranges=response.get("sourceRanges"),
            destination_ranges=response.get("destinationRanges"),
            source_tags=response.get("sourceTags"),
            target_tags=response.get("targetTags"),
            disabled=response.get("disabled", False),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class StaticAddress(GCPResource):
    """Model for a Google Cloud Static Address."""

    region: Optional[str] = Field(
        None, description="The region of the address (None for global)"
    )
    address: Optional[str] = Field(
        None, description="The static IP address"
    )
    address_type: str = Field(
        "EXTERNAL", description="The type of address (INTERNAL or EXTERNAL)"
    )
    status: str = Field("", description="The status of the address (RESERVED, IN_USE)")
    network_tier: Optional[str] = Field(
        None, description="The network tier (PREMIUM or STANDARD)"
    )
    purpose: Optional[str] = Field(
        None, description="The purpose of the address"
    )
    subnetwork: Optional[str] = Field(
        None, description="The URL of the subnetwork for INTERNAL addresses"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("address")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "StaticAddress":
        """Create a StaticAddress from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new StaticAddress instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.address",
            project=response.get("project", ""),
            region=response.get("region", "").split("/")[-1] if response.get("region") else None,
            address=response.get("address"),
            address_type=response.get("addressType", "EXTERNAL"),
            status=response.get("status", ""),
            network_tier=response.get("networkTier"),
            purpose=response.get("purpose"),
            subnetwork=response.get("subnetwork"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance
