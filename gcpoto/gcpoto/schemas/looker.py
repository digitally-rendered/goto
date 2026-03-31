"""JSON Schema definitions for Google Cloud Looker resources."""

from typing import Dict, Any

LOOKER_INSTANCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Looker Instance",
    "description": "Schema for Google Cloud Looker Instances",
    "type": "object",
    "required": ["name", "platformEdition"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the instance",
        },
        "platformEdition": {
            "type": "string",
            "description": "The platform edition of the instance",
            "enum": ["STANDARD", "ADVANCED", "ELITE"],
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
        "state": {
            "type": "string",
            "description": "The state of the instance",
            "enum": [
                "STATE_UNSPECIFIED",
                "ACTIVE",
                "CREATING",
                "FAILED",
                "SUSPENDED",
                "DELETING",
                "UPDATING",
                "EXPORTING",
                "IMPORTING",
            ],
        },
        "lookerUri": {
            "type": "string",
            "description": "The Looker instance URI",
        },
        "adminSettings": {
            "type": "object",
            "description": "Admin settings for the instance",
        },
        "maintenanceWindow": {
            "type": "object",
            "description": "Maintenance window configuration",
        },
        "denyMaintenancePeriod": {
            "type": "object",
            "description": "Deny maintenance period configuration",
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
    """Get the JSON schema for a specific Looker resource type.

    Args:
        resource_type: The type of resource to get the schema for

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "instance": LOOKER_INSTANCE_SCHEMA,
    }
    return schemas.get(resource_type.lower(), LOOKER_INSTANCE_SCHEMA)
