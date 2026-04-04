"""JSON Schema definitions for Cloud Source Repositories resources."""

from typing import Dict, Any


REPO_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Source Repository",
    "description": "Schema for Cloud Source Repositories",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the repository",
        },
        "size": {
            "type": "integer",
            "description": "The disk usage of the repo in bytes",
        },
        "url": {
            "type": "string",
            "description": "URL to clone the repository",
        },
        "mirrorConfig": {
            "type": "object",
            "description": "Mirror configuration for the repository",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the main repository",
                },
                "webhookId": {
                    "type": "string",
                    "description": "ID of the webhook listening to updates",
                },
                "deployKeyId": {
                    "type": "string",
                    "description": "ID of the SSH deploy key",
                },
            },
        },
        "pubsubConfigs": {
            "type": "object",
            "description": "Pub/Sub notification configurations",
            "additionalProperties": True,
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "repo") -> Dict[str, Any]:
    """Get the JSON schema for a Cloud Source Repositories resource type.

    Args:
        resource_type: The type of resource to get the schema for

    Returns:
        The JSON schema for the specified resource type
    """
    return REPO_SCHEMA
