"""Models for GCP Resource Manager resources (projects, folders, organizations)."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import Field, field_validator, model_validator

from gcpoto.models.base import GCPResource


class Project(GCPResource):
    """Model for a GCP Project resource."""

    project_id: str = Field(..., description="The project ID (not the numeric ID)")
    project_number: Optional[str] = Field(
        None, description="The numeric project number assigned by GCP"
    )
    display_name: str = Field(..., description="The display name of the project")
    parent: Optional[str] = Field(
        None, description="The resource name of the parent folder or organization"
    )
    state: Optional[str] = Field(None, description="The project lifecycle state")
    create_time: Optional[datetime] = Field(None, description="Creation timestamp")
    delete_time: Optional[datetime] = Field(
        None, description="Deletion timestamp (for deleted projects)"
    )
    etag: Optional[str] = Field(None, description="Entity tag for the project")

    # Combined model validator to handle all required fields
    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v):
        """Ensure name is properly formatted."""
        if not v:
            return v
        # Make sure name has the projects/ prefix
        if not v.startswith("projects/"):
            return f"projects/{v}"
        return v

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v, info):
        """Set ID from project_id if not provided."""
        if not v and "project_id" in info.data:
            return f'projects/{info.data["project_id"]}'
        return v

    # Use model_validator to ensure all required fields are set properly
    @model_validator(mode="before")
    @classmethod
    def set_required_fields(cls, data: Any) -> Any:
        """Set required fields from available data before validation."""
        if isinstance(data, dict):
            # Extract project_id from name if possible
            name = data.get("name", "")
            project_id = data.get("project_id", "")

            if name and name.startswith("projects/") and not project_id:
                project_id = name.split("/")[-1]
                data["project_id"] = project_id

            # Normalize project_id if it contains projects/ prefix
            if project_id and project_id.startswith("projects/"):
                project_id = project_id[9:]  # Remove 'projects/' prefix
                data["project_id"] = project_id

            # Set name from project_id if not provided
            if project_id and not name:
                data["name"] = f"projects/{project_id}"

            # Set id from project_id if not provided
            if project_id and not data.get("id"):
                data["id"] = f"projects/{project_id}"

            # Ensure required base fields are present
            if "type" not in data:
                data["type"] = "resourcemanager.project"

            # Set project field (used by GCPResource base class)
            if "project" not in data and project_id:
                data["project"] = project_id

            # Set display_name from project_id if not provided
            if project_id and not data.get("display_name"):
                data["display_name"] = f"Project {project_id}"
        return data

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Project":
        """Create a Project instance from a GCP API response.

        Args:
            response: The GCP API response dictionary.

        Returns:
            Project: A new Project instance.
        """
        # Extract project_id from name if present
        project_id = response.get("projectId", "")
        if not project_id and "name" in response:
            name = response["name"]
            if name.startswith("projects/"):
                project_id = name.split("/")[-1]

        # Map response fields to model fields
        return cls(
            id=response.get("name", ""),
            name=response.get("name", ""),
            type="resourcemanager.project",
            project=project_id,  # The project is itself
            project_id=project_id,
            project_number=response.get("projectNumber"),
            display_name=response.get("displayName", ""),
            parent=response.get("parent"),
            state=response.get("state"),
            create_time=response.get("createTime"),
            delete_time=response.get("deleteTime"),
            etag=response.get("etag"),
            labels=response.get("labels"),
            tags=response.get("labels"),  # Use labels as tags
        )


class Folder(GCPResource):
    """Model for a GCP Folder resource."""

    folder_id: str = Field(..., description="The folder ID")
    display_name: str = Field(..., description="The display name of the folder")
    parent: str = Field(
        ..., description="The resource name of the parent folder or organization"
    )
    state: Optional[str] = Field(None, description="The folder lifecycle state")
    create_time: Optional[datetime] = Field(None, description="Creation timestamp")
    delete_time: Optional[datetime] = Field(
        None, description="Deletion timestamp (for deleted folders)"
    )
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    etag: Optional[str] = Field(None, description="Entity tag for the folder")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v):
        """Ensure name is properly formatted."""
        if not v:
            return v
        # Make sure name has the folders/ prefix
        if not v.startswith("folders/"):
            return f"folders/{v}"
        return v

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v, info):
        """Set ID from folder_id if not provided."""
        if not v and "folder_id" in info.data:
            return f'folders/{info.data["folder_id"]}'
        return v

    # Use model_validator to ensure all required fields are set properly
    @model_validator(mode="before")
    @classmethod
    def set_required_fields(cls, data: Any) -> Any:
        """Set required fields from available data before validation."""
        if isinstance(data, dict):
            # Extract folder_id from name if possible
            name = data.get("name", "")
            folder_id = data.get("folder_id", "")

            if name and name.startswith("folders/") and not folder_id:
                folder_id = name.split("/")[-1]
                data["folder_id"] = folder_id

            # Normalize folder_id if it contains folders/ prefix
            if folder_id and folder_id.startswith("folders/"):
                folder_id = folder_id[8:]  # Remove 'folders/' prefix
                data["folder_id"] = folder_id

            # Set name from folder_id if not provided
            if folder_id and not name:
                data["name"] = f"folders/{folder_id}"

            # Set id from folder_id if not provided
            if folder_id and not data.get("id"):
                data["id"] = f"folders/{folder_id}"

            # Ensure required base fields are present
            if "type" not in data:
                data["type"] = "resourcemanager.folder"

            # Set parent if not provided (default to organization)
            if "parent" not in data:
                data["parent"] = "organizations/000000000000"

            # Ensure we have a project field for GCPResource base class
            if "project" not in data:
                parent = data.get("parent", "")
                if parent and parent.startswith("projects/"):
                    data["project"] = parent.split("/")[-1]
                else:
                    data["project"] = "unknown"

            # Set display_name from folder_id if not provided
            if folder_id and not data.get("display_name"):
                data["display_name"] = f"Folder {folder_id}"
        return data

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Folder":
        """Create a Folder instance from a GCP API response.

        Args:
            response: The GCP API response dictionary.

        Returns:
            Folder: A new Folder instance.
        """
        # Extract folder_id from name if present
        folder_id = ""
        if "name" in response:
            name = response["name"]
            if name.startswith("folders/"):
                folder_id = name.split("/")[-1]

        # Get the project ID from the parent org or use default
        parent = response.get("parent", "")
        project_id = ""
        if parent.startswith("projects/"):
            project_id = parent.split("/")[-1]
        elif "project" in response:  # For compatibility
            project_id = response["project"]

        # Map response fields to model fields
        return cls(
            id=response.get("name", ""),
            name=response.get("name", ""),
            type="resourcemanager.folder",
            project=project_id,
            folder_id=folder_id,
            display_name=response.get("displayName", ""),
            parent=response.get("parent", ""),
            state=response.get("state"),
            create_time=response.get("createTime"),
            delete_time=response.get("deleteTime"),
            update_time=response.get("updateTime"),
            etag=response.get("etag"),
            labels=response.get("labels"),
            tags=response.get("labels"),  # Use labels as tags
        )
