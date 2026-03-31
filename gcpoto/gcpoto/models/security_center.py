"""Models for Google Cloud Security Command Center resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.security_center import get_schema


class Finding(GCPResource):
    """Model for a Security Command Center Finding."""

    category: str = Field("", description="The category of the finding")
    state: str = Field(
        "ACTIVE",
        description="The state of the finding (ACTIVE or INACTIVE)",
    )
    severity: str = Field("", description="The severity of the finding")
    source_properties: Optional[Dict[str, Any]] = Field(
        None, description="Source-specific properties"
    )
    security_marks: Optional[Dict[str, str]] = Field(
        None, description="Security marks applied to the finding"
    )
    event_time: Optional[datetime] = Field(
        None, description="The time the finding was first detected"
    )
    resource_name_field: Optional[str] = Field(
        None, description="The full resource name of the affected resource"
    )
    external_uri: Optional[str] = Field(
        None, description="URI to an external page about the finding"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("finding")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Finding":
        """Create a Finding from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Finding instance
        """
        security_marks_dict = None
        if response.get("securityMarks"):
            security_marks_dict = response["securityMarks"].get("marks", {})

        return cls(
            id=response.get("name", "").split("/")[-1] if response.get("name") else "",
            name=response.get("name", ""),
            type="securitycenter.finding",
            project=response.get("resourceName", "").split("/")[1]
            if response.get("resourceName", "").startswith("//")
            else response.get("parent", ""),
            category=response.get("category", ""),
            state=response.get("state", "ACTIVE"),
            severity=response.get("severity", ""),
            source_properties=response.get("sourceProperties"),
            security_marks=security_marks_dict,
            event_time=response.get("eventTime"),
            resource_name_field=response.get("resourceName"),
            external_uri=response.get("externalUri"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )


class Source(GCPResource):
    """Model for a Security Command Center Source."""

    display_name: str = Field("", description="The display name of the source")
    description: Optional[str] = Field(
        None, description="A description of the source"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("source")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Source":
        """Create a Source from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Source instance
        """
        return cls(
            id=response.get("name", "").split("/")[-1] if response.get("name") else "",
            name=response.get("name", ""),
            type="securitycenter.source",
            project=response.get("name", "").split("/")[1]
            if len(response.get("name", "").split("/")) > 1
            else "",
            display_name=response.get("displayName", ""),
            description=response.get("description"),
        )
