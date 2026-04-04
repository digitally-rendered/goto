"""JSON Schema definitions for Google Cloud Dataplex resources."""

from typing import Dict, Any

LAKE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dataplex Lake",
    "description": "Schema for Google Cloud Dataplex Lakes",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the lake",
        },
        "description": {
            "type": "string",
            "description": "Description of the lake",
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
            "description": "The state of the lake",
            "enum": [
                "STATE_UNSPECIFIED",
                "ACTIVE",
                "CREATING",
                "DELETING",
                "ACTION_REQUIRED",
            ],
        },
        "metastore": {
            "type": "object",
            "description": "Metastore configuration",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the lake",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

ZONE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dataplex Zone",
    "description": "Schema for Google Cloud Dataplex Zones",
    "type": "object",
    "required": ["name", "type"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the zone",
        },
        "type": {
            "type": "string",
            "description": "The type of the zone",
            "enum": ["RAW", "CURATED"],
        },
        "description": {
            "type": "string",
            "description": "Description of the zone",
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
            "description": "The state of the zone",
            "enum": [
                "STATE_UNSPECIFIED",
                "ACTIVE",
                "CREATING",
                "DELETING",
                "ACTION_REQUIRED",
            ],
        },
        "discoverySpec": {
            "type": "object",
            "description": "Discovery specification",
        },
        "resourceSpec": {
            "type": "object",
            "description": "Resource specification",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the zone",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

ASSET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dataplex Asset",
    "description": "Schema for Google Cloud Dataplex Assets",
    "type": "object",
    "required": ["name", "resourceSpec"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the asset",
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
            "description": "The state of the asset",
            "enum": [
                "STATE_UNSPECIFIED",
                "ACTIVE",
                "CREATING",
                "DELETING",
                "ACTION_REQUIRED",
            ],
        },
        "resourceSpec": {
            "type": "object",
            "description": "Resource specification",
        },
        "discoverySpec": {
            "type": "object",
            "description": "Discovery specification",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the asset",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "lake") -> Dict[str, Any]:
    """Get the JSON schema for a specific Dataplex resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("lake", "zone", or "asset")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "lake": LAKE_SCHEMA,
        "zone": ZONE_SCHEMA,
        "asset": ASSET_SCHEMA,
    }
    return schemas.get(resource_type.lower(), LAKE_SCHEMA)
