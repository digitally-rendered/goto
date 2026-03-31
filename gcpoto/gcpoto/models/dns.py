"""Models for Google Cloud DNS resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.dns import get_schema


class ManagedZone(GCPResource):
    """Model for a Google Cloud DNS Managed Zone."""

    dns_name: str = Field("", description="The DNS name of the managed zone")
    description: str = Field("", description="A description of the managed zone")
    visibility: str = Field(
        "public",
        description="The zone's visibility: public or private",
    )
    name_servers: List[str] = Field(
        default_factory=list,
        description="Name servers assigned to this managed zone",
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("zone")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "ManagedZone":
        """Create a ManagedZone from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ManagedZone instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="dns.managedZone",
            project=response.get("project", ""),
            dns_name=response.get("dnsName", ""),
            description=response.get("description", ""),
            visibility=response.get("visibility", "public"),
            name_servers=response.get("nameServers", []),
            labels=response.get("labels"),
            created=response.get("creationTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class ResourceRecordSet(GCPResource):
    """Model for a Google Cloud DNS Resource Record Set."""

    zone_name: str = Field("", description="The managed zone this record set belongs to")
    dns_name: str = Field("", description="The DNS name of this record set")
    record_type: str = Field(
        "",
        description="The type of DNS record (A, AAAA, CNAME, MX, TXT, NS, SOA, SRV, PTR)",
    )
    ttl: int = Field(0, description="Time to live in seconds")
    rrdatas: List[str] = Field(
        default_factory=list,
        description="The resource record data for this record set",
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("record_set")}

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
        cls, response: Dict[str, Any], zone_name: str = ""
    ) -> "ResourceRecordSet":
        """Create a ResourceRecordSet from an API response.

        Args:
            response: The API response dictionary
            zone_name: The name of the managed zone this record belongs to

        Returns:
            A new ResourceRecordSet instance
        """
        dns_name = response.get("name", "")
        record_type = response.get("type", "")

        instance = cls(
            id=f"{dns_name}/{record_type}",
            name=dns_name,
            type="dns.resourceRecordSet",
            project=response.get("project", ""),
            zone_name=zone_name,
            dns_name=dns_name,
            record_type=record_type,
            ttl=response.get("ttl", 0),
            rrdatas=response.get("rrdatas", []),
            labels=response.get("labels"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance
