"""Models for Google Cloud Network Security resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.network_security import get_schema


class ServerTLSPolicy(GCPResource):
    """Model for a Google Cloud Network Security Server TLS Policy."""

    location: str = Field("", description="The location of the policy")
    description: Optional[str] = Field(
        None, description="A description of the policy"
    )
    allow_open: bool = Field(
        False, description="Whether to allow open (non-TLS) connections"
    )
    server_certificate: Optional[Dict[str, Any]] = Field(
        None, description="The server certificate configuration"
    )
    mtls_policy: Optional[Dict[str, Any]] = Field(
        None, description="The mutual TLS policy configuration"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("server_tls_policy")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "ServerTLSPolicy":
        """Create a ServerTLSPolicy from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ServerTLSPolicy instance
        """
        name = response.get("name", "")
        parts = name.split("/")
        project = parts[1] if len(parts) > 1 else ""
        location = parts[3] if len(parts) > 3 else ""

        instance = cls(
            id=parts[-1] if parts else "",
            name=name,
            type="networksecurity.serverTlsPolicy",
            project=project,
            location=location,
            description=response.get("description"),
            allow_open=response.get("allowOpen", False),
            server_certificate=response.get("serverCertificate"),
            mtls_policy=response.get("mtlsPolicy"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class AuthorizationPolicy(GCPResource):
    """Model for a Google Cloud Network Security Authorization Policy."""

    location: str = Field("", description="The location of the policy")
    description: Optional[str] = Field(
        None, description="A description of the policy"
    )
    action: str = Field(
        "ALLOW",
        description="The action to take (ALLOW or DENY)",
    )
    rules: Optional[List[Dict[str, Any]]] = Field(
        None, description="The authorization rules"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("authorization_policy")}

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
        cls, response: Dict[str, Any]
    ) -> "AuthorizationPolicy":
        """Create an AuthorizationPolicy from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new AuthorizationPolicy instance
        """
        name = response.get("name", "")
        parts = name.split("/")
        project = parts[1] if len(parts) > 1 else ""
        location = parts[3] if len(parts) > 3 else ""

        instance = cls(
            id=parts[-1] if parts else "",
            name=name,
            type="networksecurity.authorizationPolicy",
            project=project,
            location=location,
            description=response.get("description"),
            action=response.get("action", "ALLOW"),
            rules=response.get("rules"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance
