"""Models for Google Cloud Interconnect resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.interconnect import get_schema


class Interconnect(GCPResource):
    """Model for a Google Cloud Interconnect."""

    location: str = Field("", description="The location of the interconnect")
    interconnect_type: str = Field(
        "", description="The type of interconnect (IT_PRIVATE or PARTNER)"
    )
    link_type: str = Field("", description="The link type of the interconnect")
    requested_link_count: int = Field(
        0, description="The number of requested links"
    )
    state: str = Field("", description="The current state of the interconnect")
    operational_status: Optional[str] = Field(
        None, description="The operational status of the interconnect"
    )
    peer_ip_address: Optional[str] = Field(
        None, description="The peer IP address"
    )
    google_ip_address: Optional[str] = Field(
        None, description="The Google IP address"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("interconnect")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Interconnect":
        """Create an Interconnect from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Interconnect instance
        """
        name = response.get("name", "")
        interconnect_id = (
            name.rsplit("/", 1)[-1] if "/" in name else name
        )

        instance = cls(
            id=response.get("id", interconnect_id),
            name=name,
            type="compute.interconnect",
            project=response.get("project", ""),
            location=response.get("location", ""),
            interconnect_type=response.get("interconnectType", ""),
            link_type=response.get("linkType", ""),
            requested_link_count=response.get("requestedLinkCount", 0),
            state=response.get("state", ""),
            operational_status=response.get("operationalStatus"),
            peer_ip_address=response.get("peerIpAddress"),
            google_ip_address=response.get("googleIpAddress"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance

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


class InterconnectAttachment(GCPResource):
    """Model for a Google Cloud Interconnect Attachment (VLAN)."""

    region: str = Field("", description="The region of the attachment")
    interconnect_name: Optional[str] = Field(
        None, description="The interconnect this attachment is associated with"
    )
    router: str = Field(
        "", description="The Cloud Router associated with the attachment"
    )
    type_field: str = Field(
        "", description="The type of attachment (DEDICATED or PARTNER)"
    )
    state: str = Field(
        "", description="The current state of the attachment"
    )
    bandwidth: Optional[str] = Field(
        None, description="The bandwidth of the attachment"
    )
    vlan_tag8021q: Optional[int] = Field(
        None, description="The 802.1q VLAN tag for the attachment"
    )
    pairing_key: Optional[str] = Field(
        None, description="The pairing key for partner interconnect"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("attachment")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "InterconnectAttachment":
        """Create an InterconnectAttachment from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new InterconnectAttachment instance
        """
        name = response.get("name", "")
        attachment_id = (
            name.rsplit("/", 1)[-1] if "/" in name else name
        )

        instance = cls(
            id=response.get("id", attachment_id),
            name=name,
            type="compute.interconnectAttachment",
            project=response.get("project", ""),
            region=response.get("region", ""),
            interconnect_name=response.get("interconnect"),
            router=response.get("router", ""),
            type_field=response.get("type", ""),
            state=response.get("state", ""),
            bandwidth=response.get("bandwidth"),
            vlan_tag8021q=response.get("vlanTag8021q"),
            pairing_key=response.get("pairingKey"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance

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
