"""Models for Google Cloud Apigee resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.apigee import get_schema


class ApigeeOrganization(GCPResource):
    """Model for an Apigee Organization."""

    analytics_region: Optional[str] = Field(
        None, description="The analytics region for the organization"
    )
    authorized_network: Optional[str] = Field(
        None, description="The authorized network for the organization"
    )
    runtime_type: Optional[str] = Field(
        None, description="The runtime type (CLOUD or HYBRID)"
    )
    state: Optional[str] = Field(
        None, description="The current state of the organization"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("organization")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "ApigeeOrganization":
        """Create an ApigeeOrganization from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ApigeeOrganization instance
        """
        name = response.get("name", "")
        org_id = name.rsplit("/", 1)[-1] if "/" in name else name

        instance = cls(
            id=org_id,
            name=name,
            type="apigee.organization",
            project=response.get("projectId", ""),
            analytics_region=response.get("analyticsRegion"),
            authorized_network=response.get("authorizedNetwork"),
            runtime_type=response.get("runtimeType"),
            state=response.get("state"),
            labels=response.get("labels"),
            created=response.get("createdAt"),
            updated=response.get("lastModifiedAt"),
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


class ApigeeEnvironment(GCPResource):
    """Model for an Apigee Environment."""

    organization: str = Field(
        "", description="The organization this environment belongs to"
    )
    display_name: Optional[str] = Field(
        None, description="Display name for the environment"
    )
    description: Optional[str] = Field(
        None, description="Description of the environment"
    )
    state: Optional[str] = Field(
        None, description="The current state of the environment"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("environment")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "ApigeeEnvironment":
        """Create an ApigeeEnvironment from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ApigeeEnvironment instance
        """
        name = response.get("name", "")
        env_id = name.rsplit("/", 1)[-1] if "/" in name else name

        instance = cls(
            id=env_id,
            name=name,
            type="apigee.environment",
            project=response.get("projectId", ""),
            organization=response.get("organization", ""),
            display_name=response.get("displayName"),
            description=response.get("description"),
            state=response.get("state"),
            labels=response.get("labels"),
            created=response.get("createdAt"),
            updated=response.get("lastModifiedAt"),
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


class ApigeeAPIProxy(GCPResource):
    """Model for an Apigee API Proxy."""

    organization: str = Field(
        "", description="The organization this proxy belongs to"
    )
    revision: Optional[List[str]] = Field(
        None, description="List of revisions for this proxy"
    )
    latest_revision_id: Optional[str] = Field(
        None, description="The latest revision ID"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("api_proxy")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "ApigeeAPIProxy":
        """Create an ApigeeAPIProxy from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ApigeeAPIProxy instance
        """
        name = response.get("name", "")
        proxy_id = name.rsplit("/", 1)[-1] if "/" in name else name

        instance = cls(
            id=proxy_id,
            name=name,
            type="apigee.apiProxy",
            project=response.get("projectId", ""),
            organization=response.get("organization", ""),
            revision=response.get("revision"),
            latest_revision_id=response.get("latestRevisionId"),
            labels=response.get("labels"),
            created=response.get("createdAt"),
            updated=response.get("lastModifiedAt"),
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
