"""Models for Google Cloud Firestore resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.firestore import get_schema


class FirestoreDocument(GCPResource):
    """Model for a Google Cloud Firestore Document."""

    collection: str = Field(
        "", description="The collection containing this document"
    )
    document_id: str = Field(
        "", description="The document ID within the collection"
    )
    fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="The document fields and their values",
    )
    create_time: Optional[datetime] = Field(
        None, description="When the document was created"
    )
    update_time: Optional[datetime] = Field(
        None, description="When the document was last updated"
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

        json_schema_extra = {"schema": get_schema("document")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "FirestoreDocument":
        """Create a FirestoreDocument from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new FirestoreDocument instance
        """
        full_name = response.get("name", "")
        parts = full_name.split("/") if full_name else []

        # name format: projects/{project}/databases/{db}/documents/{collection}/{doc_id}
        document_id = parts[-1] if len(parts) >= 1 else ""
        collection = parts[-2] if len(parts) >= 2 else ""

        if not project_id and len(parts) >= 2:
            project_id = parts[1]

        instance = cls(
            id=full_name,
            name=full_name,
            type="firestore.document",
            project=project_id,
            collection=collection,
            document_id=document_id,
            fields=response.get("fields", {}),
            create_time=response.get("createTime"),
            update_time=response.get("updateTime"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        return instance


class FirestoreCollection(GCPResource):
    """Model for a Google Cloud Firestore Collection."""

    collection_id: str = Field(
        "", description="The collection ID"
    )
    document_count: Optional[int] = Field(
        None, description="The number of documents in the collection"
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

        json_schema_extra = {"schema": get_schema("collection")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "FirestoreCollection":
        """Create a FirestoreCollection from an API response.

        Args:
            response: The API response dictionary (typically just a collection ID string)
            project_id: The GCP project ID

        Returns:
            A new FirestoreCollection instance
        """
        # The listCollectionIds API returns collection IDs as strings
        if isinstance(response, str):
            collection_id = response
            return cls(
                id=collection_id,
                name=collection_id,
                type="firestore.collection",
                project=project_id,
                collection_id=collection_id,
            )

        collection_id = response.get("collectionId", "")
        return cls(
            id=collection_id,
            name=collection_id,
            type="firestore.collection",
            project=project_id,
            collection_id=collection_id,
            document_count=response.get("documentCount"),
        )


class FirestoreIndex(GCPResource):
    """Model for a Google Cloud Firestore Index."""

    collection_group: str = Field(
        "", description="The collection group this index applies to"
    )
    query_scope: str = Field(
        "COLLECTION",
        description="The query scope: COLLECTION or COLLECTION_GROUP",
    )
    fields_config: List[Dict] = Field(
        default_factory=list,
        description="The index field configurations",
    )
    state: str = Field(
        "",
        description="The index state: CREATING, READY, NEEDS_REPAIR",
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

        json_schema_extra = {"schema": get_schema("index")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "FirestoreIndex":
        """Create a FirestoreIndex from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new FirestoreIndex instance
        """
        full_name = response.get("name", "")
        parts = full_name.split("/") if full_name else []

        if not project_id and len(parts) >= 2:
            project_id = parts[1]

        # Extract collection group from the name path
        # format: projects/{project}/databases/{db}/collectionGroups/{group}/indexes/{id}
        collection_group = ""
        if len(parts) >= 6:
            collection_group = parts[5]

        instance = cls(
            id=full_name,
            name=full_name,
            type="firestore.index",
            project=project_id,
            collection_group=collection_group,
            query_scope=response.get("queryScope", "COLLECTION"),
            fields_config=response.get("fields", []),
            state=response.get("state", ""),
        )

        return instance
