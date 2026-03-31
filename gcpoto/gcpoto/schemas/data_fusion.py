"""JSON Schema definitions for Google Cloud Data Fusion resources."""

from typing import Dict, Any

DATA_FUSION_INSTANCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Data Fusion Instance",
    "description": "Schema for Google Cloud Data Fusion Instances",
    "type": "object",
    "required": ["name", "type"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the instance",
        },
        "type": {
            "type": "string",
            "description": "The type of the instance",
            "enum": ["BASIC", "ENTERPRISE", "DEVELOPER"],
        },
        "description": {
            "type": "string",
            "description": "Description of the instance",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation timestamp",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update timestamp",
        },
        "enableStackdriverLogging": {
            "type": "boolean",
            "description": "Whether Stackdriver logging is enabled",
        },
        "enableStackdriverMonitoring": {
            "type": "boolean",
            "description": "Whether Stackdriver monitoring is enabled",
        },
        "privateInstance": {
            "type": "boolean",
            "description": "Whether the instance is private",
        },
        "networkConfig": {
            "type": "object",
            "description": "Network configuration for the instance",
        },
        "state": {
            "type": "string",
            "description": "The state of the instance",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "ACTIVE",
                "FAILED",
                "DELETING",
                "UPGRADING",
                "RESTARTING",
                "UPDATING",
                "AUTO_UPDATING",
                "AUTO_UPGRADING",
                "DISABLED",
            ],
        },
        "serviceEndpoint": {
            "type": "string",
            "description": "The service endpoint URL",
        },
        "apiEndpoint": {
            "type": "string",
            "description": "The API endpoint URL",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the instance",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "instance") -> Dict[str, Any]:
    """Get the JSON schema for a specific Data Fusion resource type.

    Args:
        resource_type: The type of resource to get the schema for

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "instance": DATA_FUSION_INSTANCE_SCHEMA,
    }
    return schemas.get(resource_type.lower(), DATA_FUSION_INSTANCE_SCHEMA)
