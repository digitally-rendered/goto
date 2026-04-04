"""Models for Google Cloud VPN resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.vpn import get_schema


class VPNGateway(GCPResource):
    """Model for a Google Cloud VPN Gateway."""

    region: str = Field("", description="The region of the VPN gateway")
    network: str = Field("", description="The network this VPN gateway is in")
    vpn_interfaces: Optional[List[Dict[str, Any]]] = Field(
        None, description="VPN interfaces for the gateway"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("vpn_gateway")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "VPNGateway":
        """Create a VPNGateway from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new VPNGateway instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.vpnGateway",
            project=response.get("project", ""),
            region=response.get("region", ""),
            network=response.get("network", ""),
            vpn_interfaces=response.get("vpnInterfaces"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class VPNTunnel(GCPResource):
    """Model for a Google Cloud VPN Tunnel."""

    region: str = Field("", description="The region of the VPN tunnel")
    vpn_gateway: str = Field(
        "", description="The VPN gateway this tunnel is associated with"
    )
    peer_ip: str = Field("", description="The peer IP address")
    shared_secret: Optional[str] = Field(
        None, description="The shared secret for the tunnel"
    )
    ike_version: int = Field(2, description="The IKE protocol version")
    status: str = Field("", description="The status of the tunnel")
    detailed_status: Optional[str] = Field(
        None, description="Detailed status message"
    )
    local_traffic_selector: Optional[List[str]] = Field(
        None, description="Local traffic selector CIDR ranges"
    )
    remote_traffic_selector: Optional[List[str]] = Field(
        None, description="Remote traffic selector CIDR ranges"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("vpn_tunnel")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "VPNTunnel":
        """Create a VPNTunnel from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new VPNTunnel instance
        """
        return cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.vpnTunnel",
            project=response.get("project", ""),
            region=response.get("region", ""),
            vpn_gateway=response.get("vpnGateway", ""),
            peer_ip=response.get("peerIp", ""),
            shared_secret=response.get("sharedSecret"),
            ike_version=response.get("ikeVersion", 2),
            status=response.get("status", ""),
            detailed_status=response.get("detailedStatus"),
            local_traffic_selector=response.get("localTrafficSelector"),
            remote_traffic_selector=response.get("remoteTrafficSelector"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
