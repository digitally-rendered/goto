"""Models for Google Cloud Media CDN resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class EdgeCacheService(GCPResource):
    """Model for a Media CDN Edge Cache Service."""

    location: str = Field("", description="The location of the service")
    description: Optional[str] = Field(
        None, description="An optional description of the service"
    )
    routing: Dict = Field(
        default_factory=dict, description="Routing configuration"
    )
    edge_ssl_certificates: Optional[List[str]] = Field(
        None, description="SSL certificates for the edge"
    )
    edge_security_policy: Optional[str] = Field(
        None, description="The edge security policy"
    )
    disable_quic: bool = Field(
        False, description="Whether QUIC is disabled"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "EdgeCacheService":
        """Create an EdgeCacheService from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new EdgeCacheService instance
        """
        labels = response.get("labels")

        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="networkservices.edgeCacheService",
            project=response.get("projectId", ""),
            location=response.get("location", ""),
            description=response.get("description"),
            routing=response.get("routing", {}),
            edge_ssl_certificates=response.get("edgeSslCertificates"),
            edge_security_policy=response.get("edgeSecurityPolicy"),
            disable_quic=response.get("disableQuic", False),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class EdgeCacheOrigin(GCPResource):
    """Model for a Media CDN Edge Cache Origin."""

    location: str = Field("", description="The location of the origin")
    origin_address: str = Field(
        "", description="The origin address (IP or hostname)"
    )
    protocol: Optional[str] = Field(
        None, description="The protocol used to connect to the origin"
    )
    port: Optional[int] = Field(
        None, description="The port to connect to the origin"
    )
    retry_conditions: Optional[List[str]] = Field(
        None, description="Conditions under which retries are attempted"
    )
    max_attempts: Optional[int] = Field(
        None, description="Maximum number of attempts for origin requests"
    )
    failover_origin: Optional[str] = Field(
        None, description="The failover origin resource"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "EdgeCacheOrigin":
        """Create an EdgeCacheOrigin from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new EdgeCacheOrigin instance
        """
        labels = response.get("labels")

        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="networkservices.edgeCacheOrigin",
            project=response.get("projectId", ""),
            location=response.get("location", ""),
            origin_address=response.get("originAddress", ""),
            protocol=response.get("protocol"),
            port=response.get("port"),
            retry_conditions=response.get("retryConditions"),
            max_attempts=response.get("maxAttempts"),
            failover_origin=response.get("failoverOrigin"),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        return instance
