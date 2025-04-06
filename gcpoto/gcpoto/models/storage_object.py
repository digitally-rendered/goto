"""Models for Google Cloud Storage Objects."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.storage_object import get_schema


class ObjectAclEntry(BaseModel):
    """Access Control List entry for a Cloud Storage object."""
    entity: str = Field(..., description="The entity holding the permission")
    role: str = Field(..., description="The access permission for the entity")


class StorageObject(GCPResource):
    """Model for a Google Cloud Storage object."""
    bucket: str = Field(..., description="The bucket containing the object")
    content_type: Optional[str] = Field(None, description="The content type of the object data")
    size: Optional[int] = Field(None, description="Size of the object in bytes")
    etag: Optional[str] = Field(None, description="HTTP 1.1 Entity tag for the object")
    generation: Optional[str] = Field(None, description="The content generation of this object")
    md5_hash: Optional[str] = Field(None, description="MD5 hash of the object data")
    crc32c: Optional[str] = Field(None, description="CRC32c checksum of the object data")
    storage_class: Optional[str] = Field(None, description="Storage class of the object")
    content_encoding: Optional[str] = Field(None, description="Content encoding of the object data")
    content_disposition: Optional[str] = Field(None, description="Content disposition of the object data")
    cache_control: Optional[str] = Field(None, description="Cache control for the object data")
    metadata: Optional[Dict[str, str]] = Field(None, description="User-provided metadata for the object")
    acl: Optional[List[ObjectAclEntry]] = Field(None, description="Access control list for the object")
    _tags: Optional[Dict[str, str]] = None
    
    def get_tag(self, key: str, default: Any = None) -> Any:
        """Get a tag value by key, falling back to metadata.
        
        Args:
            key: The tag key to look up
            default: Default value to return if key not found
            
        Returns:
            The tag value or default if not found
        """
        # First check explicit tags, then fall back to metadata
        if self._tags and key in self._tags:
            return self._tags[key]
        elif self.metadata and key in self.metadata:
            return self.metadata[key]
        else:
            return default
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {"schema": get_schema()}
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'StorageObject':
        """Create a StorageObject from an API response.
        
        Args:
            response: The API response dictionary
            
        Returns:
            A new StorageObject instance
        """
        acl_entries = None
        if response.get("acl"):
            acl_entries = [
                ObjectAclEntry(entity=entry.get("entity", ""), role=entry.get("role", ""))
                for entry in response.get("acl", [])
            ]
        
        # The API uses camelCase, our model uses snake_case
        # Convert size to int if present
        size = response.get("size")
        if size is not None:
            try:
                size = int(size)
            except (ValueError, TypeError):
                # Keep as string if conversion fails
                pass
                
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="storage.object",
            project=response.get("projectId", ""),
            bucket=response.get("bucket", ""),
            content_type=response.get("contentType"),
            size=size,
            etag=response.get("etag"),
            generation=response.get("generation"),
            md5_hash=response.get("md5Hash"),
            crc32c=response.get("crc32c"),
            created=response.get("timeCreated"),
            updated=response.get("updated"),
            storage_class=response.get("storageClass"),
            content_encoding=response.get("contentEncoding"),
            content_disposition=response.get("contentDisposition"),
            cache_control=response.get("cacheControl"),
            metadata=response.get("metadata"),
            acl=acl_entries
        )
        
        # Initialize _tags from metadata if present
        if response.get("metadata"):
            instance._tags = response["metadata"]
            
        return instance
