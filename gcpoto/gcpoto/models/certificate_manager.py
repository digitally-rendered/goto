"""Models for Google Cloud Certificate Manager resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.certificate_manager import get_schema


class Certificate(GCPResource):
    """Model for a Google Cloud Certificate Manager Certificate."""

    location: str = Field("", description="The location of the certificate")
    description: Optional[str] = Field(
        None, description="A description of the certificate"
    )
    san_dnsnames: Optional[List[str]] = Field(
        None, description="Subject Alternative Name DNS names"
    )
    pem_certificate: Optional[str] = Field(
        None, description="The PEM-encoded certificate chain"
    )
    expire_time: Optional[datetime] = Field(
        None, description="The expiration time of the certificate"
    )
    scope: Optional[str] = Field(
        None, description="The scope of the certificate (DEFAULT or EDGE_CACHE)"
    )
    managed: Optional[Dict[str, Any]] = Field(
        None, description="Managed certificate configuration"
    )
    self_managed: Optional[Dict[str, Any]] = Field(
        None, description="Self-managed certificate configuration"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("certificate")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "Certificate":
        """Create a Certificate from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Certificate instance
        """
        name = response.get("name", "")
        short_name = name.split("/")[-1] if name else ""

        instance = cls(
            id=short_name,
            name=name,
            type="certificatemanager.certificate",
            project=response.get("project", ""),
            location=response.get("location", ""),
            description=response.get("description"),
            san_dnsnames=response.get("sanDnsnames"),
            pem_certificate=response.get("pemCertificate"),
            expire_time=response.get("expireTime"),
            scope=response.get("scope"),
            managed=response.get("managed"),
            self_managed=response.get("selfManaged"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class CertificateMap(GCPResource):
    """Model for a Google Cloud Certificate Manager Certificate Map."""

    location: str = Field(
        "", description="The location of the certificate map"
    )
    description: Optional[str] = Field(
        None, description="A description of the certificate map"
    )
    gclb_targets: Optional[List[Dict[str, Any]]] = Field(
        None, description="GCLB targets associated with this map"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("certificate_map")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "CertificateMap":
        """Create a CertificateMap from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new CertificateMap instance
        """
        name = response.get("name", "")
        short_name = name.split("/")[-1] if name else ""

        instance = cls(
            id=short_name,
            name=name,
            type="certificatemanager.certificateMap",
            project=response.get("project", ""),
            location=response.get("location", ""),
            description=response.get("description"),
            gclb_targets=response.get("gclbTargets"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance
