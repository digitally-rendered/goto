"""Models for Google Cloud Endpoints (Service Management) resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.endpoints import get_schema


class ManagedService(GCPResource):
    """Model for a Google Cloud Endpoints Managed Service."""

    service_name_field: str = Field(
        "", description="The name of the managed service"
    )
    producer_project_id: Optional[str] = Field(
        None, description="ID of the project that produces and owns this service"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("managed_service")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ManagedService":
        """Create a ManagedService from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ManagedService instance
        """
        service_name = response.get("serviceName", "")

        return cls(
            id=service_name,
            name=service_name,
            type="endpoints.managedService",
            project=response.get("producerProjectId", ""),
            service_name_field=service_name,
            producer_project_id=response.get("producerProjectId"),
        )


class ServiceConfig(GCPResource):
    """Model for a Google Cloud Endpoints Service Config."""

    service_name_field: str = Field(
        "", description="The name of the service this config belongs to"
    )
    title: Optional[str] = Field(
        None, description="The product title for this service"
    )
    documentation: Optional[Dict] = Field(
        None, description="Documentation configuration"
    )
    apis: Optional[List[Dict]] = Field(
        None, description="A list of API interfaces exported by this service"
    )
    quota: Optional[Dict] = Field(
        None, description="Quota configuration"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("service_config")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ServiceConfig":
        """Create a ServiceConfig from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ServiceConfig instance
        """
        config_id = response.get("id", "")
        name = response.get("name", "")

        return cls(
            id=config_id,
            name=name,
            type="endpoints.serviceConfig",
            project=response.get("producerProjectId", ""),
            service_name_field=response.get("serviceName", ""),
            title=response.get("title"),
            documentation=response.get("documentation"),
            apis=response.get("apis"),
            quota=response.get("quota"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
