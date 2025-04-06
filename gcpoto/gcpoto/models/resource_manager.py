"""Models for GCP Resource Manager resources (projects, folders, organizations)."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import Field, validator

from gcpoto.models.base import GCPResource


class Project(GCPResource):
    """Model for a GCP Project resource."""
    project_id: str = Field(..., description="The project ID (not the numeric ID)")
    project_number: Optional[str] = Field(None, description="The numeric project number assigned by GCP")
    display_name: str = Field(..., description="The display name of the project")
    parent: Optional[str] = Field(None, description="The resource name of the parent folder or organization")
    state: Optional[str] = Field(None, description="The project lifecycle state")
    create_time: Optional[datetime] = Field(None, description="Creation timestamp")
    delete_time: Optional[datetime] = Field(None, description="Deletion timestamp (for deleted projects)")
    etag: Optional[str] = Field(None, description="Entity tag for the project")
    
    @validator('name', pre=True)
    def validate_name(cls, v):
        """Ensure name is properly formatted."""
        if not v:
            return v
        # Make sure name has the projects/ prefix
        if not v.startswith('projects/'):
            return f'projects/{v}'
        return v

    @validator('id', pre=True)
    def validate_id(cls, v, values):
        """Set ID from project_id if not provided."""
        if not v and 'project_id' in values:
            return f'projects/{values["project_id"]}'
        return v

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'Project':
        """Create a Project instance from a GCP API response.
        
        Args:
            response: The GCP API response dictionary.
            
        Returns:
            Project: A new Project instance.
        """
        # Extract project_id from name if present
        project_id = response.get('projectId', '')
        if not project_id and 'name' in response:
            name = response['name']
            if name.startswith('projects/'):
                project_id = name.split('/')[-1]
        
        # Map response fields to model fields
        return cls(
            id=response.get('name', ''),
            name=response.get('name', ''),
            type='resourcemanager.project',
            project=project_id,  # The project is itself
            project_id=project_id,
            project_number=response.get('projectNumber'),
            display_name=response.get('displayName', ''),
            parent=response.get('parent'),
            state=response.get('state'),
            create_time=response.get('createTime'),
            delete_time=response.get('deleteTime'),
            etag=response.get('etag'),
            labels=response.get('labels'),
            tags=response.get('labels'),  # Use labels as tags
        )


class Folder(GCPResource):
    """Model for a GCP Folder resource."""
    folder_id: str = Field(..., description="The folder ID")
    display_name: str = Field(..., description="The display name of the folder")
    parent: str = Field(..., description="The resource name of the parent folder or organization")
    state: Optional[str] = Field(None, description="The folder lifecycle state")
    create_time: Optional[datetime] = Field(None, description="Creation timestamp")
    delete_time: Optional[datetime] = Field(None, description="Deletion timestamp (for deleted folders)")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    etag: Optional[str] = Field(None, description="Entity tag for the folder")
    
    @validator('name', pre=True)
    def validate_name(cls, v):
        """Ensure name is properly formatted."""
        if not v:
            return v
        # Make sure name has the folders/ prefix
        if not v.startswith('folders/'):
            return f'folders/{v}'
        return v

    @validator('id', pre=True)
    def validate_id(cls, v, values):
        """Set ID from folder_id if not provided."""
        if not v and 'folder_id' in values:
            return f'folders/{values["folder_id"]}'
        return v

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'Folder':
        """Create a Folder instance from a GCP API response.
        
        Args:
            response: The GCP API response dictionary.
            
        Returns:
            Folder: A new Folder instance.
        """
        # Extract folder_id from name if present
        folder_id = ''
        if 'name' in response:
            name = response['name']
            if name.startswith('folders/'):
                folder_id = name.split('/')[-1]
        
        # Get the project ID from the parent org or use default
        parent = response.get('parent', '')
        project_id = ''
        if parent.startswith('projects/'):
            project_id = parent.split('/')[-1]
        elif 'project' in response:  # For compatibility
            project_id = response['project']
        
        # Map response fields to model fields
        return cls(
            id=response.get('name', ''),
            name=response.get('name', ''),
            type='resourcemanager.folder',
            project=project_id,
            folder_id=folder_id,
            display_name=response.get('displayName', ''),
            parent=response.get('parent', ''),
            state=response.get('state'),
            create_time=response.get('createTime'),
            delete_time=response.get('deleteTime'),
            update_time=response.get('updateTime'),
            etag=response.get('etag'),
            labels=response.get('labels'),
            tags=response.get('labels'),  # Use labels as tags
        )
