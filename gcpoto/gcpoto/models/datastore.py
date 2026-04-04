"""Models for Google Cloud Datastore resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.datastore import get_schema


class Entity(GCPResource):
    """Model for a Google Cloud Datastore Entity."""

    kind: str = Field("", description="The entity kind")
    key: Dict[str, Any] = Field(
        default_factory=dict, description="The entity key"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="The entity properties"
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

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("entity")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Entity":
        """Create an Entity from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new Entity instance
        """
        entity_key = response.get("key", {})
        path = entity_key.get("path", [])
        kind = path[-1].get("kind", "") if path else ""
        entity_id = path[-1].get("id", path[-1].get("name", "")) if path else ""

        if not project_id:
            partition = entity_key.get("partitionId", {})
            project_id = partition.get("projectId", "")

        instance = cls(
            id=str(entity_id),
            name=str(entity_id),
            type="datastore.entity",
            project=project_id,
            kind=kind,
            key=entity_key,
            properties=response.get("properties", {}),
        )

        return instance


class EntityResult(GCPResource):
    """Model for a Google Cloud Datastore EntityResult."""

    entity: Dict[str, Any] = Field(
        default_factory=dict, description="The result entity"
    )
    cursor: Optional[str] = Field(
        None, description="A cursor that points to the position after the result entity"
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

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("entity_result")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "EntityResult":
        """Create an EntityResult from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new EntityResult instance
        """
        entity = response.get("entity", {})
        entity_key = entity.get("key", {})
        path = entity_key.get("path", [])
        entity_id = path[-1].get("id", path[-1].get("name", "")) if path else ""

        if not project_id:
            partition = entity_key.get("partitionId", {})
            project_id = partition.get("projectId", "")

        instance = cls(
            id=str(entity_id),
            name=str(entity_id),
            type="datastore.entityResult",
            project=project_id,
            entity=entity,
            cursor=response.get("cursor"),
        )

        return instance
