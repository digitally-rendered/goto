"""Models for Google Cloud Data Catalog resources."""

from typing import Dict, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class EntryGroup(GCPResource):
    """Model for a Google Cloud Data Catalog Entry Group."""

    location: str = Field("", description="The location of the entry group")
    display_name: Optional[str] = Field(
        None, description="Display name of the entry group"
    )
    description: Optional[str] = Field(
        None, description="Description of the entry group"
    )

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "EntryGroup":
        """Create an EntryGroup from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new EntryGroup instance
        """
        name = response.get("name", "")
        # name format: projects/{project}/locations/{location}/entryGroups/{id}
        parts = name.split("/")
        entry_group_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        return cls(
            id=entry_group_id,
            name=name,
            type="datacatalog.entryGroup",
            project=project_id,
            location=location,
            display_name=response.get("displayName"),
            description=response.get("description"),
            created=response.get("dataCatalogTimestamps", {}).get(
                "createTime"
            ),
            updated=response.get("dataCatalogTimestamps", {}).get(
                "updateTime"
            ),
        )


class Entry(GCPResource):
    """Model for a Google Cloud Data Catalog Entry."""

    entry_group: str = Field(
        "", description="The entry group this entry belongs to"
    )
    location: str = Field("", description="The location of the entry")
    entry_type: str = Field("", description="The type of the entry")
    linked_resource: Optional[str] = Field(
        None, description="The resource this entry represents"
    )
    display_name: Optional[str] = Field(
        None, description="Display name of the entry"
    )
    description: Optional[str] = Field(
        None, description="Description of the entry"
    )
    schema: Optional[Dict[str, Any]] = Field(
        None, description="Schema of the entry"
    )
    source_system_timestamps: Optional[Dict[str, Any]] = Field(
        None, description="Timestamps from the source system"
    )

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Entry":
        """Create an Entry from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new Entry instance
        """
        name = response.get("name", "")
        # name format: projects/{p}/locations/{l}/entryGroups/{eg}/entries/{e}
        parts = name.split("/")
        entry_id = parts[-1] if len(parts) >= 8 else ""
        entry_group = parts[5] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        return cls(
            id=entry_id,
            name=name,
            type="datacatalog.entry",
            project=project_id,
            entry_group=entry_group,
            location=location,
            entry_type=response.get("type", response.get("userSpecifiedType", "")),
            linked_resource=response.get("linkedResource"),
            display_name=response.get("displayName"),
            description=response.get("description"),
            schema=response.get("schema"),
            source_system_timestamps=response.get("sourceSystemTimestamps"),
            created=response.get("sourceSystemTimestamps", {}).get(
                "createTime"
            ),
            updated=response.get("sourceSystemTimestamps", {}).get(
                "updateTime"
            ),
        )


class Tag(GCPResource):
    """Model for a Google Cloud Data Catalog Tag."""

    entry_name: str = Field(
        "", description="The full name of the entry this tag belongs to"
    )
    template: str = Field("", description="The tag template name")
    fields: Dict[str, Any] = Field(
        default_factory=dict, description="The tag fields"
    )

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Tag":
        """Create a Tag from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new Tag instance
        """
        name = response.get("name", "")
        # name format: projects/{p}/locations/{l}/entryGroups/{eg}/entries/{e}/tags/{t}
        parts = name.split("/")
        tag_id = parts[-1] if len(parts) >= 10 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        # Derive entry name from tag name
        entry_name = ""
        if len(parts) >= 8:
            entry_name = "/".join(parts[:8])

        return cls(
            id=tag_id,
            name=name,
            type="datacatalog.tag",
            project=project_id,
            entry_name=entry_name,
            template=response.get("template", ""),
            fields=response.get("fields", {}),
            created=response.get("dataCatalogTimestamps", {}).get(
                "createTime"
            ),
            updated=response.get("dataCatalogTimestamps", {}).get(
                "updateTime"
            ),
        )
