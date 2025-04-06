"""Base JSON Schema definitions for GCPoto."""

from typing import Dict, Any

# Basic schema structure for all GCP resources
BASE_RESOURCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Resource",
    "description": "Base schema for all GCP resources",
    "type": "object",
    "required": ["id", "name", "type", "project"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the resource"
        },
        "name": {
            "type": "string",
            "description": "The name of the resource"
        },
        "type": {
            "type": "string",
            "description": "The GCP resource type"
        },
        "project": {
            "type": "string",
            "description": "The GCP project ID"
        },
        "labels": {
            "type": "object",
            "description": "The labels associated with the resource",
            "additionalProperties": {"type": "string"}
        },
        "created": {
            "type": "string",
            "format": "date-time",
            "description": "When the resource was created"
        },
        "updated": {
            "type": "string",
            "format": "date-time",
            "description": "When the resource was last updated"
        }
    },
    "additionalProperties": False
}


def get_schema(resource_type: str) -> Dict[str, Any]:
    """Get the JSON schema for a specific resource type.
    
    Args:
        resource_type: The GCP resource type
        
    Returns:
        The JSON schema for the resource type
    """
    # In a real implementation, this would return different schemas
    # based on the resource type
    return BASE_RESOURCE_SCHEMA
