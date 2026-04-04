"""Models for Google Cloud API Gateway resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.api_gateway import get_schema


class APIGateway(GCPResource):
    """Model for a Google Cloud API Gateway."""

    location: str = Field("", description="The location of the gateway")
    display_name: Optional[str] = Field(
        None, description="Display name for the gateway"
    )
    state: str = Field("", description="The current state of the gateway")
    default_hostname: Optional[str] = Field(
        None, description="The default hostname of the gateway"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("gateway")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "APIGateway":
        """Create an APIGateway from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new APIGateway instance
        """
        name = response.get("name", "")
        # Extract the gateway ID from the full resource name
        gateway_id = name.rsplit("/", 1)[-1] if "/" in name else name

        instance = cls(
            id=gateway_id,
            name=name,
            type="apigateway.gateway",
            project=response.get("project", ""),
            location=response.get("location", ""),
            display_name=response.get("displayName"),
            state=response.get("state", ""),
            default_hostname=response.get("defaultHostname"),
            labels=response.get("labels"),
            created=response.get("createTime"),
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


class APIConfig(GCPResource):
    """Model for a Google Cloud API Gateway API Config."""

    gateway_name: str = Field(
        "", description="The gateway this config is associated with"
    )
    location: str = Field("", description="The location of the API config")
    display_name: Optional[str] = Field(
        None, description="Display name for the API config"
    )
    state: str = Field("", description="The current state of the API config")
    service_config_id: Optional[str] = Field(
        None, description="The service config ID from Service Management"
    )
    grpc_services: Optional[List[Dict]] = Field(
        None, description="gRPC service definitions"
    )
    openapi_documents: Optional[List[Dict]] = Field(
        None, description="OpenAPI specification documents"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("api_config")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "APIConfig":
        """Create an APIConfig from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new APIConfig instance
        """
        name = response.get("name", "")
        # Extract the config ID from the full resource name
        config_id = name.rsplit("/", 1)[-1] if "/" in name else name

        instance = cls(
            id=config_id,
            name=name,
            type="apigateway.apiConfig",
            project=response.get("project", ""),
            gateway_name=response.get("gatewayServiceAccount", ""),
            location=response.get("location", ""),
            display_name=response.get("displayName"),
            state=response.get("state", ""),
            service_config_id=response.get("serviceConfigId"),
            grpc_services=response.get("grpcServices"),
            openapi_documents=response.get("openapiDocuments"),
            labels=response.get("labels"),
            created=response.get("createTime"),
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
