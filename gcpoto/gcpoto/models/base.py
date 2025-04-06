"""Base models for GCP resources."""

from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.schemas.base import get_schema


class GCPResource(BaseModel):
    """Base model for all GCP resources."""
    id: str = Field(..., description="The unique identifier for the resource")
    name: str = Field(..., description="The name of the resource")
    type: str = Field(..., description="The GCP resource type")
    project: str = Field(..., description="The GCP project ID")
    labels: Optional[Dict[str, str]] = Field(None, description="Labels associated with the resource")
    tags: Optional[Dict[str, str]] = Field(None, description="Tags associated with the resource")
    created: Optional[datetime] = Field(None, description="When the resource was created")
    updated: Optional[datetime] = Field(None, description="When the resource was last updated")
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {"schema": get_schema("base")}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary.
        
        Returns:
            A dictionary representation of the model.
        """
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'GCPResource':
        """Create a resource from an API response.
        
        Args:
            response: The API response dictionary
            
        Returns:
            A new GCPResource instance
        """
        # Convert API response to model attributes
        # This is a basic implementation - would need customization per resource type
        return cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type=response.get("kind", "").split("#")[-1],
            project=response.get("projectId", ""),
            labels=response.get("labels", {}),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime")
        )
