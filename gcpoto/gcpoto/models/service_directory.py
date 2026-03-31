"""Models for Google Cloud Service Directory resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class Namespace(GCPResource):
    """Model for a Google Cloud Service Directory namespace."""

    location: str = Field("", description="The GCP location of the namespace")
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
    def from_api_response(cls, response: Dict[str, Any]) -> "Namespace":
        """Create a Namespace from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Namespace instance
        """
        name = response.get("name", "")
        # Extract short name from full path:
        # projects/{project}/locations/{location}/namespaces/{namespace}
        short_name = name.split("/")[-1] if "/" in name else name
        parts = name.split("/")
        project = parts[1] if len(parts) >= 2 else response.get("project", "")
        location = parts[3] if len(parts) >= 4 else ""
        labels = response.get("labels")

        instance = cls(
            id=short_name,
            name=short_name,
            type="servicedirectory.namespace",
            project=project,
            location=location,
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class ServiceEntry(GCPResource):
    """Model for a Google Cloud Service Directory service."""

    namespace_name: str = Field(
        "", description="The Service Directory namespace name"
    )
    location: str = Field("", description="The GCP location of the service")
    metadata: Optional[Dict] = Field(
        None, description="Metadata for the service"
    )
    endpoints: Optional[List[Dict]] = Field(
        None, description="Endpoints associated with the service"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ServiceEntry":
        """Create a ServiceEntry from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ServiceEntry instance
        """
        name = response.get("name", "")
        # Extract short name from full path:
        # projects/{project}/locations/{location}/namespaces/{ns}/services/{svc}
        short_name = name.split("/")[-1] if "/" in name else name
        parts = name.split("/")
        project = parts[1] if len(parts) >= 2 else response.get("project", "")
        location = parts[3] if len(parts) >= 4 else ""
        namespace_name = parts[5] if len(parts) >= 6 else ""

        return cls(
            id=short_name,
            name=short_name,
            type="servicedirectory.service",
            project=project,
            namespace_name=namespace_name,
            location=location,
            metadata=response.get("metadata"),
            endpoints=response.get("endpoints"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )


class Endpoint(GCPResource):
    """Model for a Google Cloud Service Directory endpoint."""

    service_name_ref: str = Field(
        "", description="The Service Directory service name reference"
    )
    namespace_name: str = Field(
        "", description="The Service Directory namespace name"
    )
    location: str = Field("", description="The GCP location of the endpoint")
    address: Optional[str] = Field(
        None, description="The IP address of the endpoint"
    )
    port: Optional[int] = Field(
        None, description="The port number of the endpoint"
    )
    metadata: Optional[Dict] = Field(
        None, description="Metadata for the endpoint"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Endpoint":
        """Create an Endpoint from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Endpoint instance
        """
        name = response.get("name", "")
        # Extract short name from full path:
        # projects/{project}/locations/{location}/namespaces/{ns}/services/{svc}/endpoints/{ep}
        short_name = name.split("/")[-1] if "/" in name else name
        parts = name.split("/")
        project = parts[1] if len(parts) >= 2 else response.get("project", "")
        location = parts[3] if len(parts) >= 4 else ""
        namespace_name = parts[5] if len(parts) >= 6 else ""
        service_name_ref = parts[7] if len(parts) >= 8 else ""

        return cls(
            id=short_name,
            name=short_name,
            type="servicedirectory.endpoint",
            project=project,
            service_name_ref=service_name_ref,
            namespace_name=namespace_name,
            location=location,
            address=response.get("address"),
            port=response.get("port"),
            metadata=response.get("metadata"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
