"""JSON Schema definitions for Google Cloud API Keys resources."""

from typing import Dict, Any


# JSON Schema for API Key
API_KEY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP API Key",
    "description": "Schema for Google Cloud API Key",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the API key",
        },
        "uid": {
            "type": "string",
            "description": "Unique identifier for the API key",
        },
        "displayName": {
            "type": "string",
            "description": "Human-readable display name of the key",
        },
        "keyString": {
            "type": "string",
            "description": "The API key string",
        },
        "restrictions": {
            "type": "object",
            "description": "Key restrictions",
            "properties": {
                "browserKeyRestrictions": {
                    "type": "object",
                    "properties": {
                        "allowedReferrers": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                "serverKeyRestrictions": {
                    "type": "object",
                    "properties": {
                        "allowedIps": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                "apiTargets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "service": {"type": "string"},
                            "methods": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
        "annotations": {
            "type": "object",
            "description": "Annotations associated with the key",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the key",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the key",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "api_key") -> Dict[str, Any]:
    """Get the JSON schema for an API Keys resource type.

    Args:
        resource_type: The type of resource to get the schema for
            (``"api_key"``).

    Returns:
        The JSON schema for the specified resource type.
    """
    return API_KEY_SCHEMA
